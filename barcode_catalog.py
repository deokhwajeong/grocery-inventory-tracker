"""
Barcode lookup: a small bundled offline catalog, plus an optional online
lookup on Open Food Facts.

The offline table below uses UPC-A codes starting with "2". GS1 reserves that
prefix for store-internal and random-weight items, so these codes can never
collide with a real manufacturer's product.

lookup_online() asks the public Open Food Facts API (openfoodfacts.org, open
data under the ODbL) for real product codes. It is only used when the app is
started with BARCODE_ONLINE_LOOKUP=true. It has a short timeout and returns
None on any network or data problem, so the page falls back to manual entry
and the app keeps working offline.
"""
import json
import logging
import urllib.error
import urllib.request
from functools import lru_cache
from typing import Optional

logger = logging.getLogger(__name__)

SOURCE = "local catalog"
ONLINE_SOURCE = "Open Food Facts"
OFF_URL = "https://world.openfoodfacts.org/api/v2/product/{code}.json?fields=product_name,brands,categories_tags"
USER_AGENT = "GroceryInventoryTracker/1.0 (+https://github.com/deokhwajeong/grocery-inventory-tracker)"

# (first 11 digits, product name, category). The check digit is computed.
_ENTRIES = [
    ("20000000001", "Whole Milk", "Dairy"),
    ("20000000002", "Greek Yogurt", "Dairy"),
    ("20000000003", "Cheddar Cheese", "Dairy"),
    ("20000000004", "Large Eggs", "Dairy"),
    ("20000000005", "Unsalted Butter", "Dairy"),
    ("20000000011", "Chicken Breast", "Meat"),
    ("20000000012", "Ground Turkey", "Meat"),
    ("20000000021", "Bananas", "Produce"),
    ("20000000022", "Baby Spinach", "Produce"),
    ("20000000023", "Broccoli", "Produce"),
    ("20000000031", "Sourdough Bread", "Bakery"),
    ("20000000032", "Whole Wheat Bread", "Bakery"),
    ("20000000041", "Frozen Peas", "Frozen"),
    ("20000000051", "Basmati Rice", "Pantry"),
    ("20000000052", "Spaghetti", "Pantry"),
    ("20000000053", "Crushed Tomatoes", "Pantry"),
    ("20000000061", "Orange Juice", "Beverages"),
    ("20000000062", "Ground Coffee", "Beverages"),
    ("20000000071", "Granola Bars", "Snacks"),
    ("20000000072", "Hummus", "Snacks"),
]

VALID_LENGTHS = (8, 12, 13, 14)


def gs1_check_digit(body: str) -> int:
    """GS1 mod-10 check digit for the digits before the check digit."""
    total = sum(int(d) * (3 if i % 2 == 0 else 1) for i, d in enumerate(reversed(body)))
    return (10 - total % 10) % 10


def is_valid_gtin(code: str) -> bool:
    """True for an 8, 12, 13 or 14 digit code with a correct check digit."""
    return code.isdigit() and len(code) in VALID_LENGTHS and gs1_check_digit(code[:-1]) == int(code[-1])


def _key(code: str) -> str:
    # UPC-A, EAN-13 and GTIN-14 forms of the same product differ only by leading zeros
    return code.lstrip("0")


CATALOG = {}
for _body, _name, _category in _ENTRIES:
    _code = _body + str(gs1_check_digit(_body))
    CATALOG[_key(_code)] = {"barcode": _code, "name": _name, "category": _category}


def lookup(code: str) -> Optional[dict]:
    """Return {'barcode', 'name', 'category'} for a known code, otherwise None."""
    return CATALOG.get(_key(code))


def sample_codes(limit: int = 4) -> list:
    """A few catalog entries to show on the barcode page so the lookup can be tried."""
    return list(CATALOG.values())[:limit]


# Open Food Facts category tags -> app categories (first match wins).
OFF_CATEGORY_MAP = [
    ("frozen", "Frozen"), ("ice-cream", "Frozen"),
    ("dairies", "Dairy"), ("dairy", "Dairy"), ("milks", "Dairy"), ("cheeses", "Dairy"), ("yogurts", "Dairy"),
    ("eggs", "Dairy"), ("butters", "Dairy"),
    ("meats", "Meat"), ("poultry", "Meat"), ("seafood", "Meat"), ("fishes", "Meat"), ("sausages", "Meat"),
    ("fruits", "Produce"), ("vegetables", "Produce"), ("fresh-", "Produce"),
    ("breads", "Bakery"), ("pastries", "Bakery"), ("viennoiseries", "Bakery"), ("cakes", "Bakery"),
    ("beverages", "Beverages"), ("drinks", "Beverages"), ("waters", "Beverages"), ("juices", "Beverages"),
    ("coffees", "Beverages"), ("teas", "Beverages"), ("sodas", "Beverages"),
    ("snacks", "Snacks"), ("sweets", "Snacks"), ("chocolates", "Snacks"), ("biscuits", "Snacks"), ("chips", "Snacks"),
    ("cereals", "Pantry"), ("pastas", "Pantry"), ("rices", "Pantry"), ("sauces", "Pantry"), ("condiments", "Pantry"),
    ("canned", "Pantry"), ("oils", "Pantry"), ("spreads", "Pantry"), ("groceries", "Pantry"),
]


def map_off_category(tags) -> str:
    for tag in tags or []:
        tag = tag.split(":", 1)[-1]
        for needle, category in OFF_CATEGORY_MAP:
            if needle in tag:
                return category
    return "Other"


@lru_cache(maxsize=256)
def lookup_online(code: str, timeout: float = 4.0) -> Optional[dict]:
    """
    Look a product up on Open Food Facts. Returns {'barcode', 'name', 'category'}
    or None when the product is unknown or the service cannot be reached.
    """
    if not is_valid_gtin(code):
        return None
    request = urllib.request.Request(OFF_URL.format(code=code), headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
        logger.warning(f"Open Food Facts lookup failed for {code}: {e}")
        return None
    product = data.get("product") if isinstance(data, dict) and data.get("status") == 1 else None
    name = (product or {}).get("product_name", "").strip()
    if not name:
        return None
    brand = (product.get("brands") or "").split(",")[0].strip()
    if brand and brand.lower() not in name.lower():
        name = f"{brand} {name}"
    return {"barcode": code, "name": name[:100], "category": map_off_category(product.get("categories_tags"))}
