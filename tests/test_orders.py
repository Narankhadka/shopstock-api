import pytest


# ---------- Helpers ----------


def place_order(client, auth_headers, items, **overrides):
    payload = {
        "customer_name": "Anita Sharma",
        "customer_phone": "9841234567",
        "items": items,
    }
    payload.update(overrides)
    return client.post("/orders", headers=auth_headers, json=payload)


def stock_of(client, product_id):
    return client.get(f"/products/{product_id}").json()["stock_quantity"]


def movements_of(client, product_id):
    url = f"/products/{product_id}/stock-movements?page_size=50"
    return client.get(url).json()["items"]


def total_orders(client):
    return client.get("/orders").json()["total"]


def set_status(client, auth_headers, order_id, status):
    return client.patch(
        f"/orders/{order_id}/status", headers=auth_headers, json={"status": status}
    )


PATH_TO_STATUS = {
    "pending": [],
    "confirmed": ["confirmed"],
    "delivered": ["confirmed", "delivered"],
    "cancelled": ["cancelled"],
}


def order_in_status(client, auth_headers, product, status):
    line = [{"product_id": product["id"], "quantity": 1}]
    order = place_order(client, auth_headers, line).json()
    for step in PATH_TO_STATUS[status]:
        assert set_status(client, auth_headers, order["id"], step).status_code == 200
    return order


# ---------- Create order: success ----------


def test_create_order_returns_201_with_correct_total_and_pending_status(
    client, auth_headers, make_product
):
    pen = make_product(sku="STA-0001", name="Gel Pen", price=450, stock_quantity=10)
    cable = make_product(sku="ELE-0001", name="USB Cable", price=350, stock_quantity=10)

    response = place_order(
        client,
        auth_headers,
        [
            {"product_id": pen["id"], "quantity": 2},
            {"product_id": cable["id"], "quantity": 1},
        ],
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    assert body["total_amount"] == 1250.0
    assert [item["line_total"] for item in body["items"]] == [900.0, 350.0]


def test_create_order_deducts_stock_and_writes_order_movement(
    client, make_product, make_order
):
    product = make_product(stock_quantity=10)

    order = make_order([{"product_id": product["id"], "quantity": 3}])

    assert stock_of(client, product["id"]) == 7
    order_movements = [
        m for m in movements_of(client, product["id"]) if m["reason"] == "order"
    ]
    assert len(order_movements) == 1
    assert order_movements[0]["change"] == -3
    assert order_movements[0]["order_id"] == order["id"]


def test_create_order_for_exact_remaining_stock_leaves_zero(
    client, auth_headers, make_product
):
    product = make_product(stock_quantity=4)

    response = place_order(client, auth_headers, [{"product_id": product["id"], "quantity": 4}])

    assert response.status_code == 201
    assert stock_of(client, product["id"]) == 0


# ---------- Create order: failures leave the database unchanged ----------


def test_order_with_insufficient_stock_on_later_line_changes_nothing(
    client, auth_headers, make_product
):
    plenty = make_product(sku="ELE-0001", stock_quantity=5)
    scarce = make_product(sku="ELE-0002", stock_quantity=1)

    response = place_order(
        client,
        auth_headers,
        [
            {"product_id": plenty["id"], "quantity": 2},
            {"product_id": scarce["id"], "quantity": 5},
        ],
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INSUFFICIENT_STOCK"
    assert "Available: 1" in response.json()["error"]["message"]
    assert stock_of(client, plenty["id"]) == 5
    assert stock_of(client, scarce["id"]) == 1
    assert movements_of(client, plenty["id"]) == []
    assert total_orders(client) == 0


def test_order_for_the_last_unit_twice_rejects_the_second_order(
    client, auth_headers, make_product
):
    product = make_product(stock_quantity=1)
    line = [{"product_id": product["id"], "quantity": 1}]

    first = place_order(client, auth_headers, line)
    second = place_order(client, auth_headers, line)

    assert first.status_code == 201
    assert second.status_code == 409
    assert stock_of(client, product["id"]) == 0
    assert total_orders(client) == 1


def test_order_with_unknown_product_on_later_line_returns_404_and_changes_nothing(
    client, auth_headers, make_product
):
    real = make_product(stock_quantity=5)

    response = place_order(
        client,
        auth_headers,
        [
            {"product_id": real["id"], "quantity": 1},
            {"product_id": 9999, "quantity": 1},
        ],
    )

    assert response.status_code == 404
    assert stock_of(client, real["id"]) == 5
    assert total_orders(client) == 0


def test_order_with_inactive_product_is_rejected_and_changes_nothing(
    client, auth_headers, make_product
):
    product = make_product(stock_quantity=5)
    client.delete(f"/products/{product['id']}", headers=auth_headers)

    response = place_order(client, auth_headers, [{"product_id": product["id"], "quantity": 1}])

    assert response.status_code == 409
    assert stock_of(client, product["id"]) == 5
    assert total_orders(client) == 0


# ---------- Create order: validation ----------


@pytest.mark.parametrize("quantity", [0, -1, 101])
def test_order_with_invalid_quantity_returns_422(client, auth_headers, make_product, quantity):
    product = make_product(stock_quantity=100)

    response = place_order(client, auth_headers, [{"product_id": product["id"], "quantity": quantity}])

    assert response.status_code == 422
    assert stock_of(client, product["id"]) == 100


@pytest.mark.parametrize("quantity", [1, 100])
def test_order_with_boundary_quantity_is_accepted(client, auth_headers, make_product, quantity):
    product = make_product(stock_quantity=100)

    response = place_order(client, auth_headers, [{"product_id": product["id"], "quantity": quantity}])

    assert response.status_code == 201


def test_order_with_no_items_returns_422(client, auth_headers):
    response = place_order(client, auth_headers, [])

    assert response.status_code == 422


def test_order_with_21_items_returns_422(client, auth_headers, make_product):
    products = [make_product(sku=f"ELE-{n:04d}", stock_quantity=1) for n in range(21)]
    items = [{"product_id": p["id"], "quantity": 1} for p in products]

    response = place_order(client, auth_headers, items)

    assert response.status_code == 422
    assert total_orders(client) == 0


def test_order_with_20_items_is_accepted(client, auth_headers, make_product):
    products = [make_product(sku=f"ELE-{n:04d}", stock_quantity=1) for n in range(20)]
    items = [{"product_id": p["id"], "quantity": 1} for p in products]

    response = place_order(client, auth_headers, items)

    assert response.status_code == 201


def test_order_with_same_product_twice_returns_422(client, auth_headers, make_product):
    product = make_product(stock_quantity=10)
    line = {"product_id": product["id"], "quantity": 1}

    response = place_order(client, auth_headers, [line, line])

    assert response.status_code == 422
    assert stock_of(client, product["id"]) == 10


@pytest.mark.parametrize(
    "phone",
    ["1234567890", "9641234567", "984123456", "98412345678", "98412abc90", ""],
)
def test_order_with_invalid_phone_returns_422(client, auth_headers, make_product, phone):
    product = make_product(stock_quantity=5)

    response = place_order(
        client, auth_headers, [{"product_id": product["id"], "quantity": 1}], customer_phone=phone
    )

    assert response.status_code == 422
    assert total_orders(client) == 0


@pytest.mark.parametrize("phone", ["9741234567", "9841234567"])
def test_order_with_valid_nepali_phone_is_accepted(client, auth_headers, make_product, phone):
    product = make_product(stock_quantity=5)

    response = place_order(
        client, auth_headers, [{"product_id": product["id"], "quantity": 1}], customer_phone=phone
    )

    assert response.status_code == 201


def test_order_ignores_prices_and_total_sent_by_the_client(client, auth_headers, make_product):
    product = make_product(price=350, stock_quantity=5)

    response = client.post(
        "/orders",
        headers=auth_headers,
        json={
            "customer_name": "Anita Sharma",
            "customer_phone": "9841234567",
            "total_amount": 1,
            "items": [{"product_id": product["id"], "quantity": 2, "unit_price": 1}],
        },
    )

    assert response.status_code in (201, 422)
    if response.status_code == 201:
        assert response.json()["total_amount"] == 700.0


# ---------- Price snapshot and reading orders ----------


def test_price_change_after_ordering_does_not_change_the_stored_order(
    client, auth_headers, make_product, make_order
):
    product = make_product(price=350, stock_quantity=5)
    order = make_order([{"product_id": product["id"], "quantity": 2}])

    client.patch(f"/products/{product['id']}", headers=auth_headers, json={"price": 999})

    saved = client.get(f"/orders/{order['id']}").json()
    assert saved["items"][0]["unit_price"] == 350.0
    assert saved["total_amount"] == 700.0


def test_get_order_returns_what_was_created(client, make_product, make_order):
    product = make_product(stock_quantity=5)
    order = make_order([{"product_id": product["id"], "quantity": 2}])

    response = client.get(f"/orders/{order['id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == order["id"]
    assert body["total_amount"] == order["total_amount"]
    assert body["items"][0]["product_id"] == product["id"]
    assert body["items"][0]["quantity"] == 2


def test_get_unknown_order_returns_404(client):
    response = client.get("/orders/9999")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_list_orders_filters_by_status_and_reports_total(
    client, auth_headers, make_product, make_order
):
    product = make_product(stock_quantity=10)
    line = [{"product_id": product["id"], "quantity": 1}]
    make_order(line)
    cancelled = make_order(line)
    set_status(client, auth_headers, cancelled["id"], "cancelled")

    response = client.get("/orders?status=cancelled")

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["id"] == cancelled["id"]


# ---------- Status transitions ----------


@pytest.mark.parametrize(
    "start, target",
    [
        ("pending", "confirmed"),
        ("pending", "cancelled"),
        ("confirmed", "delivered"),
        ("confirmed", "cancelled"),
    ],
)
def test_valid_status_transition_returns_200(client, auth_headers, make_product, start, target):
    product = make_product(stock_quantity=5)
    order = order_in_status(client, auth_headers, product, start)

    response = set_status(client, auth_headers, order["id"], target)

    assert response.status_code == 200
    assert response.json()["status"] == target


@pytest.mark.parametrize(
    "start, target",
    [
        ("pending", "delivered"),
        ("pending", "pending"),
        ("confirmed", "pending"),
        ("confirmed", "confirmed"),
        ("delivered", "pending"),
        ("delivered", "confirmed"),
        ("delivered", "cancelled"),
        ("delivered", "delivered"),
        ("cancelled", "pending"),
        ("cancelled", "confirmed"),
        ("cancelled", "delivered"),
        ("cancelled", "cancelled"),
    ],
)
def test_invalid_status_transition_returns_409_and_keeps_status(
    client, auth_headers, make_product, start, target
):
    product = make_product(stock_quantity=5)
    order = order_in_status(client, auth_headers, product, start)

    response = set_status(client, auth_headers, order["id"], target)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INVALID_TRANSITION"
    assert client.get(f"/orders/{order['id']}").json()["status"] == start


def test_status_change_with_unknown_status_returns_422(client, auth_headers, make_product, make_order):
    product = make_product(stock_quantity=5)
    order = make_order([{"product_id": product["id"], "quantity": 1}])

    response = set_status(client, auth_headers, order["id"], "shipped")

    assert response.status_code == 422


def test_status_change_on_unknown_order_returns_404(client, auth_headers):
    response = set_status(client, auth_headers, 9999, "confirmed")

    assert response.status_code == 404


# ---------- Cancel restores stock ----------


def test_cancel_restores_stock_and_keeps_both_movements(
    client, auth_headers, make_product, make_order
):
    product = make_product(stock_quantity=10)
    order = make_order([{"product_id": product["id"], "quantity": 4}])

    response = set_status(client, auth_headers, order["id"], "cancelled")

    assert response.status_code == 200
    assert stock_of(client, product["id"]) == 10
    reasons = sorted(m["reason"] for m in movements_of(client, product["id"]))
    assert reasons == ["order", "order_cancelled"]


def test_cancelling_twice_does_not_restore_stock_twice(
    client, auth_headers, make_product, make_order
):
    product = make_product(stock_quantity=10)
    order = make_order([{"product_id": product["id"], "quantity": 4}])

    first = set_status(client, auth_headers, order["id"], "cancelled")
    second = set_status(client, auth_headers, order["id"], "cancelled")

    assert first.status_code == 200
    assert second.status_code == 409
    assert stock_of(client, product["id"]) == 10
    assert len(movements_of(client, product["id"])) == 2


# ---------- Soft delete blocked by open orders ----------


def test_product_in_open_order_cannot_be_deleted_until_order_is_cancelled(
    client, auth_headers, make_product, make_order
):
    product = make_product(stock_quantity=5)
    order = make_order([{"product_id": product["id"], "quantity": 1}])

    blocked = client.delete(f"/products/{product['id']}", headers=auth_headers)
    set_status(client, auth_headers, order["id"], "cancelled")
    allowed = client.delete(f"/products/{product['id']}", headers=auth_headers)

    assert blocked.status_code == 409
    assert allowed.status_code == 204


def test_deleted_product_still_shows_in_old_order(client, auth_headers, make_product, make_order):
    product = make_product(stock_quantity=5)
    order = make_order([{"product_id": product["id"], "quantity": 1}])
    set_status(client, auth_headers, order["id"], "cancelled")
    client.delete(f"/products/{product['id']}", headers=auth_headers)

    response = client.get(f"/orders/{order['id']}")

    assert response.status_code == 200
    assert response.json()["items"][0]["product_name"] == product["name"]


# ---------- Stock adjustments ----------


def test_stock_adjustment_updates_stock_and_writes_movement(client, auth_headers, make_product):
    product = make_product(stock_quantity=10)

    response = client.post(
        f"/products/{product['id']}/stock-adjustments",
        headers=auth_headers,
        json={"change": 5, "reason": "restock"},
    )

    assert response.status_code == 201
    assert response.json()["previous_quantity"] == 10
    assert response.json()["new_quantity"] == 15
    assert stock_of(client, product["id"]) == 15
    assert movements_of(client, product["id"])[0]["reason"] == "restock"


def test_stock_adjustment_down_to_exactly_zero_is_allowed(client, auth_headers, make_product):
    product = make_product(stock_quantity=10)

    response = client.post(
        f"/products/{product['id']}/stock-adjustments",
        headers=auth_headers,
        json={"change": -10, "reason": "damaged"},
    )

    assert response.status_code == 201
    assert stock_of(client, product["id"]) == 0


def test_stock_adjustment_below_zero_returns_409_and_writes_no_movement(
    client, auth_headers, make_product
):
    product = make_product(stock_quantity=10)

    response = client.post(
        f"/products/{product['id']}/stock-adjustments",
        headers=auth_headers,
        json={"change": -11, "reason": "damaged"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INSUFFICIENT_STOCK"
    assert stock_of(client, product["id"]) == 10
    assert movements_of(client, product["id"]) == []


@pytest.mark.parametrize(
    "payload",
    [
        {"change": 0, "reason": "restock"},
        {"change": 1, "reason": "gift"},
        {"change": 1},
    ],
)
def test_invalid_stock_adjustment_returns_422(client, auth_headers, make_product, payload):
    product = make_product(stock_quantity=10)

    response = client.post(
        f"/products/{product['id']}/stock-adjustments", headers=auth_headers, json=payload
    )

    assert response.status_code == 422
    assert stock_of(client, product["id"]) == 10


def test_stock_adjustment_on_unknown_product_returns_404(client, auth_headers):
    response = client.post(
        "/products/9999/stock-adjustments",
        headers=auth_headers,
        json={"change": 1, "reason": "restock"},
    )

    assert response.status_code == 404


def test_stock_adjustment_on_inactive_product_returns_409(client, auth_headers, make_product):
    product = make_product(stock_quantity=10)
    client.delete(f"/products/{product['id']}", headers=auth_headers)

    response = client.post(
        f"/products/{product['id']}/stock-adjustments",
        headers=auth_headers,
        json={"change": 1, "reason": "restock"},
    )

    assert response.status_code == 409


def test_stock_history_adds_up_to_current_stock_after_a_mix_of_operations(
    client, auth_headers, make_product, make_order
):
    initial = 10
    product = make_product(stock_quantity=initial)
    url = f"/products/{product['id']}/stock-adjustments"
    client.post(url, headers=auth_headers, json={"change": 5, "reason": "restock"})
    client.post(url, headers=auth_headers, json={"change": -3, "reason": "damaged"})
    cancelled = make_order([{"product_id": product["id"], "quantity": 4}])
    set_status(client, auth_headers, cancelled["id"], "cancelled")
    make_order([{"product_id": product["id"], "quantity": 2}])

    movements = movements_of(client, product["id"])

    assert len(movements) == 5
    assert initial + sum(m["change"] for m in movements) == stock_of(client, product["id"])


# ---------- Inventory report ----------


def test_inventory_summary_matches_hand_calculated_numbers(
    client, auth_headers, make_product, make_category
):
    make_product(sku="ELE-0001", price=100, stock_quantity=10)
    make_product(sku="ELE-0002", price=250.50, stock_quantity=2)
    make_product(sku="ELE-0003", price=50, stock_quantity=0)
    hidden = make_product(sku="ELE-0004", price=1000, stock_quantity=100)
    client.delete(f"/products/{hidden['id']}", headers=auth_headers)
    make_category("Empty")

    body = client.get("/reports/inventory-summary?threshold=5").json()

    assert body["total_products"] == 3
    assert body["total_stock_units"] == 12
    assert float(body["total_stock_value"]) == 1501.0
    assert body["out_of_stock_count"] == 1
    assert [item["sku"] for item in body["low_stock"]] == ["ELE-0003", "ELE-0002"]
    categories = {c["category_name"]: c for c in body["categories"]}
    assert categories["Electronics"]["total_products"] == 3
    assert categories["Empty"]["total_products"] == 0
    assert categories["Empty"]["total_stock_units"] == 0


@pytest.mark.parametrize(
    "threshold, expected_skus",
    [(0, []), (1, ["ELE-0003"]), (2, ["ELE-0003"]), (3, ["ELE-0003", "ELE-0002"])],
)
def test_inventory_summary_low_stock_respects_threshold(
    client, make_product, threshold, expected_skus
):
    make_product(sku="ELE-0001", stock_quantity=10)
    make_product(sku="ELE-0002", stock_quantity=2)
    make_product(sku="ELE-0003", stock_quantity=0)

    body = client.get(f"/reports/inventory-summary?threshold={threshold}").json()

    assert [item["sku"] for item in body["low_stock"]] == expected_skus


def test_inventory_summary_with_negative_threshold_returns_422(client):
    response = client.get("/reports/inventory-summary?threshold=-1")

    assert response.status_code == 422


def test_inventory_summary_on_empty_database_does_not_crash(client):
    response = client.get("/reports/inventory-summary")

    assert response.status_code == 200
    body = response.json()
    assert body["total_products"] == 0
    assert body["total_stock_units"] == 0
    assert float(body["total_stock_value"]) == 0.0
    assert body["low_stock"] == []
