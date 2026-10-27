import sqlite3


def list_products(db: sqlite3.Connection) -> list[dict]:
    rows = db.execute(
        "SELECT id, sku, name, category_id, price, stock_quantity, is_active "
        "FROM products WHERE is_active = 1 ORDER BY id"
    ).fetchall()

    products = []
    for row in rows:
        product = {
            "id": row["id"],
            "sku": row["sku"],
            "name": row["name"],
            "category_id": row["category_id"],
            "price": row["price"] / 100,
            "stock_quantity": row["stock_quantity"],
            "is_active": bool(row["is_active"]),
        }
        products.append(product)

    return products