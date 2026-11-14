import sqlite3
from decimal import Decimal


def paisa_to_rupees(paisa: int) -> Decimal:
    return (Decimal(paisa) / Decimal(100)).quantize(Decimal("0.01"))


def get_inventory_summary(
    db: sqlite3.Connection,
    threshold: int | None = None,
) -> dict:
    if threshold is not None and threshold < 0:
        raise ValueError("threshold must be non-negative")

    summary = db.execute(
        """
        SELECT
            COUNT(*) AS total_products,
            COALESCE(SUM(stock_quantity), 0) AS total_stock_units,
            COALESCE(SUM(price * stock_quantity), 0) AS total_stock_value_paisa,
            COALESCE(
                SUM(CASE WHEN stock_quantity = 0 THEN 1 ELSE 0 END),
                0
            ) AS out_of_stock_count
        FROM products
        WHERE is_active = 1
        """
    ).fetchone()

    low_stock_rows = db.execute(
        """
        SELECT
            p.id,
            p.sku,
            p.name,
            c.name AS category_name,
            p.stock_quantity
        FROM products AS p
        JOIN categories AS c ON c.id = p.category_id
        WHERE p.is_active = 1
        AND p.stock_quantity < COALESCE(?, p.reorder_level)
        ORDER BY p.stock_quantity ASC, p.id ASC
        """,
        (threshold,),
    ).fetchall()

    category_rows = db.execute(
        """
        SELECT
            c.id AS category_id,
            c.name AS category_name,
            COUNT(p.id) AS total_products,
            COALESCE(SUM(p.stock_quantity), 0) AS total_stock_units,
            COALESCE(SUM(p.price * p.stock_quantity), 0)
                AS total_stock_value_paisa,
            COALESCE(
                SUM(CASE WHEN p.stock_quantity = 0 THEN 1 ELSE 0 END),
                0
            ) AS out_of_stock_count
        FROM categories AS c
        LEFT JOIN products AS p
            ON p.category_id = c.id
           AND p.is_active = 1
        GROUP BY c.id, c.name
        ORDER BY c.id ASC
        """
    ).fetchall()

    return {
        "total_products": summary["total_products"],
        "total_stock_units": summary["total_stock_units"],
        "total_stock_value": paisa_to_rupees(summary["total_stock_value_paisa"]),
        "out_of_stock_count": summary["out_of_stock_count"],
        "low_stock": [dict(row) for row in low_stock_rows],
        "categories": [
            {
                "category_id": row["category_id"],
                "category_name": row["category_name"],
                "total_products": row["total_products"],
                "total_stock_units": row["total_stock_units"],
                "total_stock_value": paisa_to_rupees(row["total_stock_value_paisa"]),
                "out_of_stock_count": row["out_of_stock_count"],
            }
            for row in category_rows
        ],
    }
