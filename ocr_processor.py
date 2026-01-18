"""
OCR Processing Module for Grocery Inventory Tracker
Handles receipt image preprocessing, text extraction, and item parsing.
Advanced version with multi-stage preprocessing and intelligent parsing.
"""
import re
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import pytesseract
from PIL import Image, ImageEnhance
import cv2
import numpy as np

# Import advanced OCR features
try:
    from ocr_advanced import (
        normalize_product_name,
        detect_receipt_type,
        extract_store_info,
        merge_duplicate_items,
        validate_and_fix_items,
        analyze_receipt_quality,
        get_category_suggestion
    )
    ADVANCED_FEATURES = True
except ImportError:
    ADVANCED_FEATURES = False
    logging.warning("Advanced OCR features not available")

# Setup logging
logger = logging.getLogger(__name__)


def preprocess_image(image_path: str) -> List[np.ndarray]:
    """
    Advanced preprocessing with multiple strategies for improved OCR accuracy.
    Returns multiple preprocessed versions for better text extraction.
    
    Args:
        image_path (str): Path to the receipt image file
        
    Returns:
        List[np.ndarray]: Multiple preprocessed image versions
        
    Raises:
        Exception: If image cannot be read or processed
    """
    try:
        # Read image
        img = cv2.imread(image_path)
        
        if img is None:
            raise ValueError(f"Failed to read image from {image_path}")
        
        processed_images = []
        
        # 1. Auto-rotation correction using deskew
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = deskew_image(gray)
        
        # 2. Contrast enhancement
        enhanced = enhance_contrast(gray)
        processed_images.append(enhanced)
        
        # 3. Adaptive thresholding (good for uneven lighting)
        adaptive = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        processed_images.append(adaptive)
        
        # 4. Otsu's thresholding (good for bimodal images)
        _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        denoised_otsu = cv2.fastNlMeansDenoising(otsu)
        processed_images.append(denoised_otsu)
        
        # 5. Morphological operations for text enhancement
        kernel = np.ones((1, 1), np.uint8)
        morph = cv2.morphologyEx(denoised_otsu, cv2.MORPH_CLOSE, kernel)
        processed_images.append(morph)
        
        # 6. Sharpening for blurry images
        sharpened = sharpen_image(gray)
        processed_images.append(sharpened)
        
        logger.debug(f"Generated {len(processed_images)} preprocessed versions")
        return processed_images
    
    except Exception as e:
        logger.error(f"Image preprocessing error for {image_path}: {e}")
        raise


def deskew_image(image: np.ndarray) -> np.ndarray:
    """
    Detect and correct skewed text in receipt images.
    
    Args:
        image (np.ndarray): Grayscale input image
        
    Returns:
        np.ndarray: Deskewed image
    """
    try:
        # Detect edges
        edges = cv2.Canny(image, 50, 150, apertureSize=3)
        
        # Detect lines using Hough transform
        lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)
        
        if lines is not None:
            # Calculate average angle
            angles = []
            for rho, theta in lines[:, 0]:
                angle = np.degrees(theta) - 90
                if abs(angle) < 45:  # Only consider reasonable angles
                    angles.append(angle)
            
            if angles:
                median_angle = np.median(angles)
                
                # Only rotate if angle is significant
                if abs(median_angle) > 0.5:
                    (h, w) = image.shape
                    center = (w // 2, h // 2)
                    M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                    rotated = cv2.warpAffine(
                        image, M, (w, h),
                        flags=cv2.INTER_CUBIC,
                        borderMode=cv2.BORDER_REPLICATE
                    )
                    logger.debug(f"Image deskewed by {median_angle:.2f} degrees")
                    return rotated
        
        return image
    
    except Exception as e:
        logger.warning(f"Deskewing failed: {e}, returning original")
        return image


def enhance_contrast(image: np.ndarray) -> np.ndarray:
    """
    Enhance image contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization).
    
    Args:
        image (np.ndarray): Grayscale input image
        
    Returns:
        np.ndarray: Contrast-enhanced image
    """
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(image)
    return enhanced


def sharpen_image(image: np.ndarray) -> np.ndarray:
    """
    Sharpen image to improve OCR on blurry receipts.
    
    Args:
        image (np.ndarray): Grayscale input image
        
    Returns:
        np.ndarray: Sharpened image
    """
    kernel = np.array([[-1, -1, -1],
                       [-1,  9, -1],
                       [-1, -1, -1]])
    sharpened = cv2.filter2D(image, -1, kernel)
    return sharpened



def extract_text_from_image(image_path: str, languages: str = 'eng+kor') -> str:
    """
    Extract text from receipt using multiple preprocessing strategies and OCR configurations.
    Combines results from different approaches for best accuracy.
    
    Args:
        image_path (str): Path to the receipt image file
        languages (str): OCR language codes (default: 'eng+kor')
        
    Returns:
        str: Extracted text from the image
    """
    try:
        # Get multiple preprocessed versions
        processed_images = preprocess_image(image_path)
        
        # Different Tesseract configurations for various receipt types
        configs = [
            '--psm 6',  # Assume uniform block of text
            '--psm 4',  # Assume single column of text
            '--psm 11', # Sparse text, find as much text as possible
            '--oem 3 --psm 6',  # LSTM + Legacy engine
        ]
        
        best_text = ""
        max_length = 0
        
        # Try each preprocessed image with different configs
        for idx, img in enumerate(processed_images):
            for config in configs:
                try:
                    text = pytesseract.image_to_string(
                        img, 
                        lang=languages,
                        config=config
                    )
                    
                    # Keep the result with most extracted text
                    if len(text) > max_length:
                        max_length = len(text)
                        best_text = text
                        logger.debug(f"Better result from image variant {idx}, config: {config}")
                
                except Exception as e:
                    logger.warning(f"OCR attempt failed with config {config}: {e}")
                    continue
        
        # Post-process text
        best_text = post_process_ocr_text(best_text)
        
        logger.info(f"OCR text extracted: {len(best_text)} characters (from {len(processed_images)} variants)")
        logger.debug(f"Extracted text preview: {best_text[:200]}...")
        
        return best_text
    
    except pytesseract.TesseractNotFoundError:
        logger.error("Tesseract OCR not found. Please install Tesseract.")
        raise
    
    except Exception as e:
        logger.error(f"OCR extraction error: {e}")
        return ""


def post_process_ocr_text(text: str) -> str:
    """
    Clean up OCR output by fixing common errors and normalizing text.
    
    Args:
        text (str): Raw OCR text
        
    Returns:
        str: Cleaned text
    """
    # Common OCR misreads corrections
    corrections = {
        'О': '0',  # Cyrillic O to zero
        'о': '0',
        'І': '1',  # Cyrillic I to one
        'і': '1',
        'ㅇ': '0',  # Korean O character to zero
        '○': '0',  # Circle to zero
        'ㅣ': '1',  # Korean I character to one
    }
    
    for wrong, correct in corrections.items():
        text = text.replace(wrong, correct)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove excessive special characters
    text = re.sub(r'[|]{2,}', '|', text)
    text = re.sub(r'[-]{3,}', '-', text)
    
    return text



def extract_dates_from_text(text: str) -> Optional[str]:
    """
    Advanced date extraction with multiple format support and validation.
    
    Args:
        text (str): Text containing potential dates
        
    Returns:
        Optional[str]: Extracted date in YYYY-MM-DD format or None
    """
    # Comprehensive date patterns
    date_patterns = [
        # Dot-separated format: 2024.01.15, 2024. 1. 15
        (r'(\d{4})[.\s]*(\d{1,2})[.\s]*(\d{1,2})', 'ymd'),
        # ISO style: 2024-01-15, 2024/01/15
        (r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', 'ymd'),
        # US style: 01/15/2024, 01-15-2024
        (r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})', 'mdy'),
        # European style: 15/01/2024, 15-01-2024
        (r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})', 'dmy'),
        # Short year: 24.01.15
        (r'(\d{2})[.\s]*(\d{1,2})[.\s]*(\d{1,2})', 'ymd_short'),
        # Korean date format with Hangul characters: 2024년 1월 15일 (year month day)
        (r'(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일', 'ymd'),
    ]
    
    current_year = datetime.now().year
    
    for pattern, format_type in date_patterns:
        matches = re.finditer(pattern, text)
        
        for match in matches:
            try:
                groups = match.groups()
                
                if format_type == 'ymd':
                    year, month, day = groups
                    year = int(year)
                elif format_type == 'ymd_short':
                    year, month, day = groups
                    year = int(year)
                    # Convert 2-digit year to 4-digit
                    year = 2000 + year if year < 100 else year
                elif format_type == 'mdy':
                    month, day, year = groups
                    year = int(year)
                elif format_type == 'dmy':
                    day, month, year = groups
                    year = int(year)
                else:
                    continue
                
                month = int(month)
                day = int(day)
                
                # Validation
                if not (1 <= month <= 12 and 1 <= day <= 31):
                    continue
                
                # Year should be reasonable (within 1 year past or future)
                if not (current_year - 1 <= year <= current_year + 1):
                    continue
                
                # Validate actual date
                date_str = f"{year}-{month:02d}-{day:02d}"
                datetime.strptime(date_str, '%Y-%m-%d')
                
                logger.debug(f"Date extracted: {date_str}")
                return date_str
                
            except (ValueError, TypeError) as e:
                logger.debug(f"Invalid date candidate: {match.group()} - {e}")
                continue
    
    # Default to today if no date found
    logger.debug("No valid date found, using today's date")
    return datetime.now().strftime('%Y-%m-%d')


def extract_quantity_and_price(line: str) -> Tuple[int, Optional[str]]:
    """
    Extract quantity and price from a receipt line.
    
    Args:
        line (str): Single line from receipt
        
    Returns:
        Tuple[int, Optional[str]]: (quantity, price) or (1, None)
    """
    quantity = 1
    price = None
    
    # Quantity patterns: 2x, 3X, 5×, 2ea (ea=each in Korean), x2, *2
    quantity_patterns = [
        r'(\d+)\s*[xX×*]\s*',      # 2x, 3X
        r'[xX×*]\s*(\d+)',           # x2, *2
        r'(\d+)\s*개',               # 2ea (Korean: 2개)
        r'(\d+)\s*EA',               # 2EA
    ]
    
    for pattern in quantity_patterns:
        match = re.search(pattern, line)
        if match:
            try:
                qty = int(match.group(1))
                if 1 <= qty <= 100:  # Reasonable range
                    quantity = qty
                    break
            except (ValueError, IndexError):
                continue
    
    # Price patterns: ₩1,000, $5.99, 1000won (won=Korean currency), 5,000
    price_patterns = [
        r'₩\s*([\d,]+\.?\d*)',       # ₩1,000
        r'\$\s*([\d,]+\.?\d*)',       # $5.99
        r'([\d,]+)\s*원',             # 1000원 (Korean won)
        r'([\d,]+\.?\d*)\s*$',        # 1,000 at end of line
    ]
    
    for pattern in price_patterns:
        match = re.search(pattern, line)
        if match:
            price = match.group(1).replace(',', '')
            break
    
    return quantity, price


def calculate_confidence_score(item: Dict) -> float:
    """
    Calculate confidence score for parsed item (0-100).
    
    Args:
        item (Dict): Parsed item dictionary
        
    Returns:
        float: Confidence score
    """
    score = 50.0  # Base score
    
    # Item name quality
    name = item.get('name', '')
    if len(name) >= 3:
        score += 10
    if len(name) >= 5:
        score += 10
    
    # Has Korean characters (common in Korean receipts)
    if re.search(r'[가-힣]', name):
        score += 10
    
    # Has English characters
    if re.search(r'[a-zA-Z]', name):
        score += 5
    
    # Quantity is reasonable
    qty = item.get('quantity', 1)
    if 1 <= qty <= 10:
        score += 10
    elif qty > 100:
        score -= 20
    
    # Has valid date
    if item.get('purchase_date'):
        score += 5
    
    return min(max(score, 0), 100)


def parse_receipt_text(text: str) -> List[Dict]:
    """
    Advanced parsing of OCR text to identify grocery items.
    Uses multiple strategies and confidence scoring.
    
    Args:
        text (str): Raw text extracted from receipt via OCR
        
    Returns:
        List[Dict]: List of dictionaries containing item details with confidence scores
    """
    items = []
    lines = text.split('\n')
    
    # Extract purchase date
    purchase_date = extract_dates_from_text(text)
    
    # Keywords to skip (header/footer that aren't grocery items)
    skip_keywords = [
        'receipt', 'store', 'address', 'tel', 'phone', 'tax', 'total', 'subtotal',
        'change', 'card', 'cash', 'thank', 'welcome', 'visit', 'vat', 'qty',
        'amount', 'payment', 'balance', 'tender', 'customer', 'cashier',
        # Korean words: receipt, address, phone, total, subtotal, vat, taxable, card, cash
        '영수증', '주소', '전화', '합계', '소계', '부가세', '과세', '카드', '현금',
        # Korean words: thanks, visit, customer, cashier, change, payment, settle, total, total
        '감사', '방문', '고객', '캐시어', '거스름', '지불', '결제', '총', '계',
        # Korean words: business, representative, manager, store, number, date, date, time, time
        '사업자', '대표', '담당', '매장', '번호', '날짜', 'date', 'time', '시간'
    ]
    
    # Pattern for receipt item lines (usually: item name + quantity/price)
    # 개 = ea (each), 원 = won (Korean currency)
    item_indicators = [r'\d+[xX×]', r'₩', r'\$', r'원', r'개', r'\d{1,3}[,\d]*']
    
    for line_num, line in enumerate(lines):
        line = line.strip()
        
        # Skip empty or very short lines
        if not line or len(line) < 2:
            continue
        
        # Skip header/footer lines
        if any(keyword in line.lower() for keyword in skip_keywords):
            continue
        
        # Skip lines that are just numbers or prices
        if re.match(r'^[\d,.\s₩$원]+$', line):
            continue
        
        # Check if line likely contains an item (has price or quantity indicator)
        has_indicator = any(re.search(pattern, line) for pattern in item_indicators)
        
        if has_indicator:
            # Extract quantity and price
            quantity, price = extract_quantity_and_price(line)
            
            # Clean item name
            item_name = line
            
            # Remove quantity markers (개 = ea/each in Korean, EA = each)
            item_name = re.sub(r'\d+\s*[xX×*개EA]\s*', '', item_name)
            item_name = re.sub(r'[xX×*]\s*\d+', '', item_name)
            
            # Remove price markers
            item_name = re.sub(r'₩\s*[\d,]+\.?\d*', '', item_name)
            item_name = re.sub(r'\$\s*[\d,]+\.?\d*', '', item_name)
            item_name = re.sub(r'[\d,]+\s*원', '', item_name)
            item_name = re.sub(r'[\d,]+\.?\d*\s*$', '', item_name)
            
            # Clean special characters (keep Korean Hangul, English, numbers, spaces)
            item_name = re.sub(r'[^\w\s가-힣0-9a-zA-Z]', ' ', item_name)
            item_name = ' '.join(item_name.split())  # Normalize whitespace
            
            # Validate item name
            if item_name and 2 <= len(item_name) <= 100:
                # Avoid duplicate consecutive items
                if items and items[-1]['name'] == item_name:
                    continue
                
                item = {
                    'name': item_name,
                    'quantity': quantity,
                    'purchase_date': purchase_date,
                    'price': price
                }
                
                # Calculate confidence
                confidence = calculate_confidence_score(item)
                item['confidence'] = confidence
                
                # Only add items with reasonable confidence (>= 40)
                if confidence >= 40:
                    items.append(item)
                    logger.debug(f"Item parsed: {item_name} (qty: {quantity}, conf: {confidence:.1f}%)")
                else:
                    logger.debug(f"Rejected low-confidence item: {item_name} (conf: {confidence:.1f}%)")
    
    # Sort by confidence (highest first)
    items.sort(key=lambda x: x['confidence'], reverse=True)
    
    logger.info(f"Parsed {len(items)} items from receipt")
    return items



def process_receipt_image(image_path, languages='eng+kor'):
    """
    Main function to process a receipt image and extract grocery items.
    Combines image preprocessing, OCR text extraction, and intelligent parsing.
    Enhanced with advanced normalization and quality analysis.
    
    Args:
        image_path (str): Path to the receipt image file
        languages (str): OCR language codes (default: 'eng+kor')
        
    Returns:
        list: List of parsed grocery items with name, quantity, purchase date, and metadata
    """
    try:
        logger.info(f"Processing receipt image: {image_path}")
        
        # Extract text from image
        text = extract_text_from_image(image_path, languages)
        
        if not text or len(text.strip()) < 10:
            logger.warning("No meaningful text extracted from image")
            return []
        
        # Advanced: Detect receipt type
        if ADVANCED_FEATURES:
            receipt_type = detect_receipt_type(text)
            store_info = extract_store_info(text)
            logger.info(f"Receipt type: {receipt_type}, Store: {store_info.get('name', 'Unknown')}")
        
        # Parse extracted text into structured items
        items = parse_receipt_text(text)
        
        if not items:
            logger.warning("No items parsed from receipt text")
            return []
        
        # Advanced: Normalize, validate and merge items
        if ADVANCED_FEATURES:
            logger.info("Applying advanced item processing...")
            items = validate_and_fix_items(items)
            items = merge_duplicate_items(items)
            
            # Add category suggestions
            for item in items:
                if 'category' not in item or not item['category']:
                    item['category'] = get_category_suggestion(item['name'])
                    logger.debug(f"Category suggested for '{item['name']}': {item['category']}")
            
            # Analyze quality
            quality_analysis = analyze_receipt_quality(text, items)
            logger.info(f"Receipt quality score: {quality_analysis['quality_score']}/100")
            logger.info(f"Average item confidence: {quality_analysis['avg_confidence']:.1f}%")
            
            if quality_analysis['warnings']:
                for warning in quality_analysis['warnings']:
                    logger.warning(f"Quality issue: {warning}")
            
            # Add quality metadata to items
            for item in items:
                item['quality_score'] = quality_analysis['quality_score']
        
        logger.info(f"Receipt processing complete: {len(items)} items extracted")
        return items
    
    except Exception as e:
        logger.error(f"Error processing receipt image {image_path}: {e}", exc_info=True)
        return []
