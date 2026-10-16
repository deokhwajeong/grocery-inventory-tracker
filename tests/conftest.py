"""Shared pytest fixtures: every test runs against a fresh temporary SQLite DB, signed in as a test household."""
import json
import os
import sys
import tempfile

import pytest
from werkzeug.security import generate_password_hash

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

# Configure the app before it is imported (config is read at import time)
_tmpdir = tempfile.mkdtemp(prefix="grocery-tests-")
os.environ["DATABASE_PATH"] = os.path.join(_tmpdir, "test.db")
os.environ["UPLOAD_FOLDER"] = os.path.join(_tmpdir, "uploads")
os.environ["RECEIPT_FOLDER"] = os.path.join(_tmpdir, "uploads", "receipts")
os.environ["LOG_FILE"] = os.path.join(_tmpdir, "test.log")
os.environ["SECRET_KEY"] = "test-secret"
os.environ.pop("BARCODE_ONLINE_LOOKUP", None)

import app as app_module  # noqa: E402

TEST_PASSWORD = "correct horse"


def create_user(username):
    """Insert an account directly (fast hash) and return its id."""
    conn = app_module.get_db_connection()
    cur = conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                       (username, generate_password_hash(TEST_PASSWORD, method="pbkdf2:sha256:1000")))
    conn.commit()
    conn.close()
    return cur.lastrowid


def reset_database():
    app_module.init_db()
    conn = app_module.get_db_connection()
    for table in ("groceries", "receipts", "users"):
        conn.execute(f"DELETE FROM {table}")
    conn.commit()
    conn.close()
    folder = app_module.app.config["RECEIPT_FOLDER"]
    for name in os.listdir(folder) if os.path.isdir(folder) else []:
        os.remove(os.path.join(folder, name))


@pytest.fixture
def anon_client():
    """A client that is not signed in, on an empty database."""
    app_module.app.config["TESTING"] = True
    # Most tests post forms directly; test_security.py turns CSRF back on.
    app_module.app.config["WTF_CSRF_ENABLED"] = False
    reset_database()
    with app_module.app.test_client() as test_client:
        yield test_client


@pytest.fixture
def client(anon_client):
    """A client signed in as the household account "tester"."""
    user_id = create_user("tester")
    with anon_client.session_transaction() as sess:
        sess["user_id"] = user_id
    anon_client.user_id = user_id
    yield anon_client


@pytest.fixture
def user_id(client):
    return client.user_id


@pytest.fixture
def db():
    conn = app_module.get_db_connection()
    yield conn
    conn.close()


@pytest.fixture
def pending_receipt(client):
    """Factory: store a pending receipt with the given items for the signed-in account, return its id."""
    def make(items, **fields):
        conn = app_module.get_db_connection()
        cur = conn.execute(
            "INSERT INTO receipts (user_id, items_json, item_count, store, receipt_type, receipt_date, image_filename) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (client.user_id, json.dumps(items), len(items), fields.get("store", "Test Market"),
             fields.get("receipt_type", "supermarket"), fields.get("receipt_date"), fields.get("image_filename")),
        )
        conn.commit()
        conn.close()
        return cur.lastrowid
    return make
