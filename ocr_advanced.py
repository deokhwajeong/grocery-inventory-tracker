"""
Advanced OCR Enhancement Module
Provides AI-powered product name normalization and advanced text processing.
"""
import re
import logging
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher
try:
    from fuzzywuzzy import fuzz, process
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False
    logging.warning("fuzzywuzzy not available, fuzzy matching disabled")

logger = logging.getLogger(__name__)

# Common product name database for normalization
COMMON_PRODUCTS = {
    # Korean products
    '우유': ['milk', '밀크', '牛乳'],
    '계란': ['egg', '에그', '란', '卵'],
    '빵': ['bread', '브레드', 'パン'],
    '사과': ['apple', '애플', 'リンゴ'],
    '바나나': ['banana', '버나나'],
    '토마토': ['tomato', '토메이토'],
    '양파': ['onion', '어니언'],
    '감자': ['potato', '포테이토'],
    '당근': ['carrot', '캐럿'],
    '배추': ['cabbage', '캐비지'],
    '돼지고기': ['pork', '포크'],
    '소고기': ['beef', '비프'],
    '닭고기': ['chicken', '치킨'],
    '생수': ['water', '워터', '미네랄워터'],
    '콜라': ['cola', '코카콜라', 'coke'],
    '사이다': ['sprite', '스프라이트', '칠성사이다'],
    '맥주': ['beer', '비어'],
    '소주': ['soju', '소쥬'],
    '라면': ['ramen', '라멘', 'instant noodle'],
    '김치': ['kimchi', '김챠', 'ｷﾑﾁ'],
    '두부': ['tofu', '豆腐'],
    '치즈': ['cheese', '치이즈'],
    '요거트': ['yogurt', '요구르트', 'ヨーグルト'],
    '아이스크림': ['ice cream', '아이스크림'],
    '과자': ['snack', '스낵'],
    '초콜릿': ['chocolate', '초콜렛', 'チョコレート'],
    '커피': ['coffee', '카페', 'コーヒー'],
    '차': ['tea', '티', '茶'],
    '쌀': ['rice', '米'],
}

# Reversed mapping for faster lookup
PRODUCT_VARIANTS = {}
for canonical, variants in COMMON_PRODUCTS.items():
    for variant in variants:
        PRODUCT_VARIANTS[variant.lower()] = canonical
    PRODUCT_VARIANTS[canonical.lower()] = canonical

# Common OCR errors in Korean/English mixed text
OCR_CORRECTIONS = {
    # Number confusions
    'О': '0', 'о': '0', 'O': '0',  # Letter O to zero
    'І': '1', 'і': '1', 'l': '1',  # Letter I/l to one
    'ㅇ': '0', 'ㅣ': '1',  # Korean characters
    
    # Korean character confusions
    '둬': '돼', '쥬': '주', '툐': '퇴',
    
    # Brand name fixes
    '롯데': 'LOTTE', '삼성': 'SAMSUNG', '엘지': 'LG',
    'CJ': 'CJ', '농심': '농심', '오뚜기': '오뚜기',
}

# Noise words to remove from product names
NOISE_WORDS = {
    'korean': ['개', '봉', '팩', '입', '병', '캔', '박스', 'box', 'pack', 'ea', 'pcs'],
    'measurement': ['g', 'kg', 'ml', 'l', 'oz', 'lb', '그램', '킬로', '리터'],
    'quality': ['신선', '프리미엄', 'premium', 'fresh', 'organic', '유기농'],
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
        return canonical, 15.0  # Boost confidence for known products
    
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
            return best_match, confidence_boost
    
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
    name = re.sub(r'^[^\w가-힣]+|[^\w가-힣]+$', '', name)
    
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
    
    # Korean major retailers
    retailers = {
        'emart': ['이마트', 'emart', 'e-mart'],
        'homeplus': ['홈플러스', 'homeplus'],
        'lotte': ['롯데', 'lotte', '롯데마트'],
        'gs25': ['gs25', 'gs 25', '지에스25'],
        'cu': ['cu', '씨유', 'cvs'],
        '7eleven': ['세븐일레븐', '7-eleven', '7eleven'],
        'coupang': ['쿠팡', 'coupang'],
        'market_kurly': ['마켓컬리', 'kurly'],
    }
    
    for retailer_type, keywords in retailers.items():
        if any(keyword in text_lower for keyword in keywords):
            logger.info(f"Receipt type detected: {retailer_type}")
            return retailer_type
    
    # Determine by content
    if any(word in text_lower for word in ['편의점', 'convenience', '24시간']):
        return 'convenience_store'
    elif any(word in text_lower for word in ['마트', 'mart', 'supermarket', '슈퍼']):
        return 'supermarket'
    elif any(word in text_lower for word in ['배달', 'delivery', '주문']):
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
            if re.search(r'[가-힣a-zA-Z]{2,}', line):
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
        'Dairy': ['우유', 'milk', '치즈', 'cheese', '요거트', 'yogurt', '버터', 'butter', 'cream'],
        'Meat': ['고기', '돼지', '소고기', '닭', 'pork', 'beef', 'chicken', 'meat', 'ham'],
        'Produce': ['사과', '바나나', '토마토', '양파', '감자', '당근', '배추', 'apple', 'banana', 
                    'tomato', 'onion', 'potato', 'carrot', 'lettuce', 'fruit', '과일', '채소'],
        'Bakery': ['빵', 'bread', '케이크', 'cake', '도넛', 'donut', 'bagel', 'muffin'],
        'Frozen': ['아이스크림', 'ice cream', '냉동', 'frozen'],
        'Beverages': ['물', '음료', '주스', '콜라', '사이다', '맥주', '소주', 'water', 'juice', 
                      'cola', 'beer', 'soju', 'coffee', '커피', 'tea', '차'],
        'Snacks': ['과자', '스낵', '초콜릿', 'snack', 'chocolate', 'chip', 'candy', '사탕'],
        'Pantry': ['라면', '쌀', 'ramen', 'rice', 'pasta', '통조림', 'can', 'noodle'],
    }
    
    for category, keywords in category_keywords.items():
        if any(keyword in name_lower for keyword in keywords):
            return category
    
    return 'Other'
