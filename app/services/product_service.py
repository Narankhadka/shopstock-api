import sqlite3

from app.schemas.product import ProductCreate


class DuplicateSKUError(Exception):
    pass

def list_products(
    db: sqlite3.Connection,
    category_id: int | None = None,
    min_price:float | None = None,
    max_price: float | None = None,
    in_stock: bool | None = None,
    search:str     | None = None,
    include_inactive: bool = False,
    sort_by: str = "name",
    order: str = "asc",

    ) -> list[dict]:

    allowed_sort_columns = {
    "price": "price",
    "name": "name",
    "stock_quantity": "stock_quantity",
    "created_at": "created_at",
}
    if order not in ("asc","desc"):
        raise ValueError("Invalid order")

    if  sort_by not in allowed_sort_columns:
        raise ValueError("Invalid sort_by")

    conditions = ["1 = 1"]
    if not include_inactive:
        conditions.append("is_active = 1")

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

    if search:
        escaped_search = (
            search.replace("\\", "\\\\")
                  .replace("%", "\\%")
                  .replace("_", "\\_")
        )

        conditions.append("name LIKE ? ESCAPE '\\'")
        values.append(f"%{escaped_search}%")



    where = " AND ".join(conditions)
    sql = (
        "SELECT id, sku, name, category_id, price, stock_quantity, is_active "
        "FROM products WHERE " + where + f" ORDER BY {sort_by} {order.upper()}, id ASC" )
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

def get_product_by_id(db: sqlite3.Connection, product_id: int) -> dict | None:
    row = db.execute(
        "SELECT p.id, p.sku, p.name, p.category_id, c.name AS category_name, "
        "p.price, p.stock_quantity, p.is_active, "
        "p.created_at,p.updated_at "
        "FROM products p JOIN categories c ON c.id = p.category_id "
        "WHERE p.id = ?",
        (product_id,),
    ).fetchone()

    if row is None:
        return None

    return {
        "id": row["id"],
        "sku": row["sku"],
        "name": row["name"],
        "category_id": row["category_id"],
        "category_name": row["category_name"],
        "price": row["price"] / 100,
        "stock_quantity": row["stock_quantity"],
        "is_active": bool(row["is_active"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }

def get_product_by_sku(db: sqlite3.Connection, sku: str) -> dict | None:
    row = db.execute(
        "SELECT p.id, p.sku, p.name, p.category_id, c.name AS category_name, "
        "p.price, p.stock_quantity, p.is_active "
        "FROM products p JOIN categories c ON c.id = p.category_id "
        "WHERE p.sku = ?",
        (sku.upper(),),
    ).fetchone()

    if row is None:
        return None

    return {
        "id": row["id"],
        "sku": row["sku"],
        "name": row["name"],
        "category_id": row["category_id"],
        "category_name": row["category_name"],
        "price": row["price"] / 100,
        "stock_quantity": row["stock_quantity"],
        "is_active": bool(row["is_active"]),
    }

def category_exists(db: sqlite3.Connection, category_id: int) -> bool:
    row = db.execute(
        "SELECT 1 FROM categories WHERE id = ?",
        (category_id,)
    ).fetchone()

    return row is not None




def create_product(
    db: sqlite3.Connection,
    data: ProductCreate
) -> dict:

    if not category_exists(db, data.category_id):
        raise ValueError("Category does not exist")

    price_paisa = int(data.price * 100)

    try:
        cursor = db.execute(
            """
            INSERT INTO products
                (sku, name, category_id, price, stock_quantity)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                data.sku,
                data.name,
                data.category_id,
                price_paisa,
                data.stock_quantity,
            ),
        )

        product_id = cursor.lastrowid
        if product_id is None:
            raise RuntimeError("Failed to retrieve created product ID")
        db.commit()

    except sqlite3.IntegrityError as e:
        db.rollback()
        if "UNIQUE constraint failed: products.sku" in str(e):
            raise DuplicateSKUError(
                f"Product with SKU {data.sku} already exists"
            ) from e
        raise


    product = get_product_by_id(db, product_id)

    if product is None:
        raise RuntimeError("Created product could not be retrieved")

    return product
