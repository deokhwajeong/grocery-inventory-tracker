#!/usr/bin/env python3
"""
Build a static, no-backend demo of the app for GitHub Pages.

The real Jinja templates are rendered through Flask's test client against a
seeded in-memory SQLite database, then rewritten to use relative links so the
site works from any sub-path (for example /demos/grocery/). A small script in
demo/demo.js keeps the inventory in the browser's localStorage, so adding,
editing, deleting, marking items as used, the shopping list, and the receipt
review all work without a server.

The receipt step uses a generated sample receipt. Its OCR results are computed
here at build time (with Tesseract when it is installed, otherwise with the
same text parser on the receipt's known text) and shipped as data.

Usage:
    python scripts/build_demo.py                 # writes demo-dist/
    python scripts/build_demo.py --out some/dir
"""
import argparse
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

# Configure the app before it is imported (config is read at import time).
_tmpdir = tempfile.mkdtemp(prefix="grocery-demo-build-")
os.environ["DATABASE_PATH"] = os.path.join(_tmpdir, "import-time.db")
os.environ["UPLOAD_FOLDER"] = os.path.join(_tmpdir, "uploads")
os.environ["LOG_FILE"] = os.path.join(_tmpdir, "build.log")
os.environ["LOG_LEVEL"] = "WARNING"
os.environ.setdefault("SECRET_KEY", "demo-build-only")
os.environ["FLASK_ENV"] = "development"

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

import app as app_module  # noqa: E402
import ocr_processor  # noqa: E402
from ocr_advanced import get_category_suggestion  # noqa: E402
from seed_demo_data import DEMO_ITEMS  # noqa: E402

# Older purchases of things already in the fridge, so the shopping list has
# "frequently purchased" suggestions. Same tuple layout as DEMO_ITEMS.
HISTORY_ITEMS = [
    ("Large Eggs", 6, "Dairy", 16, 3, "Older half dozen"),
    ("Greek Yogurt", 2, "Dairy", 11, -3, "Vanilla"),
    ("Bananas", 2, "Produce", 9, -4, "Previous bunch"),
]

RECEIPT_STORE = "FRESH MART"
RECEIPT_LINES = [
    ("Chicken Breast", "8.99"),
    ("2x Greek Yogurt", "5.98"),
    ("Broccoli", "2.49"),
    ("Orange Juice", "3.49"),
    ("Cheddar Cheese", "4.29"),
    ("Whole Wheat Bread", "3.29"),
    ("Ground Coffee", "9.99"),
]
RECEIPT_DAYS_AGO = 1

# Flask route -> static file name
PAGES = {
    "/": "index.html",
    "/add": "add.html",
    "/ocr": "ocr.html",
    "/ocr/review": "ocr-review.html",
    "/shopping-list": "shopping-list.html",
    "/statistics": "statistics.html",
    "/settings": "settings.html",
    "/barcode": "barcode.html",
}

MEMORY_URI = "file:grocery-demo?mode=memory&cache=shared"


def use_in_memory_db():
    """Point the app at a shared-cache in-memory database for this process."""
    keepalive = sqlite3.connect(MEMORY_URI, uri=True)

    def get_db_connection():
        conn = sqlite3.connect(MEMORY_URI, uri=True)
        conn.row_factory = sqlite3.Row
        return conn

    app_module.get_db_connection = get_db_connection
    app_module.init_db()
    return keepalive


def seed(today):
    rows = []
    conn = app_module.get_db_connection()
    for name, qty, category, bought_ago, expires_in, notes in DEMO_ITEMS + HISTORY_ITEMS:
        purchase = today - timedelta(days=bought_ago)
        expiry = today + timedelta(days=expires_in) if expires_in is not None else None
        conn.execute(
            "INSERT INTO groceries (name, quantity, purchase_date, expiry_date, category, notes) VALUES (?, ?, ?, ?, ?, ?)",
            (name, qty, purchase.isoformat(), expiry.isoformat() if expiry else None, category, notes),
        )
        rows.append({
            "name": name, "quantity": qty, "category": category, "notes": notes,
            "purchase_offset": -bought_ago, "expiry_offset": expires_in,
        })
    conn.commit()
    conn.close()
    return rows


def receipt_text(today):
    purchase = (today - timedelta(days=RECEIPT_DAYS_AGO)).isoformat()
    lines = [RECEIPT_STORE, "Store 0042  Springfield", f"Date: {purchase}", ""]
    lines += [f"{name} ${price}" for name, price in RECEIPT_LINES]
    subtotal = sum(float(price) for _, price in RECEIPT_LINES)
    lines += ["", f"SUBTOTAL ${subtotal:.2f}", "TAX $0.00", f"TOTAL ${subtotal:.2f}", "VISA PAID", "THANK YOU"]
    return lines


def draw_receipt(lines, path):
    """Render a receipt image the same way the OCR test does (dark text on white)."""
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    bold_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    font = ImageFont.truetype(font_path, 22) if os.path.exists(font_path) else ImageFont.load_default()
    bold = ImageFont.truetype(bold_path, 28) if os.path.exists(bold_path) else font
    width, line_h = 520, 42
    img = Image.new("RGB", (width, 60 + line_h * len(lines) + 40), "white")
    draw = ImageDraw.Draw(img)
    y = 40
    for i, line in enumerate(lines):
        if line:
            f = bold if i == 0 else font
            x = (width - draw.textlength(line, font=f)) / 2 if i < 3 or line == "THANK YOU" else 40
            draw.text((x, y), line, fill="black", font=f)
        y += line_h
    img.save(path, optimize=True)


def precompute_ocr(image_path, lines, today):
    items, source = [], "Tesseract OCR"
    if ocr_processor.is_tesseract_available():
        try:
            items = ocr_processor.process_receipt_image(image_path, "eng")
        except Exception as exc:  # fall back to the text parser below
            print(f"OCR failed ({exc}); using the text parser instead.")
    if len(items) < len(RECEIPT_LINES) // 2:
        source = "the receipt text parser (Tesseract unavailable)"
        text = ocr_processor.post_process_ocr_text("\n".join(lines))
        items = ocr_processor.parse_receipt_text(text)
        for item in items:
            item.setdefault("category", get_category_suggestion(item["name"]))
    print(f"Receipt items precomputed with {source}.")
    purchase = (today - timedelta(days=RECEIPT_DAYS_AGO)).isoformat()
    cleaned = []
    for item in items:
        cleaned.append({
            "name": item["name"],
            "quantity": int(item.get("quantity") or 1),
            "purchase_date": item.get("purchase_date") or purchase,
            "category": item.get("category") or "Other",
            "confidence": int(item.get("confidence", 50)),
        })
    return cleaned, ("tesseract" if source == "Tesseract OCR" else "parser")


def to_relative(url):
    """Map an absolute app URL to a relative static file URL."""
    path, _, query = url.partition("?")
    query = f"?{query}" if query else ""
    if path.startswith("/static/"):
        return path[1:] + query
    match = re.fullmatch(r"/edit/(\d+)", path)
    if match:
        return f"edit.html?id={match.group(1)}"
    if re.fullmatch(r"/(delete|use)/\d+", path):
        return "index.html"
    if path in PAGES:
        return PAGES[path] + query
    raise ValueError(f"No static mapping for {url}")


SW_SCRIPT = re.compile(r"<script>\s*// Register service worker.*?</script>", re.S)
EXTERNAL_SCRIPT = re.compile(r'<script src="https?://[^"]+"></script>\s*')
MANIFEST_LINK = re.compile(r'\s*<link rel="manifest"[^>]*>')
URL_ATTR = re.compile(r'(href|src|action)="(/[^"]*)"')

BANNER = (
    '<div class="demo-banner" role="note">'
    '<span><strong>Demo mode:</strong> sample data saved only in your browser.</span>'
    '<button type="button" class="demo-reset" id="demo-reset">Reset demo data</button>'
    '<a href="https://github.com/deokhwajeong/grocery-inventory-tracker">Source on GitHub</a>'
    '</div>'
)


def postprocess(html, page):
    html, n = SW_SCRIPT.subn("", html)
    assert n == 1, "service worker script not found in layout.html"
    html = EXTERNAL_SCRIPT.sub("", html)
    html = MANIFEST_LINK.sub("", html)
    html = URL_ATTR.sub(lambda m: f'{m.group(1)}="{to_relative(m.group(2))}"', html)
    html = html.replace("'/static/", "'static/")  # icon paths inside inline scripts
    html = html.replace("</head>", '    <link rel="stylesheet" href="static/demo/demo.css">\n</head>', 1)
    html = html.replace("<body>", f'<body data-demo-page="{page}">\n    {BANNER}', 1)
    html = html.replace(
        "</body>",
        '    <script src="static/demo/demo-data.js"></script>\n'
        '    <script src="static/demo/demo.js"></script>\n</body>',
        1,
    )
    assert "\u2014" not in html, f"em dash found in {page}"
    return html


def build(out_dir):
    today = date.today()
    keepalive = use_in_memory_db()
    app_module.is_tesseract_available = lambda: True  # show the upload form, not the "OCR unavailable" notice
    seed_rows = seed(today)

    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    shutil.copytree(os.path.join(ROOT, "static"), os.path.join(out_dir, "static"),
                    ignore=shutil.ignore_patterns("service-worker.js", "manifest.json"))
    demo_static = os.path.join(out_dir, "static", "demo")
    os.makedirs(demo_static)
    for name in ("demo.js", "demo.css"):
        shutil.copy(os.path.join(ROOT, "demo", name), demo_static)

    lines = receipt_text(today)
    receipt_path = os.path.join(demo_static, "sample-receipt.png")
    draw_receipt(lines, receipt_path)
    with Image.open(receipt_path) as img:
        receipt_size = img.size
    ocr_items, ocr_engine = precompute_ocr(receipt_path, lines, today)

    first_id = app_module.get_db_connection().execute("SELECT MIN(id) FROM groceries").fetchone()[0]
    routes = dict(PAGES)
    routes[f"/edit/{first_id}"] = "edit.html"

    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as client:
        with client.session_transaction() as sess:
            sess["ocr_items"] = ocr_items
        for route, filename in routes.items():
            response = client.get(route)
            assert response.status_code == 200, f"{route} returned {response.status_code}"
            page = filename.removesuffix(".html")
            html = postprocess(response.get_data(as_text=True), page)
            with open(os.path.join(out_dir, filename), "w", encoding="utf-8") as fh:
                fh.write(html)

    data = {
        "built": today.isoformat(),
        "categories": app_module.CATEGORIES,
        "warningDays": app_module.app.config["EXPIRY_WARNING_DAYS"],
        "items": seed_rows,
        "receipt": {
            "image": "static/demo/sample-receipt.png",
            "engine": ocr_engine,
            "width": receipt_size[0],
            "height": receipt_size[1],
            "items": ocr_items,
        },
    }
    with open(os.path.join(demo_static, "demo-data.js"), "w", encoding="utf-8") as fh:
        fh.write("// Generated by scripts/build_demo.py. Synthetic demo data only.\n")
        fh.write(f"window.DEMO_SEED = {json.dumps(data, indent=1)};\n")
    open(os.path.join(out_dir, ".nojekyll"), "w").close()

    keepalive.close()
    shutil.rmtree(_tmpdir, ignore_errors=True)
    print(f"Demo built in {out_dir}: {len(routes)} pages, {len(seed_rows)} items, {len(ocr_items)} receipt items.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default=os.path.join(ROOT, "demo-dist"), help="output directory (default: demo-dist/)")
    build(os.path.abspath(parser.parse_args().out))
