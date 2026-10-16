"""CSRF protection, upload validation, and the offline barcode lookup."""
import io
import re
from datetime import date

import pytest
from PIL import Image

import app as app_module
import barcode_catalog


def png_bytes():
    buf = io.BytesIO()
    Image.new("RGB", (40, 20), "white").save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def csrf_client(client):
    app_module.app.config["WTF_CSRF_ENABLED"] = True
    yield client
    app_module.app.config["WTF_CSRF_ENABLED"] = False


def token_from(html):
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


def test_post_without_csrf_token_is_rejected(csrf_client, db):
    response = csrf_client.post("/add", data={"name": "Milk", "quantity": "1", "purchase_date": date.today().isoformat()},
                                follow_redirects=True)
    assert b"session expired or the form was out of date" in response.data
    assert db.execute("SELECT COUNT(*) FROM groceries").fetchone()[0] == 0


def test_post_with_csrf_token_succeeds(csrf_client, db):
    token = token_from(csrf_client.get("/add").get_data(as_text=True))
    csrf_client.post("/add", data={"name": "Milk", "quantity": "1", "purchase_date": date.today().isoformat(),
                                   "csrf_token": token})
    assert db.execute("SELECT COUNT(*) FROM groceries").fetchone()[0] == 1


def test_json_endpoints_need_csrf_header(csrf_client):
    response = csrf_client.post("/api/reset")
    assert response.status_code == 400 and "CSRF" in response.get_json()["error"]
    page = csrf_client.get("/settings").get_data(as_text=True)
    token = re.search(r'<meta name="csrf-token" content="([^"]+)"', page).group(1)
    assert csrf_client.post("/api/reset", headers={"X-CSRFToken": token}).get_json() == {"success": True}


def test_upload_rejects_files_that_are_not_images(client, monkeypatch):
    monkeypatch.setattr(app_module, "is_tesseract_available", lambda: True)
    response = client.post("/ocr", data={"receipt": (io.BytesIO(b"not really a png"), "receipt.png")},
                           content_type="multipart/form-data", follow_redirects=True)
    assert b"not a readable image" in response.data


def test_upload_rejects_wrong_extension(client, monkeypatch):
    monkeypatch.setattr(app_module, "is_tesseract_available", lambda: True)
    response = client.post("/ocr", data={"receipt": (io.BytesIO(png_bytes()), "receipt.pdf")},
                           content_type="multipart/form-data", follow_redirects=True)
    assert b"Invalid file type" in response.data


def test_upload_size_limit(client, monkeypatch):
    monkeypatch.setitem(app_module.app.config, "MAX_CONTENT_LENGTH", 1024 * 1024)
    response = client.post("/ocr", data={"receipt": (io.BytesIO(b"0" * (2 * 1024 * 1024)), "big.png")},
                           content_type="multipart/form-data", follow_redirects=True)
    assert b"too large" in response.data


def test_upload_runs_ocr_on_a_valid_image(client, monkeypatch):
    monkeypatch.setattr(app_module, "is_tesseract_available", lambda: True)
    monkeypatch.setattr(app_module, "process_receipt_image", lambda path, langs: [
        {"name": "Milk", "quantity": 1, "purchase_date": date.today().isoformat(), "category": "Dairy", "confidence": 90}])
    response = client.post("/ocr", data={"receipt": (io.BytesIO(png_bytes()), "receipt.png")},
                           content_type="multipart/form-data")
    assert response.status_code == 302 and response.headers["Location"].endswith("/ocr/review")


def test_catalog_codes_have_valid_check_digits():
    assert barcode_catalog.CATALOG
    for product in barcode_catalog.CATALOG.values():
        code = product["barcode"]
        assert code.startswith("2") and len(code) == 12      # GS1 store-internal prefix, never a real product
        assert barcode_catalog.is_valid_gtin(code)


def test_known_check_digits():
    assert barcode_catalog.is_valid_gtin("036000291452")      # GS1 UPC-A example
    assert barcode_catalog.is_valid_gtin("4006381333931")     # GS1 EAN-13 example
    assert not barcode_catalog.is_valid_gtin("036000291453")
    assert not barcode_catalog.is_valid_gtin("12345")


def test_barcode_lookup_found(client):
    code = barcode_catalog.sample_codes(1)[0]["barcode"]
    data = client.get(f"/api/barcode/{code}").get_json()
    assert data["found"] and data["name"] == "Whole Milk" and data["category"] == "Dairy"
    assert client.get(f"/api/barcode/0{code}").get_json()["found"]     # EAN-13 form of the same code


def test_barcode_lookup_not_found_and_invalid(client):
    response = client.get("/api/barcode/036000291452")
    assert response.status_code == 404 and response.get_json()["found"] is False
    response = client.get("/api/barcode/hello")
    assert response.status_code == 400 and "check digit" in response.get_json()["error"]


def test_barcode_page_lists_sample_codes(client):
    html = client.get("/barcode").get_data(as_text=True)
    assert "offline catalog" in html
    assert barcode_catalog.sample_codes(1)[0]["barcode"] in html
