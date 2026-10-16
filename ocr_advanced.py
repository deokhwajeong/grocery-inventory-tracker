"""
Advanced OCR Enhancement Module
Provides AI-powered product name normalization and advanced text processing.
"""
import re
import logging
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher
try:
    from fuzzywuzzy import fuzz
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False
    logging.warning("fuzzywuzzy not available, fuzzy matching disabled")

logger = logging.getLogger(__name__)

# Common product name database for normalization
# Keys are canonical English names, values are common variants including romanized forms
COMMON_PRODUCTS = {
    # Dairy and Eggs
    'milk': ['uyu', 'milkeu', 'melk'],
    'egg': ['gyeran', 'egeu', 'ran', 'eggs'],

    # Bakery
    'bread': ['ppang', 'beu-re-deu', 'bred'],

    # Fruits
    'apple': ['sagwa', 'aepeul', 'aple'],
    'banana': ['banana', 'beonana', 'bananna'],
    'tomato': ['tomato', 'tomeyito', 'tomatoe'],

    # Vegetables
    'onion': ['yangpa', 'eonieon', 'oinion'],
    'potato': ['gamja', 'poteyito', 'potatoe'],
    'carrot': ['danggeun', 'kaeret', 'carott'],
    'cabbage': ['baechu', 'kaebiji', 'cabage'],

    # Meat
    'pork': ['dwaejigogi', 'pokeu', 'prok'],
    'beef': ['sogogi', 'bipeu', 'beaf'],
    'chicken': ['dalgogi', 'chikin', 'chiken'],

    # Beverages
    'water': ['saengsu', 'woteo', 'mineral-water'],
    'cola': ['kola', 'kokakola', 'coke'],
    'sprite': ['saida', 'seupeuraiteu', 'chilseong'],
    'beer': ['maekju', 'bieo', 'beeer'],
    'soju': ['soju', 'sojyu', 'korean-spirit'],

    # Prepared Foods
    'ramen': ['ramyeon', 'ramen', 'instant noodle'],
    'kimchi': ['kimchi', 'gimchi', 'kimchee'],
    'tofu': ['dubu', 'bean-curd', 'soybean'],

    # Dairy Products
    'cheese': ['chijeu', 'chiijeu', 'cheeze'],
    'yogurt': ['yogeoteu', 'yogureuteu', 'yoghurt'],
    'ice cream': ['aiseukeurim', 'ice-cream', 'icecream'],

    # Snacks and Sweets
    'snack': ['gwaja', 'seunaek', 'snacks'],
    'chocolate': ['chokollit', 'chokollet', 'choco'],

    # Hot Beverages
    'coffee': ['keopi', 'kape', 'cofee'],
    'tea': ['cha', 'ti', 'tee'],

    # Grains
    'rice': ['ssal', 'rice', 'grain'],
}

# Reversed mapping for faster lookup
PRODUCT_VARIANTS = {}
for canonical, variants in COMMON_PRODUCTS.items():
    for variant in variants:
        PRODUCT_VARIANTS[variant.lower()] = canonical
    PRODUCT_VARIANTS[canonical.lower()] = canonical

# Common OCR errors in English/romanized text
OCR_CORRECTIONS = {
    # Number confusions (Cyrillic look-alikes only; mapping Latin 'O'/'l'
    # here turned product names like "Milk" into "Mi1k")
    'О': '0', 'о': '0',
    'І': '1', 'і': '1',

    # Romanized character confusions
    'dwo': 'dae', 'jyu': 'ju', 'toe': 'toe',

    # Brand name fixes (romanized Korean brands)
    'lotte': 'LOTTE', 'lotde': 'LOTTE', 'samsung': 'SAMSUNG',
    'elji': 'LG', 'CJ': 'CJ', 'nongshim': 'Nongshim', 'ottogi': 'Ottogi',
}

# Noise words to remove from product names
# Romanized units: gae=ea, bong=bundle, paek=pack, ip=piece, byeong=bottle, kaen=can, bakseu=box
# Romanized measurements: geulaem=gram, killo=kilo, liteo=liter
# Romanized quality words: sinseon=fresh, peurimieum=premium, yuginong=organic
NOISE_WORDS = {
    'units': ['gae', 'bong', 'paek', 'ip', 'byeong', 'kaen', 'bakseu', 'box', 'pack', 'ea', 'pcs'],
    'measurement': ['g', 'kg', 'ml', 'l', 'oz', 'lb', 'geulaem', 'killo', 'liteo'],
    'quality': ['sinseon', 'peurimieum', 'premium', 'fresh', 'organic', 'yuginong'],
}


def normalize_product_name(name: str) -> Tuple[str, float]:
    """
    Normalize and correct product name using AI-powered fuzzy matching.

    Args:
        name (str): Raw product name from OCR

    Returns:
        Tuple[str, float]: (normalized_name, confidence_boost)
    """
    if not name:
        return name, 0.0

    original_name = name
    confidence_boost = 0.0

    # Step 1: Apply OCR corrections
    for wrong, correct in OCR_CORRECTIONS.items():
        name = name.replace(wrong, correct)

    # Step 2: Remove noise words
    name_lower = name.lower()
    for noise_category, words in NOISE_WORDS.items():
        for word in words:
            # Remove as whole word
            name_lower = re.sub(r'\b' + re.escape(word) + r'\b', '', name_lower, flags=re.IGNORECASE)

    # Restore case from original
    name = name.strip()

    # Step 3: Check exact match in product database
    name_key = name.lower().strip()
    if name_key in PRODUCT_VARIANTS:
        canonical = PRODUCT_VARIANTS[name_key]
        logger.debug(f"Product normalized: '{original_name}' -> '{canonical}'")
        return clean_product_name(canonical), 15.0  # Boost confidence for known products

    # Step 4: Fuzzy matching for similar products
    if FUZZY_AVAILABLE and len(name) > 2:
        best_match = None
        best_score = 0

        for variant, canonical in PRODUCT_VARIANTS.items():
            score = fuzz.ratio(name_key, variant)
            if score > best_score and score > 80:  # High threshold for fuzzy match
                best_score = score
                best_match = canonical

        if best_match:
            confidence_boost = (best_score - 80) / 4  # 0-5 boost for 80-100 match
            logger.debug(f"Fuzzy match: '{original_name}' -> '{best_match}' (score: {best_score})")
            return clean_product_name(best_match), confidence_boost

    # Step 5: Clean up the name
    name = clean_product_name(name)

    return name, confidence_boost


def clean_product_name(name: str) -> str:
    """
    Clean product name by removing extra whitespace and special characters.

    Args:
        name (str): Product name to clean

    Returns:
        str: Cleaned product name
    """
    # Remove multiple spaces
    name = re.sub(r'\s+', ' ', name)

    # Remove leading/trailing special characters
    name = re.sub(r'^[^\w]+|[^\w]+$', '', name)

    # Capitalize first letter of English words
    words = name.split()
    cleaned_words = []
    for word in words:
        if re.match(r'^[a-zA-Z]', word):
            cleaned_words.append(word.capitalize())
        else:
            cleaned_words.append(word)

    return ' '.join(cleaned_words).strip()


def detect_receipt_type(text: str) -> str:
    """
    Detect the type of receipt (supermarket, convenience store, online, etc.).

    Args:
        text (str): OCR extracted text

    Returns:
        str: Receipt type
    """
    text_lower = text.lower()

    # Korean major retailers (romanized)
    retailers = {
        'emart': ['eemart', 'emart', 'e-mart', 'eemarteu'],
        'homeplus': ['homplleoseu', 'homeplus', 'home-plus'],
        'lotte': ['lotde', 'lotte', 'lotte-mart', 'lottemart'],
        'gs25': ['gs25', 'gs 25', 'jieseu25'],
        'cu': ['cu', 'ssiu', 'cvs', 'convenience'],
        '7eleven': ['sebeunil-lebeu', '7-eleven', '7eleven'],
        'coupang': ['kupang', 'coupang', 'coopang'],
        'market_kurly': ['makeskeolri', 'kurly', 'market-kurly'],
    }

    for retailer_type, keywords in retailers.items():
        if any(keyword in text_lower for keyword in keywords):
            logger.info(f"Receipt type detected: {retailer_type}")
            return retailer_type

    # Determine by content (romanized Korean keywords)
    if any(word in text_lower for word in ['pyeonuijeom', 'convenience', '24sigan', '24hour']):
        return 'convenience_store'
    elif any(word in text_lower for word in ['mateu', 'mart', 'supermarket', 'syupeo', 'super']):
        return 'supermarket'
    elif any(word in text_lower for word in ['baedal', 'delivery', 'jumun', 'order']):
        return 'online'

    return 'unknown'


def extract_store_info(text: str) -> Dict[str, Optional[str]]:
    """
    Extract store information from receipt.

    Args:
        text (str): OCR extracted text

    Returns:
        Dict: Store information (name, address, phone)
    """
    info = {
        'name': None,
        'address': None,
        'phone': None
    }

    lines = text.split('\n')[:10]  # Usually in first 10 lines

    # Extract phone number
    phone_patterns = [
        r'(\d{2,3}[-\s]?\d{3,4}[-\s]?\d{4})',  # 02-1234-5678
        r'(1\d{3}[-\s]?\d{4})',  # 1588-1234
    ]

    for line in lines:
        for pattern in phone_patterns:
            match = re.search(pattern, line)
            if match and not info['phone']:
                info['phone'] = match.group(1)
                break

    # Detect store name (usually first meaningful line)
    for line in lines:
        line = line.strip()
        if len(line) > 3 and not re.match(r'^[\d\s\-/]+$', line):
            # Avoid pure number lines
            if re.search(r'[a-zA-Z0-9]{2,}', line):
                info['name'] = line
                break

    return info


def merge_duplicate_items(items: List[Dict]) -> List[Dict]:
    """
    Merge duplicate items that are likely the same product.

    Args:
        items (List[Dict]): List of parsed items

    Returns:
        List[Dict]: Merged items with combined quantities
    """
    if not items:
        return items

    merged = []
    processed = set()

    for i, item1 in enumerate(items):
        if i in processed:
            continue

        combined_qty = item1['quantity']
        max_confidence = item1.get('confidence', 50)

        # Look for similar items
        for j, item2 in enumerate(items[i+1:], start=i+1):
            if j in processed:
                continue

            # Check similarity
            similarity = SequenceMatcher(None,
                                        item1['name'].lower(),
                                        item2['name'].lower()).ratio()

            # Also check with fuzzy matching if available
            if FUZZY_AVAILABLE:
                fuzzy_sim = fuzz.ratio(item1['name'].lower(), item2['name'].lower()) / 100
                similarity = max(similarity, fuzzy_sim)

            # Merge if very similar (>85% match)
            if similarity > 0.85:
                combined_qty += item2['quantity']
                max_confidence = max(max_confidence, item2.get('confidence', 50))
                processed.add(j)
                logger.debug(f"Merged duplicate: '{item1['name']}' + '{item2['name']}'")

        merged_item = item1.copy()
        merged_item['quantity'] = combined_qty
        merged_item['confidence'] = max_confidence
        merged.append(merged_item)
        processed.add(i)

    logger.info(f"Merged {len(items)} items into {len(merged)} unique items")
    return merged


def validate_and_fix_items(items: List[Dict]) -> List[Dict]:
    """
    Validate and automatically fix common issues in parsed items.

    Args:
        items (List[Dict]): List of parsed items

    Returns:
        List[Dict]: Validated and fixed items
    """
    fixed_items = []

    for item in items:
        # Normalize product name
        normalized_name, confidence_boost = normalize_product_name(item['name'])
        item['name'] = normalized_name
        item['confidence'] = item.get('confidence', 50) + confidence_boost

        # Validate quantity
        qty = item.get('quantity', 1)
        if qty < 1:
            item['quantity'] = 1
        elif qty > 100:
            # Likely OCR error, reduce to reasonable amount
            logger.warning(f"Suspicious quantity {qty} for '{item['name']}', capping at 10")
            item['quantity'] = 10
            item['confidence'] -= 10

        # Ensure name is not too short
        if len(item['name']) < 2:
            logger.debug(f"Skipping item with too short name: '{item['name']}'")
            continue

        # Ensure confidence is in range
        item['confidence'] = max(0, min(100, item['confidence']))

        fixed_items.append(item)

    return fixed_items


def analyze_receipt_quality(text: str, items: List[Dict]) -> Dict[str, any]:
    """
    Analyze the quality of OCR extraction and provide feedback.

    Args:
        text (str): Extracted text
        items (List[Dict]): Parsed items

    Returns:
        Dict: Quality metrics and suggestions
    """
    analysis = {
        'text_length': len(text),
        'item_count': len(items),
        'avg_confidence': 0.0,
        'quality_score': 0,
        'warnings': [],
        'suggestions': []
    }

    # Calculate average confidence
    if items:
        total_conf = sum(item.get('confidence', 50) for item in items)
        analysis['avg_confidence'] = total_conf / len(items)

    # Determine quality score (0-100)
    quality = 50

    if analysis['text_length'] > 100:
        quality += 10
    if analysis['item_count'] > 0:
        quality += 20
    if analysis['avg_confidence'] > 60:
        quality += 20

    # Check for issues
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


def get_category_suggestion(product_name: str) -> str:
    """
    Suggest category based on product name using keyword matching.

    Args:
        product_name (str): Product name

    Returns:
        str: Suggested category
    """
    name_lower = product_name.lower()

    category_keywords = {
        'Dairy': ['uyu', 'milk', 'chijeu', 'cheese', 'yogeoteu', 'yogurt', 'beoteo', 'butter', 'cream'],
        'Meat': ['gogi', 'dwaeji', 'sogogi', 'dak', 'pork', 'beef', 'chicken', 'meat', 'ham'],
        'Produce': ['sagwa', 'banana', 'tomato', 'yangpa', 'gamja', 'danggeun', 'baechu', 'apple',
                    'onion', 'potato', 'carrot', 'lettuce', 'fruit', 'gwail', 'chaeso', 'vegetable',
                    'spinach', 'berr', 'avocado', 'pepper', 'cucumber', 'grape', 'lemon'],
        'Bakery': ['ppang', 'bread', 'keikeu', 'cake', 'donut', 'bagel', 'muffin'],
        'Frozen': ['aiseukeurim', 'ice cream', 'naengdong', 'frozen'],
        'Beverages': ['mul', 'eumryo', 'juseu', 'kola', 'saida', 'maekju', 'soju', 'water', 'juice',
                      'cola', 'beer', 'sprite', 'coffee', 'keopi', 'tea', 'cha', 'drink'],
        'Snacks': ['gwaja', 'seunaek', 'chokollit', 'snack', 'chocolate', 'chip', 'candy', 'satang'],
        'Pantry': ['ramyeon', 'ssal', 'ramen', 'rice', 'pasta', 'tongjorim', 'can', 'noodle'],
    }

    for category, keywords in category_keywords.items():
        if any(keyword in name_lower for keyword in keywords):
            return category

    return 'Other'
