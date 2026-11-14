import pytest


def product_payload(category_id, **overrides):
    payload = {
        "sku": "ELE-0001",
        "name": "USB Cable",
        "category_id": category_id,
        "price": 350.00,
        "stock_quantity": 10,
    }
    payload.update(overrides)
    return payload


# ---------- Create ----------


def test_create_product_returns_201_and_is_visible(
    client, auth_headers, default_category_id
):
    response = client.post(
        "/products",
        headers=auth_headers,
        json=product_payload(default_category_id, name="  USB Cable 1m  "),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "USB Cable 1m"
    assert body["is_active"] is True
    assert client.get(f"/products/{body['id']}").status_code == 200


def test_create_product_with_duplicate_sku_returns_409(
    client, auth_headers, default_category_id, make_product
):
    make_product(sku="ELE-0001")

    response = client.post(
        "/products", headers=auth_headers, json=product_payload(default_category_id)
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"
    assert client.get("/products").json()["total"] == 1


def test_create_product_with_nonexistent_category_returns_404(client, auth_headers):
    response = client.post(
        "/products", headers=auth_headers, json=product_payload(9999)
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


@pytest.mark.parametrize(
    "field, value",
    [
        ("sku", "abc-12"),
        ("sku", "ELE-12"),
        ("price", 0),
        ("price", -5),
        ("price", 12.345),
        ("stock_quantity", -1),
        ("name", "a"),
        ("name", "   "),
    ],
)
def test_create_product_with_invalid_field_returns_422(
    client, auth_headers, default_category_id, field, value
):
    response = client.post(
        "/products",
        headers=auth_headers,
        json=product_payload(default_category_id, **{field: value}),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert client.get("/products").json()["total"] == 0


@pytest.mark.parametrize(
    "field, value",
    [
        ("price", 0.01),
        ("price", 1000000),
        ("name", "ab"),
        ("name", "a" * 100),
    ],
)
def test_create_product_accepts_boundary_values(
    client, auth_headers, default_category_id, field, value
):
    response = client.post(
        "/products",
        headers=auth_headers,
        json=product_payload(default_category_id, **{field: value}),
    )

    assert response.status_code == 201


@pytest.mark.parametrize(
    "field, value",
    [
        ("price", 1000000.01),
        ("name", "a" * 101),
    ],
)
def test_create_product_rejects_values_just_over_the_limit(
    client, auth_headers, default_category_id, field, value
):
    response = client.post(
        "/products",
        headers=auth_headers,
        json=product_payload(default_category_id, **{field: value}),
    )

    assert response.status_code == 422


# ---------- Get ----------


def test_get_product_by_id_returns_product_with_category_name(client, make_product):
    product = make_product(sku="ELE-0007")

    response = client.get(f"/products/{product['id']}")

    assert response.status_code == 200
    assert response.json()["sku"] == "ELE-0007"
    assert response.json()["category_name"] == "Electronics"


def test_get_product_with_unknown_id_returns_404(client):
    response = client.get("/products/9999")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_get_product_by_sku_returns_product(client, make_product):
    product = make_product(sku="ELE-0007")

    response = client.get("/products/sku/ELE-0007")

    assert response.status_code == 200
    assert response.json()["id"] == product["id"]


def test_get_product_with_unknown_sku_returns_404(client):
    response = client.get("/products/sku/ABC-9999")

    assert response.status_code == 404


def test_get_product_with_malformed_sku_returns_422(client):
    response = client.get("/products/sku/xyz")

    assert response.status_code == 422


def test_get_product_with_non_numeric_id_returns_422(client):
    response = client.get("/products/abc")

    assert response.status_code == 422


# ---------- List: filters, sorting, pagination ----------


def test_list_products_filters_by_category(client, make_product, make_category):
    stationery_id = make_category("Stationery")
    make_product(sku="ELE-0001")
    pen = make_product(sku="STA-0001", name="Gel Pen", category_id=stationery_id)

    response = client.get(f"/products?category_id={stationery_id}")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"]] == [pen["id"]]
    assert response.json()["total"] == 1


def test_list_products_filters_by_price_range_including_boundaries(
    client, make_product
):
    make_product(sku="ELE-0001", price=100)
    mid = make_product(sku="ELE-0002", price=200)
    high = make_product(sku="ELE-0003", price=300)
    make_product(sku="ELE-0004", price=400)

    response = client.get("/products?min_price=200&max_price=300")

    ids = {item["id"] for item in response.json()["items"]}
    assert ids == {mid["id"], high["id"]}


def test_list_products_in_stock_hides_zero_stock(client, make_product):
    in_stock = make_product(sku="ELE-0001", stock_quantity=5)
    make_product(sku="ELE-0002", stock_quantity=0)

    response = client.get("/products?in_stock=true")

    assert [item["id"] for item in response.json()["items"]] == [in_stock["id"]]


@pytest.mark.parametrize("term", ["pen", "PEN", "Pen"])
def test_list_products_search_is_case_insensitive(client, make_product, term):
    pen = make_product(sku="STA-0001", name="Gel Pen")
    make_product(sku="ELE-0001", name="USB Cable")

    response = client.get(f"/products?search={term}")

    assert [item["id"] for item in response.json()["items"]] == [pen["id"]]


def test_list_products_with_no_match_returns_200_and_empty_list(client, make_product):
    make_product()

    response = client.get("/products?search=zzzz")

    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["total"] == 0


def test_list_products_sorts_by_price_ascending_and_descending(client, make_product):
    make_product(sku="ELE-0001", price=100)
    make_product(sku="ELE-0002", price=300)
    make_product(sku="ELE-0003", price=200)

    asc = client.get("/products?sort_by=price&order=asc").json()["items"]
    desc = client.get("/products?sort_by=price&order=desc").json()["items"]

    assert [item["price"] for item in asc] == [100, 200, 300]
    assert [item["price"] for item in desc] == [300, 200, 100]


def test_list_products_with_invalid_sort_by_returns_422(client):
    response = client.get("/products?sort_by=price;DROP TABLE products")

    assert response.status_code == 422
    assert client.get("/products").status_code == 200


def test_list_products_with_min_price_above_max_price_returns_422(client):
    response = client.get("/products?min_price=500&max_price=100")

    assert response.status_code == 422


def test_list_products_pagination_returns_every_product_exactly_once(
    client, make_product
):
    for number in range(25):
        make_product(sku=f"ELE-{number:04d}", price=100)  # equal prices on purpose

    seen_ids = []
    for page in (1, 2, 3):
        body = client.get(f"/products?sort_by=price&page={page}&page_size=10").json()
        seen_ids.extend(item["id"] for item in body["items"])

    assert len(seen_ids) == 25
    assert len(set(seen_ids)) == 25
    assert body["total"] == 25
    assert body["total_pages"] == 3


# ---------- Patch ----------


def test_patch_product_changes_only_the_sent_field(client, auth_headers, make_product):
    product = make_product(sku="ELE-0001", name="USB Cable", price=350)

    response = client.patch(
        f"/products/{product['id']}", headers=auth_headers, json={"price": 399.00}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["price"] == 399.00
    assert body["name"] == "USB Cable"
    assert body["category_id"] == product["category_id"]


def test_patch_unknown_product_returns_404(client, auth_headers):
    response = client.patch("/products/9999", headers=auth_headers, json={"price": 10})

    assert response.status_code == 404


def test_patch_with_empty_body_is_rejected(client, auth_headers, make_product):
    product = make_product()

    response = client.patch(f"/products/{product['id']}", headers=auth_headers, json={})

    assert response.status_code in (400, 422)


def test_patch_cannot_change_sku(client, auth_headers, make_product):
    product = make_product(sku="ELE-0001")

    client.patch(
        f"/products/{product['id']}", headers=auth_headers, json={"sku": "ELE-9999"}
    )

    assert client.get(f"/products/{product['id']}").json()["sku"] == "ELE-0001"


# ---------- Soft delete and restore ----------


def test_delete_product_hides_it_from_default_list_but_keeps_the_row(
    client, auth_headers, make_product
):
    product = make_product()

    response = client.delete(f"/products/{product['id']}", headers=auth_headers)

    assert response.status_code == 204
    assert client.get("/products").json()["total"] == 0
    assert client.get("/products?include_inactive=true").json()["total"] == 1
    assert client.get(f"/products/{product['id']}").json()["is_active"] is False


def test_deleted_product_is_rejected_in_new_orders(client, auth_headers, make_product):
    product = make_product(stock_quantity=5)
    client.delete(f"/products/{product['id']}", headers=auth_headers)

    response = client.post(
        "/orders",
        headers=auth_headers,
        json={
            "customer_name": "Anita Sharma",
            "customer_phone": "9841234567",
            "items": [{"product_id": product["id"], "quantity": 1}],
        },
    )

    assert response.status_code == 409
    assert client.get(f"/products/{product['id']}").json()["stock_quantity"] == 5


def test_delete_product_in_pending_order_returns_409(
    client, auth_headers, make_product, make_order
):
    product = make_product(stock_quantity=5)
    make_order([{"product_id": product["id"], "quantity": 1}])

    response = client.delete(f"/products/{product['id']}", headers=auth_headers)

    assert response.status_code == 409
    assert client.get(f"/products/{product['id']}").json()["is_active"] is True


def test_restore_makes_a_deleted_product_visible_again(
    client, auth_headers, make_product
):
    product = make_product()
    client.delete(f"/products/{product['id']}", headers=auth_headers)

    response = client.post(f"/products/{product['id']}/restore", headers=auth_headers)

    assert response.status_code == 204
    assert client.get("/products").json()["total"] == 1


def test_restore_an_already_active_product_returns_409(
    client, auth_headers, make_product
):
    product = make_product()

    response = client.post(f"/products/{product['id']}/restore", headers=auth_headers)

    assert response.status_code == 409


# ---------- Auth ----------


@pytest.mark.parametrize(
    "method, url",
    [
        ("post", "/products"),
        ("patch", "/products/1"),
        ("delete", "/products/1"),
        ("post", "/products/1/restore"),
        ("post", "/products/1/stock-adjustments"),
    ],
)
def test_write_endpoints_without_api_key_return_401(client, method, url):
    response = client.request(method, url, json={})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_write_endpoint_with_wrong_api_key_returns_403(client, default_category_id):
    response = client.post(
        "/products",
        headers={"X-API-Key": "wrong-key"},
        json=product_payload(default_category_id),
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"
