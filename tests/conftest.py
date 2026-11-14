import os
import random
import sqlite3
import tempfile
from pathlib import Path

# app import hunu bhanda agadi set garnus, taaki test .env ma depend nagarun
os.environ.setdefault("API_KEY", "test-api-key")
os.environ["DATABASE_PATH"] = str(
    Path(tempfile.gettempdir()) / "shopstock_pytest_unused.db"
)

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.database import get_db
from app.main import app

SCHEMA_FILE = Path(__file__).resolve().parent.parent / "sql" / "schema.sql"


def pytest_addoption(parser):
    parser.addoption(
        "--test-order",
        choices=["reverse", "random"],
        default=None,
        help="run tests in reverse or random order",
    )


def pytest_collection_modifyitems(config, items):
    order = config.getoption("--test-order")
    if order == "reverse":
        items.reverse()
    elif order == "random":
        random.shuffle(items)


@pytest.fixture
def db_path(tmp_path):
    """Har test ko lagi naya, khali database file."""
    path = tmp_path / "test.db"
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA_FILE.read_text())
    conn.close()
    return path


@pytest.fixture
def client(db_path):
    """App lai temporary database sanga jodne TestClient."""

    def override_get_db():
        conn = sqlite3.connect(db_path, check_same_thread=False, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
        finally:
            conn.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def api_key():
    return settings.api_key.get_secret_value()


@pytest.fixture
def auth_headers(api_key):
    return {"X-API-Key": api_key}


@pytest.fixture
def make_category(db_path):
    def _make(name="Electronics"):
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        conn.commit()
        category_id = cursor.lastrowid
        conn.close()
        return category_id

    return _make


@pytest.fixture
def default_category_id(make_category):
    return make_category("Electronics")


@pytest.fixture
def make_product(client, auth_headers, default_category_id):
    def _make(
        sku="ELE-0001",
        name="USB Cable",
        price=350.00,
        stock_quantity=10,
        category_id=None,
    ):
        response = client.post(
            "/products",
            headers=auth_headers,
            json={
                "sku": sku,
                "name": name,
                "category_id": category_id or default_category_id,
                "price": price,
                "stock_quantity": stock_quantity,
            },
        )
        assert response.status_code == 201, response.text
        return response.json()

    return _make


@pytest.fixture
def make_order(client, auth_headers):
    def _make(items, customer_name="Anita Sharma", customer_phone="9841234567"):
        response = client.post(
            "/orders",
            headers=auth_headers,
            json={
                "customer_name": customer_name,
                "customer_phone": customer_phone,
                "items": items,
            },
        )
        assert response.status_code == 201, response.text
        return response.json()

    return _make
