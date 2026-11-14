import os
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = os.environ.get("DATABASE_PATH", str(BASE_DIR / "shopstock.db"))

CATEGORIES = [
    "Electronics",
    "Stationery",
    "Household",
    "Accessories",
    "Personal Care",
    "Seasonal",  # product nabhayeko category (empty)
]

# (sku, name, category_name, price_in_paisa, stock_quantity, is_active)
PRODUCTS = [
    # Electronics
    ("ELE-0001", "USB-C Cable 1m", "Electronics", 35000, 40, 1),
    ("ELE-0002", "Phone Charger 20W", "Electronics", 120000, 25, 1),
    ("ELE-0003", "Wired Earphones", "Electronics", 80000, 0, 1),
    ("ELE-0004", "Power Bank 10000mAh", "Electronics", 250000, 12, 1),
    ("ELE-0005", "Bluetooth Speaker", "Electronics", 350000, 8, 1),
    ("ELE-0006", "AA Batteries Pack (4)", "Electronics", 45000, 60, 1),
    ("ELE-0007", "Old Model Charger", "Electronics", 90000, 5, 0),
    ("ELE-0008", "Wireless Mouse", "Electronics", 150000, 0, 1),
    # Stationery
    ("STA-0001", "Notebook A5", "Stationery", 12000, 100, 1),
    ("STA-0002", "Ball Pen Blue", "Stationery", 1000, 200, 1),
    ("STA-0003", "Gel Pen Pack (10)", "Stationery", 45000, 35, 1),
    ("STA-0004", "Highlighter Set", "Stationery", 45000, 20, 1),
    ("STA-0005", "Stapler Small", "Stationery", 18000, 15, 1),
    ("STA-0006", "Sticky Notes", "Stationery", 45000, 30, 1),
    ("STA-0007", "Whiteboard Marker", "Stationery", 8000, 0, 1),
    ("STA-0008", "Old Diary 2020", "Stationery", 15000, 4, 0),
    ("STA-0009", "Pencil Box", "Stationery", 25000, 18, 1),
    # Household
    ("HOU-0001", "Steel Water Bottle", "Household", 85000, 0, 1),
    ("HOU-0002", "Plastic Bucket", "Household", 40000, 22, 1),
    ("HOU-0003", "Dish Scrub Pack", "Household", 15000, 50, 1),
    ("HOU-0004", "Broom", "Household", 30000, 14, 1),
    ("HOU-0005", "Food Container Set", "Household", 120000, 10, 1),
    ("HOU-0006", "Mosquito Racket", "Household", 85000, 9, 1),
    ("HOU-0007", "Discontinued Lamp", "Household", 95000, 3, 0),
    ("HOU-0008", "Door Mat", "Household", 35000, 17, 1),
    # Accessories
    ("ACC-0001", "Phone Cover Universal", "Accessories", 25000, 45, 1),
    ("ACC-0002", "Screen Protector", "Accessories", 15000, 70, 1),
    ("ACC-0003", "Laptop Sleeve 14in", "Accessories", 180000, 6, 1),
    ("ACC-0004", "Phone Stand", "Accessories", 30000, 0, 1),
    ("ACC-0005", "Cable Organizer", "Accessories", 10000, 35, 1),
    ("ACC-0006", "Old Phone Strap", "Accessories", 5000, 2, 0),
    # Personal Care
    ("PER-0001", "Hand Sanitizer 100ml", "Personal Care", 20000, 40, 1),
    ("PER-0002", "Face Mask Pack (10)", "Personal Care", 15000, 55, 1),
    ("PER-0003", "Pocket Tissue Pack", "Personal Care", 5000, 80, 1),
]


def seed() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    inserted = 0
    skipped = 0

    try:
        # Insert categories
        conn.executemany(
            """
            INSERT INTO categories (name)
            VALUES (?)
            ON CONFLICT(name) DO NOTHING
            """,
            [(name,) for name in CATEGORIES],
        )

        # Insert products
        for sku, name, category_name, price, stock, active in PRODUCTS:
            cursor = conn.execute(
                """
                INSERT INTO products (
                    sku,
                    name,
                    category_id,
                    price,
                    stock_quantity,
                    is_active
                )
                VALUES (
                    ?,
                    ?,
                    (SELECT id FROM categories WHERE name = ?),
                    ?,
                    ?,
                    ?
                )
                ON CONFLICT(sku) DO NOTHING
                """,
                (sku, name, category_name, price, stock, active),
            )

            if cursor.rowcount == 1:
                inserted += 1
            else:
                skipped += 1

        conn.commit()

    except sqlite3.Error as e:
        conn.rollback()
        print(f"Seed failed: {e}")
        raise

    finally:
        conn.close()

    print(f"Seed complete: {inserted} inserted, {skipped} skipped")


if __name__ == "__main__":
    seed()
