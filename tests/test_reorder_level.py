import pytest


def create_product(client, auth_headers, category_id, **overrides):
    payload = {
        "sku": "ELE-0001",
        "name": "USB Cable",
        "category_id": category_id,
        "price": 350.00,
        "stock_quantity": 10,
    }
    payload.update(overrides)
    return client.post("/products", headers=auth_headers, json=payload)


def test_new_product_without_reorder_level_gets_default_5(
    client, auth_headers, default_category_id
):
    response = create_product(client, auth_headers, default_category_id)

    assert response.status_code == 201
    assert response.json()["reorder_level"] == 5


def test_reorder_level_appears_in_every_product_response(
    client, auth_headers, default_category_id
):
    created = create_product(
        client, auth_headers, default_category_id, sku="ELE-0009", reorder_level=20
    ).json()

    assert created["reorder_level"] == 20
    assert client.get(f"/products/{created['id']}").json()["reorder_level"] == 20
    assert client.get("/products/sku/ELE-0009").json()["reorder_level"] == 20
    assert client.get("/products").json()["items"][0]["reorder_level"] == 20


@pytest.mark.parametrize("value", [-1, "abc", 1.5, None, 1000001])
def test_create_with_invalid_reorder_level_returns_422(
    client, auth_headers, default_category_id, value
):
    response = create_product(
        client, auth_headers, default_category_id, reorder_level=value
    )

    assert response.status_code == 422
    assert client.get("/products").json()["total"] == 0


def test_create_accepts_reorder_level_zero(client, auth_headers, default_category_id):
    response = create_product(
        client, auth_headers, default_category_id, reorder_level=0
    )

    assert response.status_code == 201
    assert response.json()["reorder_level"] == 0


def test_patch_reorder_level_changes_only_that_field(
    client, auth_headers, default_category_id
):
    product = create_product(client, auth_headers, default_category_id).json()

    response = client.patch(
        f"/products/{product['id']}", headers=auth_headers, json={"reorder_level": 30}
    )

    assert response.status_code == 200
    assert response.json()["reorder_level"] == 30
    assert response.json()["name"] == "USB Cable"
    assert response.json()["stock_quantity"] == 10


@pytest.mark.parametrize("value", [-1, None, "abc"])
def test_patch_with_invalid_reorder_level_keeps_old_value(
    client, auth_headers, default_category_id, value
):
    product = create_product(client, auth_headers, default_category_id).json()

    response = client.patch(
        f"/products/{product['id']}",
        headers=auth_headers,
        json={"reorder_level": value},
    )

    assert response.status_code == 422
    assert client.get(f"/products/{product['id']}").json()["reorder_level"] == 5


def test_low_stock_uses_each_products_own_reorder_level(
    client, auth_headers, default_category_id
):
    # Same stock (10): a pen is fine, a charger is an emergency.
    create_product(
        client,
        auth_headers,
        default_category_id,
        sku="STA-0001",
        name="Gel Pen",
        reorder_level=5,
    )
    create_product(
        client,
        auth_headers,
        default_category_id,
        sku="ELE-0002",
        name="Phone Charger",
        reorder_level=20,
    )

    body = client.get("/reports/inventory-summary").json()

    assert [item["sku"] for item in body["low_stock"]] == ["ELE-0002"]


def test_explicit_threshold_overrides_every_reorder_level(
    client, auth_headers, default_category_id
):
    create_product(
        client,
        auth_headers,
        default_category_id,
        sku="STA-0001",
        name="Gel Pen",
        reorder_level=5,
    )
    create_product(
        client,
        auth_headers,
        default_category_id,
        sku="ELE-0002",
        name="Phone Charger",
        reorder_level=20,
    )

    low = client.get("/reports/inventory-summary?threshold=5").json()
    high = client.get("/reports/inventory-summary?threshold=11").json()

    assert low["low_stock"] == []
    assert {item["sku"] for item in high["low_stock"]} == {"STA-0001", "ELE-0002"}


def test_reorder_level_zero_is_never_low_stock(
    client, auth_headers, default_category_id
):
    create_product(
        client, auth_headers, default_category_id, stock_quantity=0, reorder_level=0
    )

    body = client.get("/reports/inventory-summary").json()

    assert body["low_stock"] == []
    assert body["out_of_stock_count"] == 1
