#!/usr/bin/env python3
"""
Build a static, no-backend demo of the app for GitHub Pages.

The real Jinja templates are rendered through Flask's test client against a
seeded in-memory SQLite database, then rewritten to use relative links so the
site works from any sub-path (for example /demos/grocery/). A small script in
demo/demo.js keeps the inventory in the browser's localStorage, so adding,
editing, deleting, marking items as used, the shopping list, and the receipt
review all work without a server. Pages are rendered as a signed-in demo
household; the sign-in and registration pages are included and accept any
input in the demo.

The receipt step uses three generated sample receipts (supermarket,
convenience store, online order), so single and batch scanning can both be
tried. Their OCR results are computed here at build time (with Tesseract when
it is installed, otherwise with the same text parser on the receipt's known
text) and shipped as data.

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
import barcode_catalog  # noqa: E402
import ocr_processor  # noqa: E402
import receipt_store  # noqa: E402
from seed_demo_data import DEMO_ITEMS  # noqa: E402

# Older purchases of things already in the fridge, so the shopping list has
# "frequently purchased" suggestions. Same tuple layout as DEMO_ITEMS.
HISTORY_ITEMS = [
    ("Large Eggs", 6, "Dairy", 16, 3, "Older half dozen"),
    ("Greek Yogurt", 2, "Dairy", 11, -3, "Vanilla"),
    ("Bananas", 2, "Produce", 9, -4, "Previous bunch"),
]

# Three sample receipts in different layouts: (store, days ago, header lines, item lines)
W = 32


def _row(left, right):
    return f"{left}{' ' * max(2, W - len(left) - len(right))}{right}"


def sample_receipts(today):
    d1, d2, d3 = (today - timedelta(days=n) for n in (1, 2, 4))
    return [
        ("FRESH MART", [
            "FRESH MART", "Store 0042  Springfield", f"{d1:%m/%d/%Y}  18:42", "",
            _row("CHKN BRST", "8.99 F"), _row("GRK YOGURT", "5.98 F"), "  2 @ 2.99", _row("BROCCOLI", "2.49 F"),
            _row("OJ NO PULP", "3.49 F"), _row("CHDR CHS", "4.29 F"), _row("WHL WHT BRD", "3.29 F"),
            _row("GRND COFFEE", "9.99 F"), "",
            _row("SUBTOTAL", "38.52"), _row("TAX", "0.00"), _row("TOTAL", "38.52"), "VISA ************1234", "THANK YOU",
        ]),
        ("CORNER MART 24HR", [
            "CORNER MART 24HR", "STORE 2214  REG 1", f"DATE {d2:%Y-%m-%d} TIME 08:15", "",
            _row("QTY ITEM", "AMOUNT"), _row("2  BANANAS", "1.38"), _row("1  WHOLE MILK", "3.79"),
            _row("1  LG EGGS", "3.59"), "", _row("SUBTOTAL", "8.76"), _row("TAX", "0.00"), _row("TOTAL", "8.76"),
            "CASH 10.00", _row("CHANGE DUE", "1.24"),
        ]),
        ("BASKETBOX ONLINE", [
            "BASKETBOX ONLINE", "Order #318-2207741", f"Delivered {d3:%b} {d3.day}, {d3.year}", "",
            "Baby Spinach", _row("  Qty 1", "$3.99"), "Sourdough Bread", _row("  Qty 1", "$4.49"),
            "Sparkling Water", _row("  Qty 2 x $4.99", "$9.98"), "Frozen Peas", _row("  Qty 3 x $1.99", "$5.97"), "",
            _row("Delivery fee", "$3.99"), _row("TOTAL", "$28.42"), "Thanks for your order!",
        ]),
    ]

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
    "/receipts": "receipts.html",
    "/login": "login.html",
    "/register": "register.html",
}
SIGNED_OUT_PAGES = {"/login", "/register"}

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
    """Create the demo household and its items. Returns (user id, item rows for demo-data.js)."""
    rows = []
    conn = app_module.get_db_connection()
    user_id = conn.execute("INSERT INTO users (username, password_hash) VALUES ('demo', '!')").lastrowid
    for name, qty, category, bought_ago, expires_in, notes in DEMO_ITEMS + HISTORY_ITEMS:
        purchase = today - timedelta(days=bought_ago)
        expiry = today + timedelta(days=expires_in) if expires_in is not None else None
        conn.execute(
            "INSERT INTO groceries (name, quantity, purchase_date, expiry_date, category, notes, user_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, qty, purchase.isoformat(), expiry.isoformat() if expiry else None, category, notes, user_id),
        )
        rows.append({
            "name": name, "quantity": qty, "category": category, "notes": notes,
            "purchase_offset": -bought_ago, "expiry_offset": expires_in,
        })
    conn.commit()
    conn.close()
    return user_id, rows


def draw_receipt(lines, path):
    """Render a receipt image the same way the OCR test does (dark text on white)."""
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
    bold_path = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
    font = ImageFont.truetype(font_path, 22) if os.path.exists(font_path) else ImageFont.load_default()
    bold = ImageFont.truetype(bold_path, 26) if os.path.exists(bold_path) else font
    width, line_h = 500, 36
    img = Image.new("RGB", (width, 60 + line_h * len(lines) + 40), "white")
    draw = ImageDraw.Draw(img)
    y = 40
    for i, line in enumerate(lines):
        if line:
            f = bold if i == 0 else font
            x = (width - draw.textlength(line, font=f)) / 2 if i < 3 or line.startswith("THANK") else 30
            draw.text((x, y), line, fill="black", font=f)
        y += line_h
    img.save(path, optimize=True)


def precompute_ocr(image_path, lines):
    """OCR one sample receipt. Returns (analysis dict, engine name)."""
    expected = ocr_processor.parse_receipt("\n".join(lines))
    result, engine = None, "tesseract"
    if ocr_processor.is_tesseract_available():
        try:
            result = ocr_processor.analyze_receipt_image(image_path, "eng")
        except Exception as exc:  # fall back to the text parser below
            print(f"OCR failed ({exc}); using the text parser instead.")
    if not result or len(result["items"]) < len(expected["items"]) - 1:
        result, engine = expected, "parser"
    keep = ("name", "raw_name", "quantity", "price", "discount", "purchase_date", "category", "confidence")
    result["items"] = [{k: (int(v) if k == "confidence" else v) for k, v in item.items() if k in keep}
                       for item in result["items"]]
    return result, engine


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
    match = re.fullmatch(r"/receipts/(\d+)/image", path)
    if match:
        return f"static/demo/sample-receipt-{match.group(1)}.png"
    if re.fullmatch(r"/receipts/\d+/delete", path):
        return "receipts.html"
    if path == "/logout":
        return "login.html"
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
    user_id, seed_rows = seed(today)

    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    shutil.copytree(os.path.join(ROOT, "static"), os.path.join(out_dir, "static"),
                    ignore=shutil.ignore_patterns("service-worker.js", "manifest.json"))
    demo_static = os.path.join(out_dir, "static", "demo")
    os.makedirs(demo_static)
    for name in ("demo.js", "demo.css"):
        shutil.copy(os.path.join(ROOT, "demo", name), demo_static)

    # Scan the sample receipts and store them as pending receipts of the demo household.
    receipts, engines = [], set()
    conn = app_module.get_db_connection()
    for n, (store, lines) in enumerate(sample_receipts(today), start=1):
        image = os.path.join(demo_static, f"sample-receipt-{n}.png")
        draw_receipt(lines, image)
        result, engine = precompute_ocr(image, lines)
        engines.add(engine)
        rid = receipt_store.create(conn, user_id, result, f"sample-receipt-{n}.png", f"sample-receipt-{n}.png")
        assert rid == n
        with Image.open(image) as img:
            size = img.size
        receipts.append({"id": rid, "store": store, "image": f"static/demo/sample-receipt-{n}.png", "engine": engine,
                         "width": size[0], "height": size[1], "items": len(result["items"]),
                         "seconds": round(result.get("ocr_seconds") or 0.4, 2)})
    conn.commit()
    conn.close()
    print(f"Sample receipts read with: {', '.join(sorted(engines))}.")

    first_id = app_module.get_db_connection().execute("SELECT MIN(id) FROM groceries").fetchone()[0]
    all_ids = ",".join(str(r["id"]) for r in receipts)
    routes = dict(PAGES)
    routes[f"/edit/{first_id}"] = "edit.html"
    routes[f"/ocr/review?receipts={all_ids}"] = routes.pop("/ocr/review")

    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as client:
        for route, filename in routes.items():
            with client.session_transaction() as sess:
                sess.clear()
                if route not in SIGNED_OUT_PAGES:
                    sess["user_id"] = user_id
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
        "mergeWindowDays": app_module.app.config["MERGE_EXPIRY_WINDOW_DAYS"],
        "barcodes": list(barcode_catalog.CATALOG.values()),
        "items": seed_rows,
        "receipts": receipts,
    }
    with open(os.path.join(demo_static, "demo-data.js"), "w", encoding="utf-8") as fh:
        fh.write("// Generated by scripts/build_demo.py. Synthetic demo data only.\n")
        fh.write(f"window.DEMO_SEED = {json.dumps(data, indent=1)};\n")
    open(os.path.join(out_dir, ".nojekyll"), "w").close()

    keepalive.close()
    shutil.rmtree(_tmpdir, ignore_errors=True)
    n_items = sum(r["items"] for r in receipts)
    print(f"Demo built in {out_dir}: {len(routes)} pages, {len(seed_rows)} items, {len(receipts)} receipts ({n_items} items).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default=os.path.join(ROOT, "demo-dist"), help="output directory (default: demo-dist/)")
    build(os.path.abspath(parser.parse_args().out))
