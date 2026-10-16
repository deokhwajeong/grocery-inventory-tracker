"""Household accounts (#15): registration, sign-in, hashed passwords, and per-account data isolation."""
from datetime import date

import pytest

import app as app_module
from conftest import TEST_PASSWORD, create_user

TODAY = date.today().isoformat()


def register(c, username="family", password="long enough pw", confirm=None):
    return c.post("/register", data={"username": username, "password": password,
                                     "confirm": password if confirm is None else confirm})


def login(c, username, password=TEST_PASSWORD, **extra):
    return c.post("/login", data={"username": username, "password": password, **extra})


def test_pages_require_sign_in(anon_client):
    for path in ["/", "/add", "/ocr", "/receipts", "/shopping-list", "/statistics", "/settings", "/barcode"]:
        response = anon_client.get(path)
        assert response.status_code == 302 and "/login" in response.headers["Location"], path
    assert anon_client.get("/api/export").status_code == 401
    assert anon_client.post("/api/reset").get_json()["error"] == "Sign in required"
    assert anon_client.get("/login").status_code == 200
    assert anon_client.get("/register").status_code == 200
    assert anon_client.get("/static/styles.css").status_code == 200


def test_register_signs_in_and_stores_a_hash(anon_client, db):
    response = register(anon_client, "Family_1", "s3cret passphrase")
    assert response.status_code == 302 and response.headers["Location"].endswith("/")
    row = db.execute("SELECT * FROM users").fetchone()
    assert row["username"] == "Family_1"
    assert "s3cret passphrase" not in row["password_hash"] and row["password_hash"].startswith(("scrypt:", "pbkdf2:"))
    assert b"Family_1" in anon_client.get("/").data


@pytest.mark.parametrize("username, password, confirm, message", [
    ("ab", "long enough pw", None, b"username of 3 to 40"),
    ("bad name!", "long enough pw", None, b"username of 3 to 40"),
    ("family", "short", None, b"at least 8 characters"),
    ("family", "long enough pw", "different pw", b"do not match"),
])
def test_register_validation(anon_client, db, username, password, confirm, message):
    response = register(anon_client, username, password, confirm)
    assert response.status_code == 400 and message in response.data
    assert db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0


def test_usernames_are_unique_ignoring_case(anon_client):
    create_user("family")
    response = register(anon_client, "FAMILY")
    assert response.status_code == 400 and b"taken" in response.data


def test_login_logout_and_wrong_password(anon_client):
    create_user("family")
    response = login(anon_client, "family", "wrong password")
    assert response.status_code == 401 and b"Wrong username or password" in response.data
    assert login(anon_client, "nobody").status_code == 401
    response = login(anon_client, "FAMILY")                      # case-insensitive username
    assert response.status_code == 302
    assert anon_client.get("/").status_code == 200
    assert anon_client.get("/login").status_code == 302           # already signed in
    assert anon_client.get("/register").status_code == 302
    assert anon_client.get("/logout").status_code == 405          # sign-out needs a POST (CSRF protected)
    anon_client.post("/logout")
    assert anon_client.get("/").status_code == 302


def test_login_redirects_to_next_but_only_on_this_site(anon_client):
    create_user("family")
    assert "next=" in anon_client.get("/statistics").headers["Location"]
    assert login(anon_client, "family", next="/statistics").headers["Location"].endswith("/statistics")
    anon_client.post("/logout")
    assert login(anon_client, "family", next="https://evil.example/").headers["Location"].endswith("/")
    anon_client.post("/logout")
    assert login(anon_client, "family", next="//evil.example/").headers["Location"].endswith("/")


def test_deleted_account_session_is_dropped(client, db):
    db.execute("DELETE FROM users")
    db.commit()
    assert client.get("/").status_code == 302


def test_households_only_see_their_own_data(client, db, user_id):
    other = create_user("neighbours")
    db.execute("INSERT INTO groceries (name, quantity, purchase_date, category, user_id) VALUES ('Secret Salami', 1, ?, 'Meat', ?)",
               (TODAY, other))
    db.commit()
    other_item = db.execute("SELECT id FROM groceries").fetchone()[0]
    client.post("/add", data={"name": "Our Milk", "quantity": "1", "purchase_date": TODAY, "category": "Dairy"})

    for path in ["/", "/shopping-list", "/statistics", "/api/export"]:
        page = client.get(path).get_data(as_text=True)
        assert "Secret Salami" not in page, path
    assert "Our Milk" in client.get("/").get_data(as_text=True)
    assert client.get(f"/api/share/{other_item}").status_code == 404
    assert b"Item not found" in client.get(f"/edit/{other_item}", follow_redirects=True).data
    client.post(f"/edit/{other_item}", data={"name": "Hacked", "quantity": "9", "purchase_date": TODAY})
    client.post(f"/use/{other_item}")
    client.post(f"/delete/{other_item}")
    client.post("/api/reset")
    row = db.execute("SELECT name, quantity FROM groceries WHERE id = ?", (other_item,)).fetchone()
    assert (row["name"], row["quantity"]) == ("Secret Salami", 1)
    assert db.execute("SELECT COUNT(*) FROM groceries WHERE user_id = ?", (user_id,)).fetchone()[0] == 0


def test_adding_does_not_merge_into_another_households_stock(client, db, user_id):
    other = create_user("neighbours")
    db.execute("INSERT INTO groceries (name, quantity, purchase_date, category, user_id) VALUES ('Milk', 1, ?, 'Dairy', ?)",
               (TODAY, other))
    db.commit()
    client.post("/add", data={"name": "Milk", "quantity": "2", "purchase_date": TODAY, "category": "Dairy"})
    quantities = {r["user_id"]: r["quantity"] for r in db.execute("SELECT user_id, quantity FROM groceries")}
    assert quantities == {other: 1, user_id: 2}


def test_first_account_claims_items_saved_before_accounts(anon_client, db):
    db.execute("INSERT INTO groceries (name, quantity, purchase_date) VALUES ('Old Rice', 1, ?)", (TODAY,))
    db.commit()
    register(anon_client, "first")
    assert b"Old Rice" in anon_client.get("/").data
    anon_client.post("/logout")
    db.execute("INSERT INTO groceries (name, quantity, purchase_date) VALUES ('Orphan Beans', 1, ?)", (TODAY,))
    db.commit()
    register(anon_client, "second")
    assert b"Orphan Beans" not in anon_client.get("/").data   # only the first account claims old rows


def test_old_databases_are_migrated(tmp_path, monkeypatch):
    import sqlite3
    path = tmp_path / "old.db"
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE groceries (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, quantity INTEGER NOT NULL, "
                 "purchase_date TEXT NOT NULL, expiry_date TEXT, category TEXT DEFAULT 'Other', notes TEXT, "
                 "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    conn.execute("INSERT INTO groceries (name, quantity, purchase_date) VALUES ('Legacy', 1, '2026-01-01')")
    conn.commit()
    conn.close()
    monkeypatch.setitem(app_module.app.config, "DATABASE_PATH", str(path))
    app_module.init_db()
    conn = sqlite3.connect(path)
    columns = {row[1] for row in conn.execute("PRAGMA table_info(groceries)")}
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    conn.close()
    assert {"user_id", "receipt_id"} <= columns and {"users", "receipts"} <= tables


def test_account_menu_and_sign_out_form(client):
    html = client.get("/").get_data(as_text=True)
    assert "tester" in html and 'action="/logout"' in html
