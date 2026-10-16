#!/usr/bin/env python3
"""
Generate a synthetic receipt dataset with ground truth for OCR accuracy tests.

Real receipts cannot be committed (they carry card digits, store locations and
shopping habits), so this script prints fictional receipts instead. Every
receipt is produced from a fixed random seed, which makes the dataset
reproducible: the same seed always gives the same text, the same ground truth
and (with the same fonts installed) the same images.

Four receipt layouts are generated, one per receipt type the parser knows:

- supermarket: one item per line, "2 @ 1.99" quantity lines under the item,
  weighed produce ("1.42 lb @ 0.69 /lb"), savings lines, tax flags
- convenience: a QTY column in front of each item
- warehouse: a 6 digit item number in front of each item, short names
- online: a delivery order summary, item name on one line and
  "Qty 2 x $1.99   $3.98" on the next

Dates use one of seven formats (MM/DD/YYYY, MM/DD/YY, YYYY-MM-DD,
DD.MM.YYYY, YYYY.MM.DD, "Jan 15, 2026", "15 JAN 2026"). Item names are
printed the way tills print them: upper case, often abbreviated with the
generator's own shorthand table below. The ground truth always holds the plain
product name, so name accuracy measures how well the normalizer undoes this.

Images get a slight rotation, paper tint, sensor noise and blur so the OCR
step sees something closer to a phone photo than a clean render.

Usage:
    python scripts/receipt_dataset.py                    # 60 receipts into datasets/receipts/
    python scripts/receipt_dataset.py --count 20 --seed 7 --out /tmp/receipts
    python scripts/receipt_dataset.py --no-images        # ground truth only
"""
import argparse
import json
import os
import random
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT = os.path.join(ROOT, "datasets", "receipts")
DEFAULT_SEED = 50
DEFAULT_COUNT = 60

RECEIPT_TYPES = ["supermarket", "convenience", "warehouse", "online"]

# (product name, category, typical unit price, sold by weight)
PRODUCTS = [
    ("Whole Milk", "Dairy", 3.79, False), ("Skim Milk", "Dairy", 3.49, False),
    ("Oat Milk", "Dairy", 4.49, False), ("Greek Yogurt", "Dairy", 1.29, False),
    ("Cheddar Cheese", "Dairy", 4.29, False), ("Mozzarella Cheese", "Dairy", 3.99, False),
    ("Cream Cheese", "Dairy", 2.79, False), ("Unsalted Butter", "Dairy", 4.99, False),
    ("Large Eggs", "Dairy", 3.59, False), ("Sour Cream", "Dairy", 2.29, False),
    ("Heavy Cream", "Dairy", 3.89, False), ("Cottage Cheese", "Dairy", 3.49, False),
    ("Chicken Breast", "Meat", 8.99, False), ("Chicken Thighs", "Meat", 6.49, False),
    ("Ground Beef", "Meat", 6.99, False), ("Ground Turkey", "Meat", 5.99, False),
    ("Pork Chops", "Meat", 7.49, False), ("Bacon", "Meat", 6.29, False),
    ("Salmon Fillet", "Meat", 11.99, False), ("Sliced Turkey", "Meat", 4.99, False),
    ("Bananas", "Produce", 0.69, True), ("Apples", "Produce", 1.99, True),
    ("Honeycrisp Apples", "Produce", 2.49, True), ("Avocados", "Produce", 1.25, False),
    ("Baby Spinach", "Produce", 3.99, False), ("Romaine Lettuce", "Produce", 2.49, False),
    ("Broccoli", "Produce", 1.89, True), ("Carrots", "Produce", 1.49, False),
    ("Yellow Onions", "Produce", 1.19, True), ("Russet Potatoes", "Produce", 0.99, True),
    ("Tomatoes", "Produce", 2.29, True), ("Strawberries", "Produce", 3.99, False),
    ("Blueberries", "Produce", 4.49, False), ("Lemons", "Produce", 0.79, False),
    ("Limes", "Produce", 0.50, False), ("Cucumber", "Produce", 0.89, False),
    ("Red Bell Pepper", "Produce", 1.49, False), ("Garlic", "Produce", 0.75, False),
    ("Sweet Potatoes", "Produce", 1.29, True), ("Grapes", "Produce", 2.99, True),
    ("Sourdough Bread", "Bakery", 4.49, False), ("Whole Wheat Bread", "Bakery", 3.29, False),
    ("Bagels", "Bakery", 3.99, False), ("Flour Tortillas", "Bakery", 2.99, False),
    ("Croissants", "Bakery", 4.99, False), ("English Muffins", "Bakery", 2.79, False),
    ("Frozen Peas", "Frozen", 1.99, False), ("Frozen Pizza", "Frozen", 5.99, False),
    ("Vanilla Ice Cream", "Frozen", 4.99, False), ("Frozen Blueberries", "Frozen", 3.99, False),
    ("Fish Sticks", "Frozen", 4.49, False), ("Frozen Waffles", "Frozen", 2.99, False),
    ("Basmati Rice", "Pantry", 4.99, False), ("Spaghetti", "Pantry", 1.49, False),
    ("Penne Pasta", "Pantry", 1.49, False), ("Crushed Tomatoes", "Pantry", 1.79, False),
    ("Peanut Butter", "Pantry", 3.49, False), ("Olive Oil", "Pantry", 8.99, False),
    ("Black Beans", "Pantry", 1.09, False), ("Chicken Broth", "Pantry", 2.49, False),
    ("Rolled Oats", "Pantry", 3.99, False), ("Honey", "Pantry", 6.49, False),
    ("All Purpose Flour", "Pantry", 3.29, False), ("Granulated Sugar", "Pantry", 3.19, False),
    ("Tuna", "Pantry", 1.39, False), ("Ketchup", "Pantry", 2.99, False),
    ("Orange Juice", "Beverages", 3.49, False), ("Apple Juice", "Beverages", 2.99, False),
    ("Ground Coffee", "Beverages", 9.99, False), ("Green Tea", "Beverages", 3.99, False),
    ("Sparkling Water", "Beverages", 4.99, False), ("Bottled Water", "Beverages", 5.49, False),
    ("Cola", "Beverages", 2.29, False), ("Lemonade", "Beverages", 2.99, False),
    ("Potato Chips", "Snacks", 3.99, False), ("Tortilla Chips", "Snacks", 3.49, False),
    ("Granola Bars", "Snacks", 3.99, False), ("Dark Chocolate", "Snacks", 2.99, False),
    ("Pretzels", "Snacks", 2.79, False), ("Hummus", "Snacks", 3.99, False),
    ("Popcorn", "Snacks", 3.29, False), ("Almonds", "Snacks", 6.99, False),
    ("Paper Towels", "Other", 7.99, False), ("Dish Soap", "Other", 3.49, False),
]

# Shorthand used on till receipts. This table belongs to the generator only.
SHORTHAND = {
    "whole": "WHL", "milk": "MLK", "greek": "GRK", "yogurt": "YOGRT", "cheddar": "CHDR",
    "cheese": "CHS", "mozzarella": "MOZZ", "unsalted": "UNSLT", "butter": "BTR",
    "large": "LG", "chicken": "CHKN", "breast": "BRST", "thighs": "THGH", "ground": "GRND",
    "turkey": "TRKY", "salmon": "SLMN", "fillet": "FLT", "bananas": "BNNA", "honeycrisp": "HNYCRSP",
    "apples": "APPL", "avocados": "AVOCADO", "spinach": "SPNCH", "romaine": "ROMAINE",
    "lettuce": "LTTC", "broccoli": "BROC", "carrots": "CARROT", "yellow": "YLW", "onions": "ONION",
    "potatoes": "POTATO", "strawberries": "STRAWB", "blueberries": "BLUEB", "sourdough": "SRDGH",
    "bread": "BRD", "wheat": "WHT", "frozen": "FRZN", "vanilla": "VAN", "ice": "ICE", "cream": "CRM",
    "basmati": "BSMTI", "rice": "RICE", "crushed": "CRSHD", "tomatoes": "TOM", "orange": "OJ",
    "juice": "JCE", "coffee": "COFFEE", "granola": "GRNLA", "bars": "BAR", "peanut": "PNT",
    "olive": "OLV", "oil": "OIL", "sparkling": "SPRKL", "water": "WTR", "chocolate": "CHOC",
    "tortilla": "TORT", "chips": "CHP", "potato": "POT", "sweet": "SWT", "pasta": "PSTA",
    "beans": "BNS", "broth": "BRTH", "rolled": "RLD", "oats": "OATS", "purpose": "PURP",
    "flour": "FLR", "granulated": "GRAN", "sugar": "SUGAR", "paper": "PPR", "towels": "TWL",
    "dish": "DSH", "soap": "SOAP", "bottled": "BTL", "pretzels": "PRTZL", "croissants": "CRSNT",
    "english": "ENG", "muffins": "MUFFIN", "waffles": "WAFFLE", "sliced": "SLCD", "pork": "PORK",
    "chops": "CHOP", "cottage": "CTTG", "heavy": "HVY", "sour": "SOUR", "skim": "SKIM",
}

BRANDLESS_PREFIX = {"warehouse": ["KS", "KS ORG", "KIRK"], "supermarket": ["ORG", "GV", "STORE"]}

STORES = {
    "supermarket": ["GREENLEAF MARKET", "VALLEY FRESH GROCERY", "HARVEST FOODS SUPERMARKET", "MAPLE STREET MARKET"],
    "convenience": ["QUICKSTOP #2214", "CORNER MART 24HR", "EZ STOP CONVENIENCE", "DAILY GO #118"],
    "warehouse": ["BULKWAY WHOLESALE", "PANTRY CLUB WAREHOUSE", "MEGABULK DEPOT"],
    "online": ["FRESHCART DELIVERY", "BASKETBOX ONLINE", "DOORSTEP GROCER"],
}

DATE_FORMATS = ["mdy_slash", "mdy_short", "iso", "dmy_dot", "ymd_dot", "mon_d_y", "d_mon_y"]
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/freefont/FreeMono.ttf",
]


def format_date(d, kind):
    if kind == "mdy_slash":
        return d.strftime("%m/%d/%Y")
    if kind == "mdy_short":
        return d.strftime("%m/%d/%y")
    if kind == "iso":
        return d.isoformat()
    if kind == "dmy_dot":
        return d.strftime("%d.%m.%Y")
    if kind == "ymd_dot":
        return d.strftime("%Y.%m.%d")
    if kind == "mon_d_y":
        return f"{MONTHS[d.month - 1].title()} {d.day}, {d.year}"
    return f"{d.day:02d} {MONTHS[d.month - 1]} {d.year}"


def printed_name(rng, name, receipt_type):
    """How a till would print this product name."""
    if receipt_type == "online":
        return name  # order summaries use the catalogue name
    words = name.split()
    style = rng.random()
    if style < 0.35:
        out = [w.upper() for w in words]
    elif style < 0.8:
        out = [SHORTHAND.get(w.lower(), w.upper()) if rng.random() < 0.8 else w.upper() for w in words]
    else:
        out = [SHORTHAND.get(w.lower(), w.upper()) for w in words]
    if receipt_type in BRANDLESS_PREFIX and rng.random() < 0.25:
        out.insert(0, rng.choice(BRANDLESS_PREFIX[receipt_type]))
    text = " ".join(out)
    return text[:22] if receipt_type == "warehouse" else text


def money(x):
    return f"{x:.2f}"


def pick_items(rng, receipt_type):
    n = {"convenience": rng.randint(2, 5), "online": rng.randint(4, 9)}.get(receipt_type, rng.randint(5, 11))
    chosen = rng.sample(PRODUCTS, n)
    items = []
    for name, category, base, by_weight in chosen:
        unit = round(base * rng.uniform(0.85, 1.2), 2)
        qty, weight = 1, None
        if by_weight and receipt_type == "supermarket" and rng.random() < 0.6:
            weight = round(rng.uniform(0.6, 3.2), 2)
            total = round(weight * unit, 2)
        else:
            qty = rng.choice([1, 1, 1, 1, 2, 2, 3, 4]) if receipt_type != "warehouse" else rng.choice([1, 1, 2])
            total = round(qty * unit, 2)
        items.append({
            "name": name, "category": category, "printed": printed_name(rng, name, receipt_type),
            "quantity": qty, "unit_price": unit, "price": total, "weight_lb": weight,
        })
    return items


def pad_line(left, right, width):
    gap = max(2, width - len(left) - len(right))
    return f"{left}{' ' * gap}{right}"


def build_supermarket(rng, items, store, when, date_kind, width):
    lines = [store, f"{rng.randint(100, 9999)} {rng.choice(['MAIN ST', 'OAK AVE', 'PINE RD', 'ELM BLVD'])}",
             f"TEL 555-{rng.randint(100, 999)}-{rng.randint(1000, 9999)}",
             f"{format_date(when, date_kind)}  {rng.randint(7, 21):02d}:{rng.randint(0, 59):02d}", ""]
    savings = 0.0
    for it in items:
        flag = rng.choice(["", "", " F", " T"])
        if it["weight_lb"]:
            lines.append(it["printed"])
            lines.append(pad_line(f"  {it['weight_lb']:.2f} lb @ {money(it['unit_price'])} /lb", money(it["price"]) + flag, width))
        elif it["quantity"] > 1:
            lines.append(pad_line(it["printed"], money(it["price"]) + flag, width))
            lines.append(f"  {it['quantity']} @ {money(it['unit_price'])}")
        else:
            lines.append(pad_line(it["printed"], money(it["price"]) + flag, width))
        if rng.random() < 0.15:
            off = round(min(it["price"] * 0.2, rng.choice([0.5, 1.0, 1.5])), 2)
            savings += off
            lines.append(pad_line("  SAVINGS", f"-{money(off)}", width))
    return lines, savings


def build_convenience(rng, items, store, when, date_kind, width):
    lines = [store, f"STORE {rng.randint(1000, 9999)}  REG {rng.randint(1, 4)}",
             f"DATE {format_date(when, date_kind)} TIME {rng.randint(0, 23):02d}:{rng.randint(0, 59):02d}", "",
             pad_line("QTY ITEM", "AMOUNT", width)]
    for it in items:
        lines.append(pad_line(f"{it['quantity']}  {it['printed']}", money(it["price"]), width))
    return lines, 0.0


def build_warehouse(rng, items, store, when, date_kind, width):
    lines = [store, f"MEMBER {rng.randint(10**11, 10**12 - 1)}", ""]
    for it in items:
        code = rng.randint(100000, 999999)
        if it["quantity"] > 1:
            lines.append(f"{it['quantity']} @ {money(it['unit_price'])}")
        lines.append(pad_line(f"{code} {it['printed']}", money(it["price"]) + rng.choice([" E", " A", ""]), width))
    lines += ["", f"{format_date(when, date_kind)} {rng.randint(8, 20):02d}:{rng.randint(0, 59):02d}"]
    return lines, 0.0


def build_online(rng, items, store, when, date_kind, width):
    lines = [store, f"Order #{rng.randint(100, 999)}-{rng.randint(1000000, 9999999)}",
             f"Delivered {format_date(when, date_kind)}", ""]
    for it in items:
        lines.append(it["printed"])
        if it["quantity"] > 1:
            lines.append(pad_line(f"  Qty {it['quantity']} x ${money(it['unit_price'])}", f"${money(it['price'])}", width))
        else:
            lines.append(pad_line("  Qty 1", f"${money(it['price'])}", width))
    lines += ["", pad_line("Delivery fee", f"${money(rng.choice([0.0, 3.99, 5.99]))}", width)]
    return lines, 0.0


BUILDERS = {"supermarket": build_supermarket, "convenience": build_convenience,
            "warehouse": build_warehouse, "online": build_online}


def make_receipt(rng, index, today):
    receipt_type = RECEIPT_TYPES[index % len(RECEIPT_TYPES)]
    store = rng.choice(STORES[receipt_type])
    when = today - timedelta(days=rng.randint(0, 120))
    date_kind = DATE_FORMATS[(index // len(RECEIPT_TYPES) + index) % len(DATE_FORMATS)]
    width = 34
    items = pick_items(rng, receipt_type)
    lines, savings = BUILDERS[receipt_type](rng, items, store, when, date_kind, width)
    subtotal = round(sum(it["price"] for it in items) - savings, 2)
    tax = round(subtotal * rng.choice([0.0, 0.0, 0.0725, 0.0825]) * 0.4, 2)
    total = round(subtotal + tax, 2)
    lines += ["", pad_line("SUBTOTAL", money(subtotal), width), pad_line("TAX", money(tax), width),
              pad_line("TOTAL", money(total), width)]
    if receipt_type != "online":
        lines += [f"VISA ************{rng.randint(1000, 9999)}", pad_line("CHANGE DUE", "0.00", width), "THANK YOU FOR SHOPPING"]
    else:
        lines += ["Charged to card ending " + str(rng.randint(1000, 9999)), "Thanks for your order!"]
    return {
        "id": f"r{index + 1:03d}",
        "type": receipt_type,
        "store": store,
        "date": when.isoformat(),
        "date_format": date_kind,
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
        "items": [{k: it[k] for k in ("name", "category", "printed", "quantity", "unit_price", "price")} for it in items],
        "text": "\n".join(lines),
    }


def render(receipt, path, rng):
    """Draw the receipt text as a slightly noisy phone-photo style image."""
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter, ImageFont

    fonts = [p for p in FONT_CANDIDATES if os.path.exists(p)]
    size = rng.randint(20, 26)
    font = ImageFont.truetype(rng.choice(fonts), size) if fonts else ImageFont.load_default()
    lines = receipt["text"].split("\n")
    probe = ImageDraw.Draw(Image.new("L", (10, 10)))
    text_w = max(int(probe.textlength(line, font=font)) for line in lines)
    line_h = int(size * 1.45)
    margin = rng.randint(28, 48)
    width, height = text_w + 2 * margin, line_h * len(lines) + 2 * margin
    paper = rng.randint(232, 252)
    img = Image.new("L", (width, height), paper)
    draw = ImageDraw.Draw(img)
    ink = rng.randint(15, 60)
    for i, line in enumerate(lines):
        draw.text((margin, margin + i * line_h), line, fill=ink, font=font)

    angle = rng.uniform(-1.8, 1.8)
    img = img.rotate(angle, resample=Image.BICUBIC, expand=True, fillcolor=paper - 25)
    if rng.random() < 0.6:
        img = img.filter(ImageFilter.GaussianBlur(radius=rng.uniform(0.3, 0.9)))
    arr = np.asarray(img, dtype=np.float32)
    noise = np.random.default_rng(rng.randint(0, 2**31)).normal(0, rng.uniform(3, 9), arr.shape)
    # uneven lighting: a soft left-to-right gradient
    gradient = np.linspace(0, rng.uniform(-25, 10), arr.shape[1])[None, :]
    arr = np.clip(arr + noise + gradient, 0, 255).astype(np.uint8)
    Image.fromarray(arr).convert("RGB").save(path, format="JPEG", quality=rng.randint(70, 90))


def generate(count=DEFAULT_COUNT, seed=DEFAULT_SEED, today=date(2026, 6, 30)):
    """Return the list of receipts (ground truth plus printed text)."""
    rng = random.Random(seed)
    return [make_receipt(rng, i, today) for i in range(count)]


def write_dataset(out_dir, count=DEFAULT_COUNT, seed=DEFAULT_SEED, images=True):
    receipts = generate(count, seed)
    os.makedirs(out_dir, exist_ok=True)
    if images:
        img_dir = os.path.join(out_dir, "images")
        os.makedirs(img_dir, exist_ok=True)
        rng = random.Random(seed * 7919)
        for r in receipts:
            r["image"] = f"images/{r['id']}.jpg"
            render(r, os.path.join(out_dir, r["image"]), rng)
    manifest = {"seed": seed, "count": count, "note": "Synthetic receipts. Generated by scripts/receipt_dataset.py.",
                "receipts": receipts}
    with open(os.path.join(out_dir, "ground_truth.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1)
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default=DEFAULT_OUT)
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--no-images", action="store_true", help="write ground truth only")
    args = parser.parse_args()
    m = write_dataset(args.out, args.count, args.seed, images=not args.no_images)
    n_items = sum(len(r["items"]) for r in m["receipts"])
    print(f"Wrote {m['count']} receipts ({n_items} items) to {args.out}")
