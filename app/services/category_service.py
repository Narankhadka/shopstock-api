import sqlite3


def list_categories(db: sqlite3.Connection) -> list[dict]:
    query = """
        SELECT
            c.id,
            c.name,
            COUNT(p.id) AS active_product_count
        FROM categories c
        LEFT JOIN products p
            ON c.id = p.category_id
            AND p.is_active = 1
        GROUP BY c.id, c.name
        ORDER BY c.name ASC
    """
    rows = db.execute(query).fetchall()
    return [dict(row) for row in rows]
