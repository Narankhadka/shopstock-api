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
