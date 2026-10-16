"""
Post-processing for parsed receipt items: product name normalization against
the curated catalog (product_catalog.py), duplicate merging, validation,
quality analysis, and category suggestions.
"""
import logging
import re
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple

import product_catalog
from receipt_parser import detect_receipt_type as _detect_layout

try:
    from fuzzywuzzy import fuzz
    FUZZY_AVAILABLE = True
except ImportError:  # pragma: no cover - fuzzywuzzy is in requirements.txt
    FUZZY_AVAILABLE = False
    logging.warning("fuzzywuzzy not available, fuzzy matching disabled")

logger = logging.getLogger(__name__)

# Cyrillic look-alikes that OCR sometimes returns inside Latin text.
OCR_CORRECTIONS = {'О': 'O', 'о': 'o', 'І': 'I', 'і': 'i', 'Е': 'E', 'е': 'e', 'А': 'A', 'а': 'a'}


def normalize_product_name(name: str) -> Tuple[str, float]:
    """
    Map a receipt name to a clean product name.

    Known products (see product_catalog.py) come back as their catalog name with
    a confidence boost of up to 15 points. Unknown names are cleaned up (item
    codes, sizes and store-brand words removed, receipt shorthand expanded) and
    title-cased, with no boost.

    Returns:
        (normalized_name, confidence_boost)
    """
    if not name:
        return name, 0.0
    for wrong, right in OCR_CORRECTIONS.items():
        name = name.replace(wrong, right)

    canonical, score = product_catalog.match_product(name, fuzz.ratio if FUZZY_AVAILABLE else None)
    if canonical:
        logger.debug(f"Product normalized: '{name}' -> '{canonical}' ({score:.0f})")
        return canonical, round(15.0 * score / 100.0, 1)

    cleaned = product_catalog.clean_receipt_name(name) or name
    return clean_product_name(cleaned), 0.0


def clean_product_name(name: str) -> str:
    """Collapse whitespace, trim punctuation, and capitalize each word."""
    name = re.sub(r'\s+', ' ', name)
    name = re.sub(r'^[^\w]+|[^\w%]+$', '', name)
    return ' '.join(w.capitalize() if re.match(r'^[a-zA-Z]', w) else w for w in name.split()).strip()


def detect_receipt_type(text: str) -> str:
    """Receipt layout: supermarket, convenience, warehouse, online or unknown."""
    receipt_type = _detect_layout(text)
    logger.info(f"Receipt type detected: {receipt_type}")
    return receipt_type


def extract_store_info(text: str) -> Dict[str, Optional[str]]:
    """Store name (first meaningful line) and phone number from the receipt header."""
    info: Dict[str, Optional[str]] = {'name': None, 'address': None, 'phone': None}
    lines = text.split('\n')[:10]
    for line in lines:
        match = re.search(r'(\(?\d{2,3}\)?[-.\s]?\d{3,4}[-.\s]\d{4})', line)
        if match:
            info['phone'] = match.group(1)
            break
    for line in lines:
        line = line.strip()
        if len(line) > 3 and re.search(r'[A-Za-z]{3,}', line) and not re.match(r'^[\d\s\-/]+$', line):
            info['name'] = line
            break
    return info


def _money(value) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def merge_duplicate_items(items: List[Dict]) -> List[Dict]:
    """
    Merge items that are the same product (the same name printed twice, or two
    near-identical OCR readings). Quantities and line totals are added up.
    """
    if not items:
        return items

    merged: List[Dict] = []
    for item in items:
        target = None
        for existing in merged:
            a, b = existing['name'].lower(), item['name'].lower()
            similarity = SequenceMatcher(None, a, b).ratio()
            if FUZZY_AVAILABLE:
                similarity = max(similarity, fuzz.ratio(a, b) / 100)
            if similarity > 0.9:
                target = existing
                break
        if target is None:
            merged.append(dict(item))
            continue
        target['quantity'] += item['quantity']
        p1, p2 = _money(target.get('price')), _money(item.get('price'))
        if p1 is not None and p2 is not None:
            target['price'] = f"{p1 + p2:.2f}"
        target['confidence'] = max(target.get('confidence', 50), item.get('confidence', 50))
        logger.debug(f"Merged duplicate: '{target['name']}' + '{item['name']}'")

    logger.info(f"Merged {len(items)} items into {len(merged)} unique items")
    return merged


def validate_and_fix_items(items: List[Dict]) -> List[Dict]:
    """Normalize names, clamp quantities, and drop items without a usable name."""
    fixed_items = []
    for item in items:
        item = dict(item)
        item['raw_name'] = item.get('raw_name', item['name'])
        normalized_name, confidence_boost = normalize_product_name(item['name'])
        item['name'] = normalized_name
        item['confidence'] = item.get('confidence', 50) + confidence_boost

        qty = item.get('quantity', 1)
        if qty < 1:
            item['quantity'] = 1
        elif qty > 100:
            logger.warning(f"Suspicious quantity {qty} for '{item['name']}', capping at 10")
            item['quantity'] = 10
            item['confidence'] -= 10

        if len(item['name']) < 2:
            logger.debug(f"Skipping item with too short name: '{item['name']}'")
            continue
        item['confidence'] = max(0, min(100, item['confidence']))
        fixed_items.append(item)
    return fixed_items


def analyze_receipt_quality(text: str, items: List[Dict]) -> Dict[str, Any]:
    """Overall quality score (0-100) with warnings and suggestions for the user."""
    analysis: Dict[str, Any] = {
        'text_length': len(text),
        'item_count': len(items),
        'avg_confidence': 0.0,
        'quality_score': 0,
        'warnings': [],
        'suggestions': []
    }
    if items:
        analysis['avg_confidence'] = sum(item.get('confidence', 50) for item in items) / len(items)

    quality = 50
    if analysis['text_length'] > 100:
        quality += 10
    if analysis['item_count'] > 0:
        quality += 20
    if analysis['avg_confidence'] > 60:
        quality += 20

    if analysis['text_length'] < 50:
        analysis['warnings'].append('Very little text extracted - image may be blurry')
        quality -= 20
    if analysis['item_count'] == 0:
        analysis['warnings'].append('No items detected in receipt')
        analysis['suggestions'].append('Try taking a clearer photo with better lighting')
        quality -= 30
    if analysis['avg_confidence'] < 50:
        analysis['warnings'].append('Low confidence in extracted items')
        analysis['suggestions'].append('Please review and verify item names')
    if len(text) > 50 and analysis['item_count'] < 3:
        analysis['warnings'].append('Text detected but few items parsed')
        analysis['suggestions'].append('Receipt format may not be recognized')

    analysis['quality_score'] = max(0, min(100, quality))
    return analysis


CATEGORY_KEYWORDS = {
    'Dairy': ['uyu', 'milk', 'chijeu', 'cheese', 'yogeoteu', 'yogurt', 'beoteo', 'butter', 'cream', 'egg'],
    'Meat': ['gogi', 'dwaeji', 'sogogi', 'dak', 'pork', 'beef', 'chicken', 'meat', 'ham', 'turkey',
             'salmon', 'fish', 'shrimp', 'steak', 'sausage', 'bacon'],
    'Produce': ['sagwa', 'banana', 'tomato', 'yangpa', 'gamja', 'danggeun', 'baechu', 'apple',
                'onion', 'potato', 'carrot', 'lettuce', 'fruit', 'gwail', 'chaeso', 'vegetable',
                'spinach', 'berr', 'avocado', 'pepper', 'cucumber', 'grape', 'lemon', 'lime', 'salad'],
    'Bakery': ['ppang', 'bread', 'keikeu', 'cake', 'donut', 'bagel', 'muffin', 'bun', 'roll'],
    'Frozen': ['aiseukeurim', 'ice cream', 'naengdong', 'frozen'],
    'Beverages': ['mul', 'eumryo', 'juseu', 'kola', 'saida', 'maekju', 'soju', 'water', 'juice',
                  'cola', 'beer', 'sprite', 'coffee', 'keopi', 'tea', 'cha', 'drink', 'soda', 'wine'],
    'Snacks': ['gwaja', 'seunaek', 'chokollit', 'snack', 'chocolate', 'chip', 'candy', 'satang', 'cookie', 'cracker'],
    'Pantry': ['ramyeon', 'ssal', 'ramen', 'rice', 'pasta', 'tongjorim', 'can', 'noodle', 'sauce', 'flour', 'oil'],
}


def get_category_suggestion(product_name: str) -> str:
    """Category for a product name: catalog lookup first, then keyword matching."""
    category = product_catalog.category_for(product_name)
    if category:
        return category
    name_lower = product_name.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in name_lower for keyword in keywords):
            return category
    return 'Other'
