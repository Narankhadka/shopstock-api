import sqlite3


def list_products(
    db: sqlite3.Connection,
    category_id: int | None = None,
    min_price:float | None = None,
    max_price: float | None = None,
    in_stock: bool | None = None,
    ) -> list[dict]:
    
    conditions = ["is_active = 1"]
    values = []

    if category_id is not None:
        conditions.append("category_id = ?")
        values.append(category_id)
    
    if min_price is not None: 
        conditions.append("price >=?")
        values.append(round(min_price * 100))
    
    if max_price is not None: 
        conditions.append("price <=?")
        values.append(round(max_price * 100))
    
    if in_stock is True: 
        conditions.append("stock_quantity > 0")
    elif in_stock is False:
        conditions.append("stock_quantity = 0")
        
        

    where = " AND ".join(conditions)
    sql = (
        "SELECT id, sku, name, category_id, price, stock_quantity, is_active "
        "FROM products WHERE " + where + " ORDER BY id"
    )
    rows = db.execute(sql, values).fetchall()

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