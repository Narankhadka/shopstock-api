import sqlite3


def test_fresh_database_has_all_tables(db_path):
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
    ).fetchall()
    conn.close()

    table_names = {row[0] for row in rows}
    expected = {"categories", "products", "orders", "order_items", "stock_movements"}
    assert expected <= table_names


def test_health_returns_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}


def test_write_endpoint_rejects_missing_api_key(client):
    response = client.post("/products", json={})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_make_category_appears_in_categories_list(client, make_category):
    category_id = make_category("Stationery")

    response = client.get("/categories")

    assert response.status_code == 200
    assert response.json() == [
        {"id": category_id, "name": "Stationery", "active_product_count": 0}
    ]


def test_make_product_creates_visible_product(client, make_product):
    product = make_product()

    response = client.get(f"/products/{product['id']}")

    assert response.status_code == 200
    assert response.json()["sku"] == "ELE-0001"


def test_make_order_reduces_stock(client, make_product, make_order):
    product = make_product(stock_quantity=10)

    order = make_order([{"product_id": product["id"], "quantity": 3}])

    assert order["status"] == "pending"
    response = client.get(f"/products/{product['id']}")
    assert response.json()["stock_quantity"] == 7
