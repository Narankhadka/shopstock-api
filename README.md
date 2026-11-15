# ShopStock API

A RESTful inventory and order management API built with FastAPI and SQLite. The application supports product and category management, stock adjustments, order processing, and inventory reporting.

## Project Overview

ShopStock API is a backend inventory management system designed to handle common inventory and order management operations.

### Key Features

- Product creation, updating, deactivation, and restoration
- Product search, filtering, sorting, and pagination
- Category management
- Stock adjustments and stock movement history
- Order creation and status management
- Automatic stock deduction and restoration during order operations
- Inventory summary and low-stock reporting
- API key authentication for write operations
- Consistent error responses and request logging
- Automated tests using pytest and FastAPI TestClient

### Technology Stack

- **Language:** Python
- **Framework:** FastAPI
- **Database:** SQLite
- **Validation:** Pydantic
- **Testing:** pytest, FastAPI TestClient
- **Code Quality:** Ruff

## Installation and Setup

### Prerequisites

- Python 3.13 or later
- Git

### 1. Clone the repository

```bash
git clone <repository-url>
cd shopstock-api
```

Replace `<repository-url>` with the actual GitHub repository URL.

### 2. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Update the configuration:

```env
DATABASE_PATH=shopstock.db
API_KEY=your-secret-api-key
LOW_STOCK_DEFAULT=5
DEBUG=false
```

| Variable | Description | Default |
|---|---|---|
| `DATABASE_PATH` | SQLite database file path | `shopstock.db` |
| `API_KEY` | API key required for protected operations | Required |
| `LOW_STOCK_DEFAULT` | Default low-stock setting | `5` |
| `DEBUG` | Debug configuration | `false` |

The `API_KEY` must not be empty. Use your own secret value instead of the example value.

### 5. Initialize the database

```bash
python -m scripts.init_db
```

This creates the database schema using `sql/schema.sql`.

### 6. Apply database migrations

```bash
python -m scripts.migrate
```

This applies any migration files that have not already been applied.

### 7. Insert sample data

```bash
python -m scripts.seed
```

The seed script inserts sample categories and products. Existing categories and products with duplicate SKUs are skipped, making the operation safe to repeat.

## Running the API

Start the development server:

```bash
uvicorn app.main:app --reload --no-access-log
```

The API will be available at:

- **API:** http://127.0.0.1:8000
- **Swagger UI:** http://127.0.0.1:8000/docs
- **ReDoc:** http://127.0.0.1:8000/redoc

Check API and database health:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "database": "connected"
}
```

## API Endpoints

All write operations require a valid API key through the `X-API-Key` request header.

### Health

| Method | Endpoint | Description | Authentication |
|---|---|---|---|
| GET | `/health` | Check API and database health | No |

### Products

| Method | Endpoint | Description | Authentication |
|---|---|---|---|
| GET | `/products` | List products with filtering, sorting, and pagination | No |
| GET | `/products/{product_id}` | Get product by ID | No |
| GET | `/products/sku/{sku}` | Get product by SKU | No |
| POST | `/products` | Create a product | API key |
| PATCH | `/products/{product_id}` | Update a product | API key |
| DELETE | `/products/{product_id}` | Deactivate a product | API key |
| POST | `/products/{product_id}/restore` | Restore a deactivated product | API key |
| POST | `/products/{product_id}/stock-adjustments` | Adjust product stock | API key |
| GET | `/products/{product_id}/stock-movements` | View product stock movement history | No |

### Categories

| Method | Endpoint | Description | Authentication |
|---|---|---|---|
| GET | `/categories` | List all product categories | No |

### Orders

| Method | Endpoint | Description | Authentication |
|---|---|---|---|
| POST | `/orders` | Create a new order | API key |
| GET | `/orders` | List orders with filters and pagination | No |
| GET | `/orders/{order_id}` | Get order details by ID | No |
| PATCH | `/orders/{order_id}/status` | Update order status | API key |

### Reports

| Method | Endpoint | Description | Authentication |
|---|---|---|---|
| GET | `/reports/inventory-summary` | Get inventory summary and low-stock report | No |

## Business Rules

### Product Management

- Product SKUs must follow the required format: three letters, a hyphen, and four digits.
- Product SKUs must be unique.
- Product names are validated before storage.
- Product prices are stored as integer paisa.
- Products can be deactivated and restored instead of being permanently deleted.
- Inactive products are excluded from normal product listings unless explicitly requested.

### Stock Management

- Stock quantities cannot become negative.
- Stock adjustments create stock movement records.
- Order creation deducts stock from the corresponding products.
- Cancelling an eligible order restores the deducted stock.
- Repeated cancellation must not restore stock more than once.
- Stock operations use database transactions to protect inventory consistency.

### Order Management

- Orders contain one or more product items.
- Order creation validates product availability and stock.
- Order status changes follow defined transition rules.
- Invalid status transitions return a conflict response.
- Cancelling an eligible order restores its reserved stock.

## Design Decisions

### Money Storage

Product prices and order amounts are stored as integer paisa instead of floating-point values.

For example:

- NPR 350.00 is stored as `35000`.
- NPR 12.50 is stored as `1250`.

This avoids floating-point precision problems during financial calculations.

### Database Transactions and Concurrency

SQLite is used as the database for this project.

Critical stock and order operations use explicit database transactions with `BEGIN IMMEDIATE`, followed by `COMMIT` or `ROLLBACK`.

Stock updates also use conditional SQL updates to prevent inventory from becoming negative.

This approach helps prevent concurrent requests from overselling available stock.

### Authentication

An API key is required for protected write operations.

The key is configured through the `API_KEY` environment variable and should not be committed to version control.

### Error Handling

The application uses centralized exception handlers to provide consistent error responses.

Different error codes distinguish validation failures, missing resources, conflicts, insufficient stock, and unexpected server errors.

### Timezone Convention

Database timestamps are stored in UTC using SQLite's `datetime('now')`.

API timestamps currently do not include an explicit timezone offset.

Nepal Standard Time (NPT) is UTC+05:45. Clients should treat database timestamps as UTC before converting them to the user's local timezone.

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

All database timestamps are stored in UTC using SQLite's `datetime('now')`.

API timestamps currently do not include an explicit timezone offset.

Nepal Standard Time (NPT) is UTC+05:45.

Clients should treat database timestamps as UTC before converting them to the user's local timezone.

## Error Handling and Logging

### Error Format

Every error uses the same response structure:

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Product with id 9999 not found"
  }
}
```

Validation errors (422) also include a `details` list with the field name and message.

The rejected input value is intentionally omitted so sensitive values, such as phone numbers, are not echoed back.

### Error Codes

| Error Code | HTTP Status | Description |
|---|---:|---|
| `NOT_FOUND` | 404 | Product, order, or category does not exist |
| `METHOD_NOT_ALLOWED` | 405 | Wrong HTTP method on a known route |
| `CONFLICT` | 409 | Duplicate SKU, inactive product, or similar conflicts |
| `INSUFFICIENT_STOCK` | 409 | Not enough stock available |
| `INVALID_TRANSITION` | 409 | Requested order status change is not allowed |
| `VALIDATION_ERROR` | 422 | Invalid request body or query parameter |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

### Logging

- Every request logs its method, path, status, and duration.
- Business events are logged with IDs: `order_created`, `order_status_changed`, `order_cancelled`, and `stock_adjusted`.
- Logs do not contain customer names, phone numbers, or the API key.
- Run the server with `--no-access-log` because Uvicorn's default access log prints the full query string, which can contain a phone number.

## Testing

Run all tests:

```bash
pytest
```

Each test uses a fresh temporary database, so the development database is never touched.

The API key for tests is configured in `tests/conftest.py`, so tests do not need a `.env` file.

Run tests in reverse or random order to check that they do not depend on each other:

```bash
pytest --test-order=reverse
pytest --test-order=random
```

Known limitation: `starlette.testclient` prints a deprecation warning asking for `httpx2`. It is not installed because it is not in the allowed packages.

### Code Quality

Run Ruff checks:

```bash
ruff check .
```

Check formatting:

```bash
ruff format --check .
```

### Mutation Check (Task 3.4)

I intentionally introduced three changes and confirmed that a test fails for each one:

- Removing the duplicate-SKU check fails `test_create_product_with_duplicate_sku_returns_409`.
- Flipping the sort direction fails `test_list_products_sorts_by_price_ascending_and_descending`.
- Removing the `min_price` filter fails `test_list_products_filters_by_price_range_including_boundaries`.

### What the Order Tests Found (Task 3.5)

The order and stock tests all passed on the first run, so they did not find a bug in the original implementation.

To check that they would catch a stock restoration bug, I changed the stock restore operation on cancellation from `+` to `-`.

Three tests failed:

- `test_cancel_restores_stock_and_keeps_both_movements`
- `test_cancelling_twice_does_not_restore_stock_twice`
- `test_stock_history_adds_up_to_current_stock_after_a_mix_of_operations`

The incorrect change was reverted.

### What Is Not Tested

`test_order_for_the_last_unit_twice_rejects_the_second_order` runs two orders one after another, not at the same time.

Protection against true concurrent overselling (`BEGIN IMMEDIATE` plus the conditional `UPDATE`) is not covered by an automated concurrency test.

## Reorder Level

Each product has its own `reorder_level`:

- Integer value between `0` and `1,000,000`
- Default value: `5`
- Accepted by `POST /products` and `PATCH /products/{id}`
- Returned in every product response

`null`, negative, and non-integer values return 422.

### Report Precedence

`GET /reports/inventory-summary` lists a product as low stock when:

```text
stock_quantity < reorder_level
```

If the caller passes `?threshold=N`, that number replaces every product's `reorder_level` for that request. An explicit threshold takes precedence.

`reorder_level = 0` means the product is never listed as low stock.

`LOW_STOCK_DEFAULT` in `.env` is not used by the report.

## Database Migrations

Migration files live in `sql/migrations/` and are applied in file-name order.

Run migrations using:

```bash
python -m scripts.migrate
```

Applied files are recorded in the `schema_migrations` table, so running the command again does not reapply previously completed migrations.

To check whether your local database is migrated:

```bash
sqlite3 shopstock.db "SELECT version, applied_at FROM schema_migrations;"
```

A fresh database created from `sql/schema.sql` already has the relevant column and migration record.

Always back up a database before applying migrations to a database containing important data.

## Code Structure Notes

Several service functions are longer than 40 lines. The reasons are:

- `create_order`, `update_order_status`, and `adjust_stock` each run one database transaction (`BEGIN IMMEDIATE` through `COMMIT` or `ROLLBACK`). Splitting them would move part of the transaction into other functions and make rollback behavior harder to follow. Stock protection against overselling depends on keeping this operation together.
- `list_products`, `get_order_by_id`, `get_inventory_summary`, and similar functions are longer mostly because of SQL strings and dictionaries built from database rows. They contain relatively little branching logic.

`list_orders` was split into smaller helpers (`_build_order_filters`, `_order_summary`) as an example of the same pattern.

## Lessons Learned

### 1. Validate Numeric Boundaries

**Symptom:** Extremely large numeric values in request parameters or request bodies can cause problems when passed to database operations.

**Root cause:** SQLite integer storage has a finite range. Accepting values beyond the supported range can result in database-level errors rather than a useful client validation response.

**Fix:** Apply explicit numeric boundaries to identifiers, pagination parameters, and stock-related inputs. Test unusually large values and verify they return 422 rather than 500.

### 2. Validate Text Input

**Symptom:** Product names containing control characters, such as newlines, tabs, or bell characters, should not be accepted as normal names.

**Root cause:** Basic string validation does not automatically reject every unwanted control character.

**Fix:** Validate product names before storing them and add tests for control characters.

### 3. Protect Stock Restoration

**Symptom:** An incorrect stock restoration operation during order cancellation can reduce stock instead of restoring it.

**Root cause:** The stock adjustment direction must be consistent with the operation being performed.

**Fix:** Keep stock restoration within the order cancellation transaction and test both the stock quantity and stock movement history.

## Known Limitations

- True concurrent order creation is not covered by an automated concurrency test.
- API timestamps do not currently include explicit timezone offsets.
- The application uses SQLite, which may not be the ideal database for a high-concurrency production workload.
- The test client currently produces a deprecation warning related to `httpx2`.
- `LOW_STOCK_DEFAULT` is configured but is not used by the inventory report, which uses product-specific reorder levels or an explicit threshold.

## What I'd Do Next

- Add automated tests for simultaneous order creation and stock contention.
- Add explicit timezone information to API timestamp responses.
- Evaluate PostgreSQL for deployments with higher concurrency requirements.
- Add database backup and recovery procedures.
- Improve deployment configuration, monitoring, and operational logging.
- Review and document a production migration strategy.
