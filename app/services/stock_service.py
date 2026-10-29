import sqlite3

from app.schemas.stock import StockAdjustmentIn


def adjust_stock(
    db: sqlite3.Connection,
    product_id: int,
    data: StockAdjustmentIn,
) -> dict:

    try:
        db.execute("BEGIN IMMEDIATE")

        product = db.execute(
            """
        SELECT id, stock_quantity, is_active
        FROM products
        WHERE id = ?
        """,
            (product_id,),
        ).fetchone()

        if product is None:
            raise ValueError("Product Not found")
        if not product["is_active"]:
            raise ValueError("Cannot adjust stock of an inactive product")

        previous_quantity = product["stock_quantity"]
        new_quantity = previous_quantity + data.change

        if new_quantity < 0:
            raise ValueError("Insufficient stock for adjustment")

        db.execute(
            """
            UPDATE products
            SET stock_quantity = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (new_quantity, product_id),
        )
        cursor = db.execute(
            """
            INSERT INTO stock_movements (product_id, change, reason)
            VALUES (?, ?, ?)
            """,
            (product_id, data.change, data.reason),
        )

        db.commit()

    except Exception:
        db.rollback()
        raise

    movement_id = cursor.lastrowid

    if movement_id is None:
        raise RuntimeError("Failed to retrieve stock movement ID")

    movement = db.execute(
        """
    SELECT created_at
    FROM stock_movements
    WHERE id = ?
    """,
        (movement_id,),
    ).fetchone()

    if movement is None:
        raise RuntimeError("Stock movement not found")

    return {
        "product_id": product_id,
        "previous_quantity": previous_quantity,
        "change": data.change,
        "new_quantity": new_quantity,
        "reason": data.reason,
        "created_at": movement["created_at"],
    }


def list_stock_movements(
    db: sqlite3.Connection,
    product_id: int,
    page: int = 1,
    page_size: int = 10,
) -> dict:

    offset = (page - 1) * page_size

    product = db.execute(
        "SELECT id FROM products WHERE id = ?",
        (product_id,),
    ).fetchone()

    if product is None:
        raise ValueError("Product Not found")
    total = db.execute(
        "SELECT COUNT(*) FROM stock_movements WHERE product_id = ?",
        (product_id,),
    ).fetchone()[0]

    total_pages = (total + page_size - 1) // page_size

    rows = db.execute(
        """
        SELECT id, product_id, change, reason, order_id, created_at
        FROM stock_movements
        WHERE product_id = ?
        ORDER BY created_at DESC, id DESC
        LIMIT ? OFFSET ?
        """,
        (product_id, page_size, offset),
    ).fetchall()

    return {
        "items": [dict(row) for row in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }
