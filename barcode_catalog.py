"""
Offline barcode lookup against a small bundled catalog.

There is no online product database behind the barcode page. Lookups resolve
against the table below, which uses UPC-A codes starting with "2". GS1 reserves
that prefix for store-internal and random-weight items, so these codes can
never collide with a real manufacturer's product. Anything not in the table is
reported as not found and the user types the details in by hand.

Swapping this module for an Open Food Facts client is the intended upgrade
path; the API response shape (found, name, category, source) stays the same.
"""
from typing import Optional

SOURCE = "local catalog"

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
