"""Receipt image storage (#20), batch upload (#5), the online barcode lookup (#8) and dark mode (#16)."""
import io
import json
import os
import urllib.error
from datetime import date

import pytest
from PIL import Image

import app as app_module
import barcode_catalog
import check_contrast
from conftest import create_user

TODAY = date.today().isoformat()


def image_bytes(size=(400, 600), fmt="PNG", color="white"):
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format=fmt)
    return buf.getvalue()


@pytest.fixture
def fake_ocr(monkeypatch):
    """Pretend OCR: every image yields the items given (default: milk and bread)."""
    calls = []

    def analyze(path, langs):
        calls.append(path)
        assert os.path.exists(path)          # the upload is on disk while OCR runs
        items = [{"name": "Milk", "quantity": 1, "purchase_date": TODAY, "category": "Dairy", "confidence": 90, "price": "3.99"},
                 {"name": "Bread", "quantity": 2, "purchase_date": TODAY, "category": "Bakery", "confidence": 80, "price": "5.00"}]
        return {"items": items, "date": TODAY, "store": "TEST MARKET", "receipt_type": "supermarket", "ocr_seconds": 0.4}
    monkeypatch.setattr(app_module, "is_tesseract_available", lambda: True)
    monkeypatch.setattr(app_module, "analyze_receipt_image", analyze)
    return calls


def receipt_files(db):
    folder = app_module.app.config["RECEIPT_FOLDER"]
    names = [r["image_filename"] for r in db.execute("SELECT image_filename FROM receipts") if r["image_filename"]]
    return [os.path.join(folder, n) for n in names]


# ---------------------------------------------------------------- image storage (#20)

def test_upload_stores_a_downscaled_jpeg_and_review_shows_it(client, db, fake_ocr):
    response = client.post("/ocr", data={"receipt": (io.BytesIO(image_bytes((3000, 4000))), "photo.png")},
                           content_type="multipart/form-data")
    assert response.status_code == 302
    review = response.headers["Location"]
    receipt = db.execute("SELECT * FROM receipts").fetchone()
    assert receipt["status"] == "pending" and receipt["item_count"] == 2 and receipt["original_name"] == "photo.png"
    [path] = receipt_files(db)
    with Image.open(path) as img:
        assert img.format == "JPEG" and max(img.size) == app_module.app.config["RECEIPT_MAX_DIMENSION"]
    # the temporary upload is gone, only the stored copy remains
    assert sorted(os.listdir(app_module.app.config["UPLOAD_FOLDER"])) == ["receipts"]

    html = client.get(review).get_data(as_text=True)
    assert f"/receipts/{receipt['id']}/image" in html and "TEST MARKET" in html
    image = client.get(f"/receipts/{receipt['id']}/image")
    assert image.status_code == 200 and image.mimetype == "image/jpeg" and "private" in image.headers["Cache-Control"]


def test_history_lists_receipts_and_items_link_back(client, db, fake_ocr):
    client.post("/ocr", data={"receipt": (io.BytesIO(image_bytes()), "r.png")}, content_type="multipart/form-data")
    rid = db.execute("SELECT id FROM receipts").fetchone()[0]
    assert "Waiting for review" in client.get("/receipts").get_data(as_text=True)
    client.post(f"/ocr/review?receipts={rid}", data={"selected": ["0"], "name_0": "Milk", "quantity_0": "1",
                                                      "purchase_date_0": TODAY, "category_0": "Dairy"})
    html = client.get("/receipts").get_data(as_text=True)
    assert "1 of 2 added" in html and "TEST MARKET" in html
    item_id = db.execute("SELECT id FROM groceries WHERE receipt_id = ?", (rid,)).fetchone()[0]
    assert "Added from a scanned receipt" in client.get(f"/edit/{item_id}").get_data(as_text=True)


def test_other_households_cannot_see_receipts(client, db, fake_ocr):
    client.post("/ocr", data={"receipt": (io.BytesIO(image_bytes()), "r.png")}, content_type="multipart/form-data")
    rid = db.execute("SELECT id FROM receipts").fetchone()[0]
    other = create_user("neighbours")
    with client.session_transaction() as sess:
        sess["user_id"] = other
    assert client.get(f"/receipts/{rid}/image").status_code == 404
    assert client.get(f"/ocr/review?receipts={rid}").status_code == 302
    assert "No receipts yet" in client.get("/receipts").get_data(as_text=True)
    client.post(f"/receipts/{rid}/delete")
    assert db.execute("SELECT COUNT(*) FROM receipts").fetchone()[0] == 1


def test_delete_receipt_removes_image_but_keeps_items(client, db, fake_ocr):
    client.post("/ocr", data={"receipt": (io.BytesIO(image_bytes()), "r.png")}, content_type="multipart/form-data")
    rid = db.execute("SELECT id FROM receipts").fetchone()[0]
    client.post(f"/ocr/review?receipts={rid}", data={"selected": ["0", "1"], "name_0": "Milk", "quantity_0": "1",
                                                      "purchase_date_0": TODAY, "name_1": "Bread", "quantity_1": "2",
                                                      "purchase_date_1": TODAY})
    [path] = receipt_files(db)
    response = client.post(f"/receipts/{rid}/delete", follow_redirects=True)
    assert b"Receipt deleted" in response.data
    assert not os.path.exists(path)
    assert db.execute("SELECT COUNT(*) FROM receipts").fetchone()[0] == 0
    assert [r[0] for r in db.execute("SELECT receipt_id FROM groceries")] == [None, None]
    assert b"Receipt not found" in client.post(f"/receipts/{rid}/delete", follow_redirects=True).data
    assert client.get(f"/receipts/{rid}/image").status_code == 404


def test_only_the_newest_images_are_kept(client, db, fake_ocr, monkeypatch):
    monkeypatch.setitem(app_module.app.config, "RECEIPT_KEEP", 2)
    for i in range(3):
        client.post("/ocr", data={"receipt": (io.BytesIO(image_bytes()), f"r{i}.png")}, content_type="multipart/form-data")
    rows = db.execute("SELECT id, image_filename FROM receipts ORDER BY id").fetchall()
    assert [r["image_filename"] is None for r in rows] == [True, False, False]
    assert len(os.listdir(app_module.app.config["RECEIPT_FOLDER"])) == 2
    assert "No image" in client.get("/receipts").get_data(as_text=True)


def test_image_storage_can_be_turned_off(client, db, fake_ocr, monkeypatch):
    monkeypatch.setitem(app_module.app.config, "STORE_RECEIPT_IMAGES", False)
    client.post("/ocr", data={"receipt": (io.BytesIO(image_bytes()), "r.png")}, content_type="multipart/form-data")
    receipt = db.execute("SELECT * FROM receipts").fetchone()
    assert receipt["image_filename"] is None and receipt["item_count"] == 2
    assert "Image storage is turned off" in client.get("/receipts").get_data(as_text=True)


def test_receipt_with_no_items_is_not_stored(client, db, monkeypatch):
    monkeypatch.setattr(app_module, "is_tesseract_available", lambda: True)
    monkeypatch.setattr(app_module, "analyze_receipt_image", lambda path, langs: {"items": []})
    response = client.post("/ocr", data={"receipt": (io.BytesIO(image_bytes()), "r.png")},
                           content_type="multipart/form-data", follow_redirects=True)
    assert b"No items found" in response.data
    assert db.execute("SELECT COUNT(*) FROM receipts").fetchone()[0] == 0
    assert os.listdir(app_module.app.config["RECEIPT_FOLDER"]) == []


def test_discard_scan(client, db, pending_receipt):
    rid = pending_receipt([{"name": "Milk", "quantity": 1, "purchase_date": TODAY}])
    response = client.post(f"/ocr/review?receipts={rid}", data={"action": "discard"}, follow_redirects=True)
    assert b"Scan discarded" in response.data
    assert db.execute("SELECT status FROM receipts").fetchone()[0] == "discarded"
    assert db.execute("SELECT COUNT(*) FROM groceries").fetchone()[0] == 0


def test_ocr_failure_on_one_file_is_reported(client, db, monkeypatch):
    monkeypatch.setattr(app_module, "is_tesseract_available", lambda: True)

    def boom(path, langs):
        raise RuntimeError("tesseract crashed")
    monkeypatch.setattr(app_module, "analyze_receipt_image", boom)
    response = client.post("/ocr", data={"receipt": (io.BytesIO(image_bytes()), "r.png")},
                           content_type="multipart/form-data", follow_redirects=True)
    assert b"Could not read that receipt" in response.data and b"tesseract crashed" not in response.data
    assert client.post("/api/ocr/scan", data={"receipt": (io.BytesIO(image_bytes()), "r.png")},
                       content_type="multipart/form-data").status_code == 500


# ---------------------------------------------------------------- batch upload (#5)

def test_batch_upload_without_javascript_reviews_all_receipts_together(client, db, fake_ocr):
    files = [(io.BytesIO(image_bytes()), f"receipt{i}.png") for i in range(3)]
    response = client.post("/ocr", data={"receipt": files}, content_type="multipart/form-data", follow_redirects=True)
    html = response.get_data(as_text=True)
    assert "Found 6 items from 3 receipts" in html and "your 3 receipts" in html
    assert len(fake_ocr) == 3
    assert html.count('class="panel p-0 mb-3 receipt-group"') == 3
    ids = [r[0] for r in db.execute("SELECT id FROM receipts ORDER BY id")]
    # rows are numbered across receipts; pick one item from the first and one from the last receipt
    client.post(f"/ocr/review?receipts={','.join(map(str, ids))}", data={
        "selected": ["0", "5"], "name_0": "Milk", "quantity_0": "1", "purchase_date_0": TODAY, "category_0": "Dairy",
        "name_5": "Bread", "quantity_5": "2", "purchase_date_5": TODAY, "category_5": "Bakery"})
    rows = {r["name"]: r["receipt_id"] for r in db.execute("SELECT name, receipt_id FROM groceries")}
    assert rows == {"Milk": ids[0], "Bread": ids[2]}
    statuses = [(r["status"], r["imported_count"]) for r in db.execute("SELECT * FROM receipts ORDER BY id")]
    assert statuses == [("imported", 1), ("imported", 0), ("imported", 1)]


def test_batch_skips_bad_files_and_keeps_good_ones(client, db, fake_ocr):
    files = [(io.BytesIO(image_bytes()), "good.png"), (io.BytesIO(b"not an image"), "bad.png"), (io.BytesIO(b"x"), "doc.pdf")]
    response = client.post("/ocr", data={"receipt": files}, content_type="multipart/form-data", follow_redirects=True)
    html = response.get_data(as_text=True)
    assert "not a readable image" in html and "Invalid file type" in html and "Review scanned items" in html
    assert db.execute("SELECT COUNT(*) FROM receipts").fetchone()[0] == 1


def test_batch_size_limit(client, fake_ocr, monkeypatch):
    monkeypatch.setitem(app_module.app.config, "BATCH_MAX_FILES", 2)
    files = [(io.BytesIO(image_bytes()), f"r{i}.png") for i in range(3)]
    response = client.post("/ocr", data={"receipt": files}, content_type="multipart/form-data", follow_redirects=True)
    assert b"at most 2 receipts" in response.data and not fake_ocr


def test_scan_api_processes_one_file_for_the_progress_view(client, db, fake_ocr):
    data = client.post("/api/ocr/scan", data={"receipt": (io.BytesIO(image_bytes()), "r.png")},
                       content_type="multipart/form-data").get_json()
    assert data["items"] == 2 and data["seconds"] == 0.4 and data["review_url"].endswith(f"receipts={data['receipt_id']}")
    bad = client.post("/api/ocr/scan", data={"receipt": (io.BytesIO(b"nope"), "r.png")}, content_type="multipart/form-data")
    assert bad.status_code == 400 and "readable image" in bad.get_json()["error"]
    assert client.post("/api/ocr/scan").status_code == 400


def test_scan_api_without_tesseract_and_without_items(client, monkeypatch):
    monkeypatch.setattr(app_module, "is_tesseract_available", lambda: False)
    assert client.post("/api/ocr/scan").status_code == 503
    monkeypatch.setattr(app_module, "is_tesseract_available", lambda: True)
    monkeypatch.setattr(app_module, "analyze_receipt_image", lambda path, langs: {"items": []})
    data = client.post("/api/ocr/scan", data={"receipt": (io.BytesIO(image_bytes()), "r.png")},
                       content_type="multipart/form-data").get_json()
    assert data["receipt_id"] is None and "No items" in data["message"]


def test_upload_page_supports_multiple_files(client):
    html = client.get("/ocr").get_data(as_text=True)
    assert 'name="receipt" accept="image/*" multiple' in html and 'data-scan-url="/api/ocr/scan"' in html


def test_too_large_upload_on_the_api_is_json(client, monkeypatch):
    monkeypatch.setitem(app_module.app.config, "MAX_CONTENT_LENGTH", 1024)
    response = client.post("/api/ocr/scan", data={"receipt": (io.BytesIO(b"0" * 4096), "big.png")},
                           content_type="multipart/form-data")
    assert response.status_code == 413 and "too large" in response.get_json()["error"]


# ---------------------------------------------------------------- online barcode lookup (#8)

class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def off_payload(status=1, **product):
    return FakeResponse(json.dumps({"status": status, "product": product}).encode())


REAL_CODE = "4006381333931"   # GS1's published EAN-13 example


def test_online_lookup_is_off_by_default(client, monkeypatch):
    def no_network(*args, **kwargs):
        raise AssertionError("must not go online")
    monkeypatch.setattr(barcode_catalog.urllib.request, "urlopen", no_network)
    response = client.get(f"/api/barcode/{REAL_CODE}")
    assert response.status_code == 404 and response.get_json()["online"] is False
    assert "Online lookup on Open Food Facts is" in client.get("/barcode").get_data(as_text=True)


def test_online_lookup_finds_real_products(client, monkeypatch):
    barcode_catalog.lookup_online.cache_clear()
    monkeypatch.setitem(app_module.app.config, "BARCODE_ONLINE_LOOKUP", True)
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"], seen["timeout"], seen["agent"] = request.full_url, timeout, request.get_header("User-agent")
        return off_payload(product_name="Highlighter Yellow", brands="Stabilo",
                           categories_tags=["en:snacks", "en:sweet-snacks"])
    monkeypatch.setattr(barcode_catalog.urllib.request, "urlopen", fake_urlopen)
    data = client.get(f"/api/barcode/{REAL_CODE}").get_json()
    assert data == {"barcode": REAL_CODE, "found": True, "name": "Stabilo Highlighter Yellow", "category": "Snacks",
                    "source": "Open Food Facts"}
    assert REAL_CODE in seen["url"] and seen["timeout"] == 4.0 and "GroceryInventoryTracker" in seen["agent"]
    # the bundled catalog is still checked first, without a network call
    monkeypatch.setattr(barcode_catalog.urllib.request, "urlopen", None)
    local = barcode_catalog.sample_codes(1)[0]["barcode"]
    assert client.get(f"/api/barcode/{local}").get_json()["source"] == "local catalog"
    assert "then Open Food Facts" in client.get("/barcode").get_data(as_text=True)


@pytest.mark.parametrize("behaviour", ["offline", "unknown", "garbage"])
def test_online_lookup_falls_back_to_manual_entry(client, monkeypatch, behaviour):
    barcode_catalog.lookup_online.cache_clear()
    monkeypatch.setitem(app_module.app.config, "BARCODE_ONLINE_LOOKUP", True)

    def fake_urlopen(request, timeout):
        if behaviour == "offline":
            raise urllib.error.URLError("no network")
        if behaviour == "unknown":
            return off_payload(status=0)
        return FakeResponse(b"<html>not json</html>")
    monkeypatch.setattr(barcode_catalog.urllib.request, "urlopen", fake_urlopen)
    response = client.get(f"/api/barcode/{REAL_CODE}")
    assert response.status_code == 404
    assert response.get_json()["online"] is True and "manually" in response.get_json()["message"]


def test_off_category_mapping():
    assert barcode_catalog.map_off_category(["en:plant-based-foods", "en:frozen-foods"]) == "Frozen"
    assert barcode_catalog.map_off_category(["en:dairies", "en:cheeses"]) == "Dairy"
    assert barcode_catalog.map_off_category(["fr:boissons", "en:beverages"]) == "Beverages"
    assert barcode_catalog.map_off_category([]) == "Other"
    assert barcode_catalog.lookup_online("123") is None


# ---------------------------------------------------------------- dark mode (#16)

def test_theme_is_applied_before_paint_and_toggle_is_present(client):
    pages = [client.get("/").get_data(as_text=True)]
    client.post("/logout")
    pages.append(client.get("/login").get_data(as_text=True))       # signed out: toggle still there
    for html in pages:
        head = html.split("</head>")[0]
        assert "prefers-color-scheme: dark" in head and "data-bs-theme" in head
        assert head.index("data-bs-theme") < head.index("styles.css")    # set before the stylesheet loads
        assert 'id="theme-toggle"' in html and "theme.js" in html
    assert client.get("/static/theme.js").status_code == 200


def test_theme_colors_meet_wcag_aa():
    rows = check_contrast.check()
    assert {r[0] for r in rows} == {"light", "dark"}
    low = [r for r in rows if r[4] < 4.5]
    assert not low, low
