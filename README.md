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
