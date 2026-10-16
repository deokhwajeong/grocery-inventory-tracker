"""Route-level tests for the Flask app."""
from datetime import date, timedelta

import app as app_module


def iso(days_from_today):
    return (date.today() + timedelta(days=days_from_today)).isoformat()


def add_item(db, name, qty=1, purchase=-1, expiry=None, category="Other", notes=""):
    db.execute(
        "INSERT INTO groceries (name, quantity, purchase_date, expiry_date, category, notes) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (name, qty, iso(purchase), iso(expiry) if expiry is not None else None, category, notes),
    )
    db.commit()


def test_all_pages_render(client):
    for path in ["/", "/add", "/ocr", "/shopping-list", "/statistics", "/settings", "/barcode"]:
        response = client.get(path)
        assert response.status_code == 200, path


def test_static_assets_are_served_locally(client):
    for path in ["/static/styles.css", "/static/vendor/bootstrap/bootstrap.min.css",
                 "/static/vendor/bootstrap/bootstrap.bundle.min.js", "/static/manifest.json"]:
        assert client.get(path).status_code == 200, path


def test_add_item_and_show_on_dashboard(client, db):
    response = client.post("/add", data={
        "name": "Greek Yogurt", "quantity": "2", "purchase_date": iso(0),
        "expiry_date": iso(5), "category": "Dairy", "notes": "Plain",
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Greek Yogurt" in response.data
    row = db.execute("SELECT * FROM groceries").fetchone()
    assert row["quantity"] == 2
    assert row["category"] == "Dairy"


def test_add_rejects_invalid_input(client, db):
    response = client.post("/add", data={"name": "Milk", "quantity": "0", "purchase_date": iso(0)})
    assert b"Quantity must be a positive number" in response.data
    response = client.post("/add", data={
        "name": "Milk", "quantity": "1", "purchase_date": iso(0), "expiry_date": iso(-3),
    })
    assert b"Expiry date cannot be before purchase date" in response.data
    assert db.execute("SELECT COUNT(*) FROM groceries").fetchone()[0] == 0


def test_unknown_category_falls_back_to_other(client, db):
    client.post("/add", data={"name": "Mystery", "quantity": "1", "purchase_date": iso(0),
                              "category": "Not a category"})
    assert db.execute("SELECT category FROM groceries").fetchone()[0] == "Other"


def test_edit_item(client, db):
    add_item(db, "Bananas", qty=6, category="Produce")
    item_id = db.execute("SELECT id FROM groceries").fetchone()[0]
    response = client.post(f"/edit/{item_id}", data={
        "name": "Bananas", "quantity": "3", "purchase_date": iso(-1), "category": "Produce",
    }, follow_redirects=True)
    assert response.status_code == 200
    assert db.execute("SELECT quantity FROM groceries").fetchone()[0] == 3


def test_delete_requires_post(client, db):
    add_item(db, "Bagels")
    item_id = db.execute("SELECT id FROM groceries").fetchone()[0]
    assert client.get(f"/delete/{item_id}").status_code == 405
    client.post(f"/delete/{item_id}")
    assert db.execute("SELECT COUNT(*) FROM groceries").fetchone()[0] == 0


def test_mark_used_decrements_then_removes(client, db):
    add_item(db, "Greek Yogurt", qty=2)
    item_id = db.execute("SELECT id FROM groceries").fetchone()[0]
    assert client.get(f"/use/{item_id}").status_code == 405
    response = client.post(f"/use/{item_id}", follow_redirects=True)
    assert b"1 left" in response.data
    assert db.execute("SELECT quantity FROM groceries").fetchone()[0] == 1
    client.post(f"/use/{item_id}")
    assert db.execute("SELECT COUNT(*) FROM groceries").fetchone()[0] == 0


def test_dashboard_expiry_counts_and_warnings(client, db):
    add_item(db, "Old Spinach", expiry=-2, category="Produce")
    add_item(db, "Chicken Thighs", expiry=1, category="Meat")
    add_item(db, "Cheddar", expiry=20, category="Dairy")
    add_item(db, "Rice", category="Pantry")
    html = client.get("/").get_data(as_text=True)
    assert "Use these first" in html
    assert "Expired 2 days ago" in html
    assert "Expires tomorrow" in html
    # Expiring soon excludes already expired items; expired is its own count
    with app_module.app.test_request_context():
        conn = app_module.get_db_connection()
        soon = conn.execute(
            "SELECT COUNT(*) FROM groceries WHERE expiry_date >= date('now') "
            "AND expiry_date <= date('now', '+7 days')").fetchone()[0]
        conn.close()
    assert soon == 1


def test_sort_by_expiry_is_soonest_first(client, db):
    add_item(db, "Later", expiry=30)
    add_item(db, "Sooner", expiry=2)
    add_item(db, "No date")
    html = client.get("/?sort=expiry_date").get_data(as_text=True)
    assert html.index("Sooner") < html.index("Later") < html.index("No date")


def test_search_and_category_filter(client, db):
    add_item(db, "Whole Milk", category="Dairy")
    add_item(db, "Sourdough", category="Bakery")
    html = client.get("/?search=milk").get_data(as_text=True)
    assert "Whole Milk" in html and "Sourdough" not in html
    html = client.get("/?category=Bakery").get_data(as_text=True)
    assert "Sourdough" in html and "Whole Milk" not in html


def test_item_names_with_quotes_are_safe(client, db):
    add_item(db, "Baker's <b>Bread</b>")
    html = client.get("/").get_data(as_text=True)
    assert "<b>Bread</b>" not in html
    assert "&lt;b&gt;" in html


def test_notifications_api(client, db):
    add_item(db, "Today Milk", expiry=0)
    add_item(db, "Tomorrow Eggs", expiry=1)
    add_item(db, "Soon Berries", expiry=3)
    data = client.get("/api/notifications/check").get_json()
    assert [i["name"] for i in data["today"]] == ["Today Milk"]
    assert [i["name"] for i in data["tomorrow"]] == ["Tomorrow Eggs"]
    assert [i["name"] for i in data["soon"]] == ["Soon Berries"]


def test_export_csv(client, db):
    add_item(db, "Olive Oil", category="Pantry")
    response = client.get("/api/export")
    assert response.mimetype == "text/csv"
    assert "Olive Oil" in response.get_data(as_text=True)


def test_clear_expired(client, db):
    add_item(db, "Expired Yogurt", expiry=-1)
    add_item(db, "Fresh Yogurt", expiry=5)
    assert client.post("/api/clear-expired").get_json()["count"] == 1
    names = [r[0] for r in db.execute("SELECT name FROM groceries")]
    assert names == ["Fresh Yogurt"]


def test_statistics_with_data(client, db):
    add_item(db, "Expired Yogurt", expiry=-1, category="Dairy")
    add_item(db, "Apples", expiry=10, category="Produce")
    html = client.get("/statistics").get_data(as_text=True)
    assert "50.0%" in html


def test_settings_warning_days_affects_dashboard(client, db):
    add_item(db, "Carrots", expiry=10, category="Produce")
    assert "Use these first" not in client.get("/").get_data(as_text=True)
    client.post("/settings", data={"expiry_warning_days": "14"})
    assert "Use these first" in client.get("/").get_data(as_text=True)


def test_ocr_review_saves_selected_items(client, db):
    with client.session_transaction() as sess:
        sess["ocr_items"] = [
            {"name": "Milk", "quantity": 1, "purchase_date": iso(0), "category": "Dairy", "confidence": 95},
            {"name": "Bread", "quantity": 1, "purchase_date": iso(0), "category": "Bakery", "confidence": 90},
        ]
    page = client.get("/ocr/review")
    assert page.status_code == 200 and b"Milk" in page.data
    client.post("/ocr/review", data={
        "selected": ["0"], "name_0": "Milk", "quantity_0": "2", "purchase_date_0": iso(0),
        "expiry_date_0": iso(7), "category_0": "Dairy",
    })
    rows = db.execute("SELECT name, quantity FROM groceries").fetchall()
    assert [(r[0], r[1]) for r in rows] == [("Milk", 2)]


def test_ocr_upload_without_tesseract_degrades_gracefully(client, monkeypatch):
    import io
    monkeypatch.setattr(app_module, "is_tesseract_available", lambda: False)
    page = client.get("/ocr").get_data(as_text=True)
    assert "OCR is unavailable" in page
    response = client.post("/ocr", data={"receipt": (io.BytesIO(b"fake"), "r.png")},
                           content_type="multipart/form-data", follow_redirects=True)
    assert response.status_code == 200
    assert "Tesseract OCR engine" in response.get_data(as_text=True)
