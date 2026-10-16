"""
OCR pipeline for receipt images: OpenCV preprocessing, Tesseract, then the
text parser in receipt_parser.py and the name normalizer in ocr_advanced.py.

Speed: the image is rescaled so its letters are a size Tesseract reads well
(close-up phone photos are shrunk, small crops are enlarged), and OCR runs in
passes. The first
pass is one Tesseract call on a contrast-enhanced image. If its text already
looks like a receipt (several "name ... price" lines and a total), that result
is used. Otherwise the remaining preprocessing and page-layout combinations run
in parallel and the best-scoring text wins. scripts/ocr_accuracy.py --mode ocr
reports the resulting time per receipt.
"""
import logging
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Dict, List, Optional, Tuple

import cv2
import numpy as np
import pytesseract

import receipt_parser
from ocr_advanced import (
    analyze_receipt_quality,
    detect_receipt_type,
    extract_store_info,
    get_category_suggestion,
    merge_duplicate_items,
    validate_and_fix_items,
)

logger = logging.getLogger(__name__)

# Tesseract is fastest and most accurate when capital letters are roughly
# 20 to 40 pixels tall. Huge glyphs (a close-up phone photo) make it very slow
# and tiny ones make it miss characters, so the image is rescaled until the
# typical glyph height falls in this range.
TARGET_GLYPH_HEIGHT = 28
GLYPH_HEIGHT_RANGE = (22, 44)
MAX_SIDE = 4000          # never hand Tesseract more than this many pixels on a side
TESSERACT_TIMEOUT = 20   # seconds per Tesseract call; a stuck pass is abandoned


def estimate_glyph_height(gray: np.ndarray) -> Optional[float]:
    """Median height (pixels) of character-sized blobs, or None if there is no text-like content."""
    scale = 1.0
    if max(gray.shape) > 1600:  # estimate on a smaller copy for speed
        scale = 1600 / max(gray.shape)
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    _, _, stats, _ = cv2.connectedComponentsWithStats(bw, connectivity=8)
    h, w = stats[1:, cv2.CC_STAT_HEIGHT], stats[1:, cv2.CC_STAT_WIDTH]
    keep = (h >= 4) & (h <= gray.shape[0] / 8) & (w <= h * 2.5) & (w >= 2)
    if keep.sum() < 10:
        return None
    return float(np.median(h[keep])) / scale


def load_grayscale(image_path: str) -> np.ndarray:
    """Read an image as grayscale, rescaled so text has a Tesseract-friendly size, and deskewed."""
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"Failed to read image from {image_path}")
    factor = 1.0
    glyph = estimate_glyph_height(img)
    if glyph and not (GLYPH_HEIGHT_RANGE[0] <= glyph <= GLYPH_HEIGHT_RANGE[1]):
        factor = TARGET_GLYPH_HEIGHT / glyph
    factor = min(factor, MAX_SIDE / max(img.shape))
    if abs(factor - 1.0) > 0.05:
        interpolation = cv2.INTER_AREA if factor < 1 else cv2.INTER_CUBIC
        img = cv2.resize(img, None, fx=factor, fy=factor, interpolation=interpolation)
        logger.debug(f"Rescaled by {factor:.2f} (glyph height {glyph})")
    return deskew_image(img)


def deskew_image(image: np.ndarray) -> np.ndarray:
    """Rotate the image so text lines are horizontal (no-op when already straight)."""
    try:
        edges = cv2.Canny(image, 50, 150, apertureSize=3)
        lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)
        if lines is None:
            return image
        angles = [np.degrees(theta) - 90 for _, theta in lines[:, 0] if abs(np.degrees(theta) - 90) < 45]
        if not angles:
            return image
        median_angle = float(np.median(angles))
        if abs(median_angle) <= 0.5:
            return image
        h, w = image.shape
        matrix = cv2.getRotationMatrix2D((w // 2, h // 2), median_angle, 1.0)
        logger.debug(f"Image deskewed by {median_angle:.2f} degrees")
        return cv2.warpAffine(image, matrix, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    except cv2.error as e:  # pragma: no cover - defensive
        logger.warning(f"Deskewing failed: {e}, returning original")
        return image


def enhance_contrast(image: np.ndarray) -> np.ndarray:
    """CLAHE contrast enhancement (handles uneven lighting without hard thresholds)."""
    return cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(image)


def otsu_threshold(image: np.ndarray) -> np.ndarray:
    blurred = cv2.medianBlur(image, 3)
    return cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]


def adaptive_threshold(image: np.ndarray) -> np.ndarray:
    return cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 10)


def sharpen_image(image: np.ndarray) -> np.ndarray:
    kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    return cv2.filter2D(image, -1, kernel)


VARIANTS: Dict[str, Callable[[np.ndarray], np.ndarray]] = {
    "contrast": enhance_contrast,
    "otsu": otsu_threshold,
    "adaptive": adaptive_threshold,
    "sharpen": sharpen_image,
}

# (variant, Tesseract config). The first entry is the fast path.
# Order chosen with scripts/ocr_accuracy.py: Otsu + "uniform block" (psm 6)
# read the most items on its own; the others rescue images it struggles with.
OCR_PASSES: List[Tuple[str, str]] = [
    ("otsu", "--oem 1 --psm 6"),
    ("contrast", "--oem 1 --psm 4"),
    ("sharpen", "--oem 1 --psm 6"),
    ("otsu", "--oem 1 --psm 4"),
]


def preprocess_image(image_path: str) -> List[np.ndarray]:
    """All preprocessed versions of the receipt, in OCR_PASSES variant order (kept for callers and tests)."""
    gray = load_grayscale(image_path)
    return [fn(gray) for fn in VARIANTS.values()]


# ---------------------------------------------------------------- Tesseract

def is_tesseract_available() -> bool:
    """Return True if the Tesseract binary can be found and executed."""
    try:
        pytesseract.get_tesseract_version()
        return True
    except (pytesseract.TesseractNotFoundError, OSError):
        return False


_installed_languages: Optional[set] = None


def resolve_languages(languages: str) -> str:
    """
    Keep only the requested Tesseract languages that are installed. Tesseract
    fails outright if a requested language pack is missing (for example
    'eng+kor' without tesseract-ocr-kor), so fall back gracefully.
    """
    global _installed_languages
    if _installed_languages is None:
        try:
            _installed_languages = set(pytesseract.get_languages(config=''))
        except Exception:
            return languages
    installed = _installed_languages
    wanted = [lang for lang in languages.split('+') if lang in installed]
    if not wanted:
        wanted = ['eng'] if 'eng' in installed else sorted(installed)[:1]
    resolved = '+'.join(wanted)
    if resolved != languages:
        logger.info(f"OCR languages '{languages}' not all installed, using '{resolved}'")
    return resolved


def count_item_lines(text: str) -> int:
    """Count lines that look like a receipt item: letters followed by a price."""
    return sum(1 for line in text.splitlines() if re.search(r'[A-Za-z]{2,}.*\d+[.,]\d{2}\s*[A-Z]?\s*$', line.strip()))


def text_score(text: str) -> Tuple[int, int, int]:
    """Rank OCR outputs: item-like lines first, then a found total, then length."""
    has_total = int(bool(re.search(r'\btotal\b', text, re.I)))
    return count_item_lines(text), has_total, len(text)


def looks_complete(text: str) -> bool:
    """True when a pass already produced a plausible receipt, so the slower passes can be skipped."""
    items, has_total, _ = text_score(text)
    return items >= 2 and has_total == 1


def _run_tesseract(image: np.ndarray, languages: str, config: str) -> str:
    try:
        return pytesseract.image_to_string(image, lang=languages, config=config, timeout=TESSERACT_TIMEOUT)
    except pytesseract.TesseractNotFoundError:
        raise
    except RuntimeError as e:  # pytesseract raises RuntimeError on timeout
        logger.warning(f"OCR pass {config} gave up after {TESSERACT_TIMEOUT}s: {e}")
        return ""
    except Exception as e:
        logger.warning(f"OCR attempt failed with config {config}: {e}")
        return ""


def extract_text_from_image(image_path: str, languages: str = 'eng+kor', passes: Optional[List[Tuple[str, str]]] = None,
                            stats: Optional[Dict] = None) -> str:
    """
    Extract receipt text with as few Tesseract calls as the image allows.

    Args:
        image_path: path to the receipt image
        languages: Tesseract language codes ('eng+kor' falls back to what is installed)
        passes: override OCR_PASSES (used by the benchmark)
        stats: optional dict that receives timing and pass counts

    Returns:
        Cleaned OCR text ('' on failure). Raises TesseractNotFoundError if
        Tesseract is missing.
    """
    if not is_tesseract_available():
        raise pytesseract.TesseractNotFoundError()
    languages = resolve_languages(languages)
    passes = passes or OCR_PASSES
    started = time.perf_counter()
    try:
        gray = load_grayscale(image_path)
    except Exception as e:
        logger.error(f"Image preprocessing error for {image_path}: {e}")
        return ""
    prepared = time.perf_counter()

    cache: Dict[str, np.ndarray] = {}

    def image_for(variant: str) -> np.ndarray:
        if variant not in cache:
            cache[variant] = VARIANTS[variant](gray)
        return cache[variant]

    first_variant, first_config = passes[0]
    best = _run_tesseract(image_for(first_variant), languages, first_config)
    used = 1
    if not looks_complete(best) and len(passes) > 1:
        rest = passes[1:]
        for variant, _ in rest:
            image_for(variant)
        # Tesseract runs as a subprocess, so threads give real parallelism.
        workers = max(1, min(len(rest), (os.cpu_count() or 2) - 1, 3))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(lambda p: _run_tesseract(cache[p[0]], languages, p[1]), rest))
        used += len(rest)
        for text in results:
            if text_score(text) > text_score(best):
                best = text

    best = post_process_ocr_text(best)
    if stats is not None:
        stats.update({"passes": used, "preprocess_s": prepared - started, "total_s": time.perf_counter() - started})
    logger.info(f"OCR text extracted: {len(best)} characters in {used} pass(es), "
                f"{time.perf_counter() - started:.2f}s")
    return best


def post_process_ocr_text(text: str) -> str:
    """Fix common OCR misreads and normalize whitespace, keeping one receipt line per line."""
    corrections = {
        'О': 'O', 'о': 'o', 'І': 'I', 'і': 'i',  # Cyrillic look-alikes
        'ㅇ': '0', '○': '0', 'ㅣ': '1',
        '\u2014': '-', '\u2013': '-', '\u2019': "'", '\u2018': "'",  # long dashes and curly quotes
    }
    for wrong, correct in corrections.items():
        text = text.replace(wrong, correct)
    lines = (re.sub(r'[ \t\f\v]+', ' ', line).strip() for line in text.splitlines())
    text = '\n'.join(line for line in lines if line)
    text = re.sub(r'[|]{2,}', '|', text)
    text = re.sub(r'[-]{3,}', '-', text)
    return text


# ---------------------------------------------------------------- parsing

def extract_dates_from_text(text: str, day_first: bool = False) -> str:
    """Purchase date as YYYY-MM-DD, or today's date when the receipt has none."""
    return receipt_parser.find_receipt_date(text, day_first=day_first) or receipt_parser.today_iso()


def extract_quantity_and_price(line: str) -> Tuple[int, Optional[str]]:
    """Quantity and line price from a single receipt line, e.g. '2x Milk $5.98' -> (2, '5.98')."""
    if receipt_parser.PRICE_AT_END.search(line):
        parts = receipt_parser._split_item_line(line, "unknown")
        if parts:
            _, qty, price = parts
            return qty, None if price is None else f"{price:.2f}"
    q = receipt_parser.QTY_AT.match(line)
    if q:
        return int(q["qty"]), f"{receipt_parser.to_amount(q['unit']) * int(q['qty']):.2f}"
    return 1, None


def calculate_confidence_score(item: Dict) -> float:
    return receipt_parser.calculate_confidence(item)


def parse_receipt_text(text: str, receipt_type: Optional[str] = None, purchase_date: Optional[str] = None) -> List[Dict]:
    """
    Parse receipt text into raw items (before name normalization), in receipt order.

    Each item has name, quantity, price (line total as a string), unit_price,
    purchase_date and confidence, plus discount or weight when printed.
    """
    purchase_date = purchase_date or extract_dates_from_text(text)
    items = receipt_parser.parse_receipt_items(text, receipt_type)
    for item in items:
        item['purchase_date'] = purchase_date
        item['confidence'] = calculate_confidence_score(item)
    logger.info(f"Parsed {len(items)} items from receipt")
    return items


def parse_receipt(text: str, day_first: bool = False) -> Dict:
    """
    Full text pipeline: date, layout type, store, items with normalized names and categories.

    Returns a dict with keys items, date (None if not printed), receipt_type, store, quality.
    """
    text = post_process_ocr_text(text)
    receipt_type = detect_receipt_type(text)
    found_date = receipt_parser.find_receipt_date(text, day_first=day_first)
    items = parse_receipt_text(text, receipt_type, found_date or receipt_parser.today_iso())
    items = merge_duplicate_items(validate_and_fix_items(items))
    for item in items:
        item.setdefault('category', get_category_suggestion(item['name']))
    quality = analyze_receipt_quality(text, items)
    for item in items:
        item['quality_score'] = quality['quality_score']
    return {
        'items': items,
        'date': found_date,
        'receipt_type': receipt_type,
        'store': extract_store_info(text).get('name'),
        'quality': quality,
        'text': text,
    }


def analyze_receipt_image(image_path: str, languages: str = 'eng+kor') -> Dict:
    """OCR an image and parse it. Same keys as parse_receipt() plus 'ocr_seconds' and 'passes'."""
    stats: Dict = {}
    text = extract_text_from_image(image_path, languages, stats=stats)
    if not text or len(text.strip()) < 10:
        logger.warning("No meaningful text extracted from image")
        return {'items': [], 'date': None, 'receipt_type': 'unknown', 'store': None, 'quality': None, 'text': text or '',
                'ocr_seconds': stats.get('total_s'), 'passes': stats.get('passes')}
    result = parse_receipt(text)
    result['ocr_seconds'] = stats.get('total_s')
    result['passes'] = stats.get('passes')
    logger.info(f"Receipt type: {result['receipt_type']}, store: {result['store']}, {len(result['items'])} items")
    return result


def process_receipt_image(image_path, languages='eng+kor'):
    """
    Process a receipt image and return the list of parsed grocery items.
    Raises TesseractNotFoundError when Tesseract is missing; returns [] on other errors.
    """
    try:
        logger.info(f"Processing receipt image: {image_path}")
        return analyze_receipt_image(image_path, languages)['items']
    except pytesseract.TesseractNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error processing receipt image {image_path}: {e}", exc_info=True)
        return []
