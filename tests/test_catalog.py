"""Product name normalization against the curated catalog (#1)."""
import pytest

import product_catalog
from ocr_advanced import get_category_suggestion, normalize_product_name


def test_catalog_has_500_plus_distinct_products_in_every_category():
    assert len(product_catalog.PRODUCTS) >= 500
    counts = product_catalog.stats()
    assert set(counts) == {"Dairy", "Meat", "Produce", "Bakery", "Frozen", "Pantry", "Beverages", "Snacks", "Other"}
    assert all(n >= 30 for n in counts.values())


def test_every_canonical_name_maps_to_itself():
    for canonical in product_catalog.PRODUCTS:
        assert product_catalog.LOOKUP[product_catalog._key(canonical)] == canonical, canonical


@pytest.mark.parametrize("raw, expected", [
    ("COCA COLA", "Coca-Cola"), ("Coca-Cola", "Coca-Cola"), ("coke", "Coca-Cola"), ("DIET COKE", "Diet Cola"),
    ("ORG BNNA", "Bananas"), ("BANANA", "Bananas"),
    ("GRND BEEF 80/20", "Ground Beef"), ("KS WHL MLK 1GAL", "Whole Milk"),
    ("BNLS SKLS CHKN BRST", "Chicken Breast"), ("CHKN BRST", "Chicken Breast"),
    ("GV HVY CRM", "Heavy Cream"), ("STRAWB", "Strawberries"), ("STRWBRY 1LB", "Strawberries"),
    ("SHRD MOZZ CHS", "Mozzarella Cheese"), ("BTL WTR 24PK", "Bottled Water"),
    ("OJ", "Orange Juice"), ("EVOO", "Olive Oil"), ("PB CRUNCHY", "Peanut Butter"),
    ("PPR TWL", "Paper Towels"), ("EGGS DOZEN LG", "Large Eggs"),
    ("123456 FRZN PEAS", "Frozen Peas"), ("HONEYCRSP APL", "Honeycrisp Apples"),
    ("sweet italian sausage", "Italian Sausage"), ("mac n cheese", "Macaroni and Cheese"),
    # romanized Korean names the app already understood
    ("uyu", "Milk"), ("gyeran", "Egg"), ("ramyeon", "Ramen"), ("baechu", "Napa Cabbage"), ("dubu", "Tofu"),
    # light OCR damage, caught by fuzzy matching
    ("Brocolli", "Broccoli"), ("Spinnach", "Spinach"),
])
def test_receipt_names_normalize_to_catalog_products(raw, expected):
    assert normalize_product_name(raw)[0] == expected


def test_known_products_get_a_confidence_boost_and_unknown_names_are_cleaned():
    name, boost = normalize_product_name("GRND BEEF")
    assert name == "Ground Beef" and boost > 10
    name, boost = normalize_product_name("ZZYZX GADGET 12OZ")
    assert name == "Zzyzx Gadget" and boost == 0


def test_names_are_not_corrupted():
    assert normalize_product_name("Olive Oil")[0] == "Olive Oil"
    assert normalize_product_name("milk")[0] == "Milk"
    assert normalize_product_name("")[0] == ""
    assert normalize_product_name("Mоzzarella")[0] == "Mozzarella Cheese"   # Cyrillic "о" from OCR


@pytest.mark.parametrize("name, category", [
    ("Whole Milk", "Dairy"), ("Chicken Breast", "Meat"), ("Bananas", "Produce"), ("Orange Juice", "Beverages"),
    ("Basmati Rice", "Pantry"), ("Eggplant", "Produce"), ("Tater Tots", "Frozen"), ("Dish Soap", "Other"),
    ("Pretzels", "Snacks"), ("Naan", "Bakery"),
    ("Vegan Cheese Slices", "Dairy"),     # not in the catalog: keyword fallback
    ("Mystery Thing", "Other"),
])
def test_category_suggestion(name, category):
    assert get_category_suggestion(name) == category


def test_match_product_without_fuzzy_matching():
    assert product_catalog.match_product("Brocolli") == (None, 0.0)
    assert product_catalog.match_product("") == (None, 0.0)
    assert product_catalog.category_for("Bagels") == "Bakery"
    assert product_catalog.category_for("unobtainium") is None
