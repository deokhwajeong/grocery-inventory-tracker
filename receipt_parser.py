"""
Turn receipt text (from OCR or typed in) into items, prices, a date and a type.

This module is pure text processing with no OpenCV or Tesseract dependency, so
it is fast to test and is what scripts/ocr_accuracy.py measures in text mode.

Layout types (see detect_receipt_type) and how each is read:

- supermarket: "NAME   4.99 F" per line. A "2 @ 1.99" line under an item sets
  its quantity; a "1.42 lb @ 0.69 /lb   0.98" line under a name-only line is
  a weighed item; "SAVINGS -1.00" lines become a discount on the item above.
- convenience: a QTY column in front of the name ("2  CHIPS   7.98").
- warehouse: an item number in front of the name ("512345 KS MILK 4.99 E").
  A "2 @ 5.80" line usually comes before the item it belongs to.
- online: the item name on its own line and "Qty 2 x $1.99   $3.98" below.

Quantity lines are attached by arithmetic, not by position alone: the line
"N @ unit" goes to whichever neighbouring item has a total of N x unit, which
copes with both orders and with OCR dropping a line.
"""
import re
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple

RECEIPT_TYPES = ("supermarket", "convenience", "warehouse", "online", "unknown")

# Korean chains (romanized) the app recognised before, mapped to a layout type.
KNOWN_CHAINS = {
    "supermarket": ["emart", "e-mart", "eemart", "homeplus", "home-plus", "lotte mart", "lottemart"],
    "convenience": ["gs25", "gs 25", "7-eleven", "7eleven", "ministop", "emart24"],
    "online": ["coupang", "kurly", "market kurly", "ssg.com"],
}

MONTHS = {m: i + 1 for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}
_MON = r"(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?"

# Lines containing these words are never items (word match, case-insensitive).
SKIP_WORDS = [
    "subtotal", "sub total", "sub-total", "total", "tax", "taxes", "vat", "change", "change due", "cash",
    "visa", "mastercard", "amex", "discover", "debit", "credit", "card", "balance", "tender", "tendered",
    "payment", "paid", "charged", "thank", "thanks", "welcome", "visit", "receipt", "cashier", "approval",
    "auth", "delivery fee", "service fee", "bag fee", "tip", "points", "rewards", "you saved", "total savings",
    "items sold", "item count", "terminal", "trans", "invoice", "survey", "return policy", "refund",
    # romanized Korean: receipt, total, subtotal, VAT, card, cash, thanks, payment
    "yeongsujeung", "hapgye", "sogye", "bugase", "kadeu", "hyeongeum", "gamsa", "gyeolje",
]
# Words that mark header lines. They only skip a line that has no price,
# because store-brand items ("STORE BRAND MILK 3.49") use some of them too.
HEADER_WORDS = [
    "store", "reg", "register", "lane", "member", "membership", "tel", "phone", "address", "order", "ordered",
    "delivered", "delivery", "date", "time", "qty item", "item amount", "description", "www", "http", ".com",
    "open", "hours", "manager",
]
ADDRESS_RE = re.compile(r"^\d+\s+.*\b(st|street|ave|avenue|rd|road|blvd|dr|drive|ln|lane|way|hwy)\b\.?", re.I)
DISCOUNT_WORDS = ["savings", "saving", "coupon", "discount", "promo", "instant savings", "member savings", "off", "sale"]

_PRICE = r"-?\$?\s?(?:\d{1,3}(?:,\d{3})+\.\d{2}|\d{1,5}[.,]\s?\d{2})"
PRICE_AT_END = re.compile(rf"(?P<price>{_PRICE})(?:\s*-)?\s*(?P<flag>[A-Z]{{1,2}}|\*)?\s*$")
QTY_AT = re.compile(rf"^\s*(?P<qty>\d{{1,3}})\s*(?:@|at|x|X|×)\s*(?P<unit>{_PRICE})\s*(?:/?\s*ea)?(?:\s+(?P<total>{_PRICE}))?\s*$", re.I)
WEIGHT_AT = re.compile(
    rf"^\s*(?P<w>\d+(?:[.,]\d+)?)\s*(?P<u>lb|lbs|kg|g)\s*@\s*(?P<unit>{_PRICE})\s*/\s*(?:lb|kg|g)\s*(?P<total>{_PRICE})?\s*[A-Z]?\s*$", re.I)
ONLINE_QTY = re.compile(
    rf"^\s*(?:qty|quantity)\s*:?\s*(?P<qty>\d{{1,3}})(?:\s*(?:x|×|@)\s*(?P<unit>{_PRICE}))?\s+(?P<total>{_PRICE})\s*$", re.I)
INLINE_QTY = [
    re.compile(r"^\s*(?P<qty>\d{1,3})\s*[xX×*]\s+(?=[A-Za-z])"),             # 2x Milk / 2 x Milk
    re.compile(r"\s+[xX×*]\s*(?P<qty>\d{1,3})\s*$"),                         # Milk x2
    re.compile(r"\s+(?P<qty>\d{1,3})\s*[xX×]\s*$"),                         # Milk 2x
    re.compile(r"\s+(?P<qty>\d{1,3})\s*(?:ea|EA|pcs|gae)\b\s*$"),           # Milk 2 EA
    re.compile(r"\s+(?P<qty>\d{1,3})\s*@\s*\$?\d+[.,]\d{2}\s*$"),           # Milk 2 @ 2.99
]
ITEM_CODE = re.compile(r"^\s*(?:\d{4,14}|[A-Z]?\d{5,})\s+(?=\S)")
QTY_COLUMN = re.compile(r"^\s*(?P<qty>\d{1,2})\s+(?=[A-Za-z])")


def _word_pattern(words):
    return re.compile(r"(?<![a-z])(" + "|".join(re.escape(w) for w in sorted(words, key=len, reverse=True)) + r")(?![a-z])", re.I)


SKIP_RE = _word_pattern(SKIP_WORDS)
HEADER_RE = _word_pattern(HEADER_WORDS)
DISCOUNT_RE = _word_pattern(DISCOUNT_WORDS)


def to_amount(text: Optional[str]) -> Optional[float]:
    """'$1,234.50' / '3,49' / '3. 49' -> float, or None."""
    if not text:
        return None
    t = text.replace("$", "").replace(" ", "")
    t = re.sub(r",(\d{2})$", r".\1", t)       # decimal comma
    t = t.replace(",", "")
    try:
        return round(float(t), 2)
    except ValueError:
        return None


# ---------------------------------------------------------------- dates

def _valid(year: int, month: int, day: int, today: date) -> Optional[str]:
    if year < 100:
        year += 2000
    try:
        d = date(year, month, day)
    except ValueError:
        return None
    if not (2000 <= d.year <= today.year + 1) or (d - today).days > 1:
        return None
    return d.isoformat()


def _date_candidates(line: str, today: date, day_first: bool):
    low = line.lower()
    for m in re.finditer(r"(?<!\d)(\d{4})\s*(?:nyeon|년)\s*(\d{1,2})\s*(?:wol|월)\s*(\d{1,2})\s*(?:il|일)?", low):
        yield _valid(int(m[1]), int(m[2]), int(m[3]), today)
    for m in re.finditer(r"(?<!\d)(\d{4})\s?[-/.]\s?(\d{1,2})\s?[-/.]\s?(\d{1,2})(?!\d)", low):
        yield _valid(int(m[1]), int(m[2]), int(m[3]), today)
    for m in re.finditer(r"(?<![\d.])(\d{1,2})\.(\d{1,2})\.(\d{4}|\d{2})(?![\d.])", low):
        yield _valid(int(m[3]), int(m[2]), int(m[1]), today)        # dotted: day.month.year
    for m in re.finditer(r"(?<![\d/-])(\d{1,2})[/-](\d{1,2})[/-](\d{4}|\d{2})(?![\d/-])", low):
        a, b, y = int(m[1]), int(m[2]), int(m[3])
        if a > 12 or (day_first and b <= 12):
            a, b = b, a
        yield _valid(y, a, b, today)
    for m in re.finditer(rf"(?<![a-z]){_MON}\s+(\d{{1,2}})(?:st|nd|rd|th)?,?\s+(\d{{4}})", low):
        yield _valid(int(m[3]), MONTHS[m[1][:3]], int(m[2]), today)
    for m in re.finditer(rf"(?<!\d)(\d{{1,2}})(?:st|nd|rd|th)?\s+{_MON},?\s+(\d{{4}})", low):
        yield _valid(int(m[3]), MONTHS[m[2][:3]], int(m[1]), today)


def find_receipt_date(text: str, day_first: bool = False, today: Optional[date] = None) -> Optional[str]:
    """
    Return the purchase date as YYYY-MM-DD, or None if no plausible date is found.

    Supports YYYY-MM-DD, YYYY/MM/DD, YYYY.MM.DD, MM/DD/YYYY, MM/DD/YY,
    DD.MM.YYYY, "Jan 15, 2026", "15 Jan 2026" and the Korean "2026nyeon 1wol
    15il" form. Slash dates are read month first (US receipts) unless the first
    number is above 12 or ``day_first`` is set. Lines with a date keyword or a
    time are preferred, and dates in the future or before 2000 are ignored.
    """
    today = today or date.today()
    lines = text.splitlines()
    keyed = [ln for ln in lines if re.search(r"date|delivered|ordered|purchased|\d{1,2}:\d{2}|nyeon", ln, re.I)]
    for group in (keyed, lines):
        for line in group:
            for found in _date_candidates(line, today, day_first):
                if found:
                    return found
    return None


# ---------------------------------------------------------------- type detection

def detect_receipt_type(text: str) -> str:
    """Classify the receipt layout: supermarket, convenience, warehouse, online or unknown."""
    low = text.lower()
    for kind, names in KNOWN_CHAINS.items():
        if any(re.search(r"(?<![a-z0-9])" + re.escape(n) + r"(?![a-z0-9])", low) for n in names):
            return kind
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    priced = [ln for ln in lines if PRICE_AT_END.search(ln) and not SKIP_RE.search(ln)]
    score = dict.fromkeys(RECEIPT_TYPES[:-1], 0.0)

    if re.search(r"order\s*(#|no|number)|delivered|delivery|shipped|qty\s*:?\s*\d", low):
        score["online"] += 2
    score["online"] += 1.5 * sum(bool(ONLINE_QTY.match(ln)) for ln in lines)

    if re.search(r"wholesale|warehouse|member(ship)?\s*(#|no)?\s*\d|club", low):
        score["warehouse"] += 2
    score["warehouse"] += 1.0 * sum(bool(re.match(r"\d{5,8}\s+[A-Za-z]", ln)) for ln in priced)

    if re.search(r"convenience|24\s*h(ou)?rs?|pyeonuijeom|\bqty\s+item|food\s*mart|gas", low):
        score["convenience"] += 2
    score["convenience"] += 1.0 * sum(bool(re.match(r"\d{1,2}\s+[A-Za-z]", ln)) for ln in priced)

    if re.search(r"market|grocery|supermarket|foods|syupeo|mateu", low):
        score["supermarket"] += 2
    score["supermarket"] += 1.0 * sum(bool(QTY_AT.match(ln) or WEIGHT_AT.match(ln)) for ln in lines)
    score["supermarket"] += 0.5 * sum(bool(re.search(r"\d[.,]\d{2}\s*[A-Z]\s*$", ln)) for ln in priced)
    if priced and not any(score.values()):
        score["supermarket"] = 0.5

    best = max(score, key=score.get)
    return best if score[best] > 0 else "unknown"


# ---------------------------------------------------------------- item lines

def _clean_name(name: str) -> str:
    # OCR often reads the letter O as zero inside words ("0J", "C0LA"); sizes like "20OZ" are left alone.
    name = re.sub(r"\b0(?=[A-Za-z])|(?<=[A-Za-z])0", "O", name)
    name = re.sub(r"[^\w\s%&'/-]", " ", name)
    name = re.sub(r"\s+", " ", name).strip(" -/'")
    return name


def _new_item(name: str, quantity: int, price: Optional[float], unit: Optional[float] = None, weight=None) -> Dict:
    item = {"name": name, "quantity": quantity, "price": None if price is None else f"{price:.2f}"}
    if unit is not None:
        item["unit_price"] = f"{unit:.2f}"
    elif price is not None and quantity:
        item["unit_price"] = f"{price / quantity:.2f}"
    if weight:
        item["weight"] = weight
    return item


def _close(a: Optional[float], b: Optional[float]) -> bool:
    return a is not None and b is not None and abs(a - b) <= 0.02


def _split_item_line(line: str, receipt_type: str) -> Optional[Tuple[str, int, float]]:
    """'2  CHIPS  7.98 F' -> ('CHIPS', 2, 7.98). None if the line has no usable name."""
    m = PRICE_AT_END.search(line)
    price = to_amount(m.group("price"))
    name = line[:m.start()].rstrip(" .:$")
    qty = 1
    name = ITEM_CODE.sub("", name)
    col = QTY_COLUMN.match(name)
    if col and (receipt_type == "convenience" or receipt_type == "unknown") and 1 <= int(col["qty"]) <= 20:
        qty, name = int(col["qty"]), name[col.end():]
    for pattern in INLINE_QTY:
        q = pattern.search(name)
        if q:
            qty = int(q["qty"]) or 1
            name = name[:q.start()] + name[q.end():]
            break
    name = _clean_name(name)
    if len(re.sub(r"[^A-Za-z]", "", name)) < 2:
        return None
    return name, max(1, min(qty, 100)), price


def parse_receipt_items(text: str, receipt_type: Optional[str] = None) -> List[Dict]:
    """Extract item dicts (name, quantity, price, unit_price, optional discount/weight) in receipt order."""
    receipt_type = receipt_type or detect_receipt_type(text)
    items: List[Dict] = []
    pending_name: Optional[str] = None     # name-only line waiting for its qty / weight line
    pending_qty: Optional[Tuple[int, float]] = None  # "N @ unit" seen before its item (warehouse)

    for raw in text.splitlines():
        line = raw.strip()
        if len(line) < 2:
            continue

        w = WEIGHT_AT.match(line)
        if w:
            total = to_amount(w["total"]) or round(float(w["w"].replace(",", ".")) * to_amount(w["unit"]), 2)
            if pending_name:
                items.append(_new_item(pending_name, 1, total, to_amount(w["unit"]), f"{w['w']} {w['u'].lower()}"))
                pending_name = None
            continue

        o = ONLINE_QTY.match(line)
        if o:
            qty, total = int(o["qty"]), to_amount(o["total"])
            if pending_name:
                items.append(_new_item(pending_name, qty, total, to_amount(o["unit"])))
                pending_name = None
            elif items and items[-1]["price"] is None:
                items[-1].update(_new_item(items[-1]["name"], qty, total, to_amount(o["unit"])))
            continue

        q = QTY_AT.match(line)
        if q:
            qty, unit = int(q["qty"]), to_amount(q["unit"])
            total = to_amount(q["total"]) or round(qty * unit, 2)
            last = items[-1] if items else None
            if pending_name:
                items.append(_new_item(pending_name, qty, total, unit))
                pending_name = None
            elif last and last["quantity"] == 1 and _close(to_amount(last["price"]), total):
                last["quantity"], last["unit_price"] = qty, f"{unit:.2f}"
            else:
                pending_qty = (qty, unit)
            continue

        if find_receipt_date(line):
            pending_name = None
            continue
        has_price = bool(PRICE_AT_END.search(line))
        if SKIP_RE.search(line):
            pending_name = None
            continue
        if has_price and DISCOUNT_RE.search(line) or re.match(r"^-\s?\$?\d", line):
            amount = to_amount(PRICE_AT_END.search(line).group("price")) if has_price else None
            if items and amount is not None:
                previous = to_amount(items[-1].get("discount")) or 0.0
                items[-1]["discount"] = f"{previous + abs(amount):.2f}"
            continue
        if not has_price:
            if HEADER_RE.search(line) or ADDRESS_RE.match(line) or re.search(r"\d{3}[-. ]\d{3,4}[-. ]\d{4}", line):
                pending_name = None
                continue
            letters = re.sub(r"[^A-Za-z]", "", line)
            if len(letters) >= 3 and not re.fullmatch(r"[\d\s\W]+", line):
                pending_name = _clean_name(ITEM_CODE.sub("", line))
            continue

        parts = _split_item_line(line, receipt_type)
        pending_name = None
        if not parts:
            continue
        name, qty, price = parts
        if price is not None and price < 0:
            continue
        unit = None
        if pending_qty and qty == 1 and (_close(price, pending_qty[0] * pending_qty[1]) or receipt_type == "warehouse"):
            qty, unit = pending_qty
        pending_qty = None
        items.append(_new_item(name, qty, price, unit))

    return [it for it in items if it["price"] is not None or it["quantity"] > 1]


def calculate_confidence(item: Dict) -> float:
    """Heuristic confidence (0-100) for a parsed item."""
    score = 45.0
    name = item.get("name", "")
    if len(name) >= 3:
        score += 10
    if len(name) >= 5:
        score += 5
    if re.fullmatch(r"[A-Za-z][A-Za-z0-9 %&'/-]*", name):
        score += 10
    if item.get("price") is not None:
        score += 15
    qty = item.get("quantity", 1)
    if 1 <= qty <= 10:
        score += 10
    elif qty > 100:
        score -= 20
    return min(max(score, 0.0), 100.0)


def today_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d")
