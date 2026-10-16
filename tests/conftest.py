"""Shared pytest fixtures: every test runs against a fresh temporary SQLite DB."""
import os
import sys
import tempfile

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# Configure the app before it is imported (config is read at import time)
_tmpdir = tempfile.mkdtemp(prefix="grocery-tests-")
os.environ["DATABASE_PATH"] = os.path.join(_tmpdir, "test.db")
os.environ["UPLOAD_FOLDER"] = os.path.join(_tmpdir, "uploads")
os.environ["LOG_FILE"] = os.path.join(_tmpdir, "test.log")
os.environ["SECRET_KEY"] = "test-secret"

import app as app_module  # noqa: E402


@pytest.fixture
def client():
    app_module.app.config["TESTING"] = True
    # Most tests post forms directly; test_security.py turns CSRF back on.
    app_module.app.config["WTF_CSRF_ENABLED"] = False
    app_module.init_db()
    conn = app_module.get_db_connection()
    conn.execute("DELETE FROM groceries")
    conn.commit()
    conn.close()
    with app_module.app.test_client() as test_client:
        yield test_client


@pytest.fixture
def db():
    conn = app_module.get_db_connection()
    yield conn
    conn.close()
