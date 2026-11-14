## Product Pagination

The `GET /products` endpoint supports pagination.

### Query Parameters

- `page`: Page number (default: `1`, minimum: `1`)
- `page_size`: Number of products per page (default: `10`, minimum: `1`, maximum: `50`)

### Example Request

```http
GET /products?page=1&page_size=10
```

### Example Response

```json
{
  "items": [],
  "total": 39,
  "page": 1,
  "page_size": 10,
  "total_pages": 4
}
```

### Breaking Change

Previously, `GET /products` returned a JSON array of products.

Now, it returns a JSON object containing:

- `items`: Products on the current page
- `total`: Total number of products matching the filters
- `page`: Current page number
- `page_size`: Number of products requested per page
- `total_pages`: Total number of pages

## Timestamp Convention

All database timestamps are stored in UTC using SQLite's
`datetime('now')`. API timestamps currently do not include
an explicit timezone offset.

Nepal Standard Time (NPT) is UTC+05:45.
Clients should treat database timestamps as UTC before
converting them to the user's local timezone.

## Error handling and logging

### Error format

Every error uses the same shape:

{"error": {"code": "NOT_FOUND", "message": "Product with id 9999 not found"}}

Validation errors (422) also include a `details` list with the field
name and message. The rejected input value is left out on purpose, so
phone numbers are never echoed back.

### Error codes

- NOT_FOUND (404): product, order or category does not exist
- METHOD_NOT_ALLOWED (405): wrong HTTP method on a known route
- CONFLICT (409): duplicate SKU, inactive product, and similar clashes
- INSUFFICIENT_STOCK (409): not enough stock
- INVALID_TRANSITION (409): order status change not allowed
- VALIDATION_ERROR (422): invalid request body or query parameter
- INTERNAL_ERROR (500): unexpected failure, nothing internal is shown

### Logging

- Every request logs method, path, status and duration.
- Business events are logged with IDs: order_created,
  order_status_changed, order_cancelled, stock_adjusted.
- Logs never contain customer names, phone numbers or the API key.
- Run the server with `--no-access-log`, because uvicorn's own access
  log prints the full query string, which can contain a phone number.

## Testing

Run all tests:

    pytest

Each test uses a fresh temporary database, so the development database is
never touched. The API key for tests is set in `tests/conftest.py`, so tests
do not need a `.env` file.

Run tests in reverse or random order to check they do not depend on each other:

    pytest --test-order=reverse
    pytest --test-order=random

Known limitation: `starlette.testclient` prints a deprecation warning asking
for `httpx2`. It is not installed because it is not in the allowed packages.

### Mutation check (Task 3.4)

I broke the code in three places and confirmed that a test fails each time:

- Removing the duplicate-SKU check fails `test_create_product_with_duplicate_sku_returns_409`.
- Flipping the sort direction fails `test_list_products_sorts_by_price_ascending_and_descending`.
- Removing the `min_price` filter fails `test_list_products_filters_by_price_range_including_boundaries`.

### What the order tests found (Task 3.5)

The order and stock tests all passed on the first run, so they did not find a bug in
my own code. To check that they would catch one, I changed the stock restore on cancel
from `+` to `-`. Three tests failed:

- `test_cancel_restores_stock_and_keeps_both_movements`
- `test_cancelling_twice_does_not_restore_stock_twice`
- `test_stock_history_adds_up_to_current_stock_after_a_mix_of_operations`

I then reverted the change.

### What is not tested

`test_order_for_the_last_unit_twice_rejects_the_second_order` runs two orders one after
the other, not at the same time. The protection against true concurrent overselling
(`BEGIN IMMEDIATE` plus the conditional `UPDATE`) is not covered by an automated test.


## Reorder level

Each product has its own `reorder_level` (integer, 0 to 1,000,000, default 5). It is
accepted by `POST /products` and `PATCH /products/{id}` and returned in every product
response. `null`, negative and non-integer values return 422.

**Report precedence.** `GET /reports/inventory-summary` lists a product as low stock
when `stock_quantity < reorder_level`. If the caller passes `?threshold=N`, that number
replaces every product's `reorder_level` for that request (an explicit value wins).
`reorder_level = 0` means the product is never listed as low stock. `LOW_STOCK_DEFAULT`
in `.env` is not used by the report.

### Migrations

Migration files live in `sql/migrations/` and are applied in file-name order:

```bash
python -m scripts.migrate
```

Applied files are recorded in the `schema_migrations` table, so running it twice does
nothing the second time. To check whether your local database is migrated:

```bash
sqlite3 shopstock.db "SELECT version, applied_at FROM schema_migrations;"
```

A fresh database made from `sql/schema.sql` already has the column and the record. Copy
the database file before migrating one you care about.
