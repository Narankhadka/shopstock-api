import sqlite3

from app.schemas.order import OrderCreate


def create_order(
    db: sqlite3.Connection,
    data: OrderCreate,
) -> dict:
    try:
        db.execute("BEGIN IMMEDIATE")

        total_amount = 0
        order_lines = []

        # 1. Validate all products and calculate prices
        for item in data.items:
            product = db.execute(
                """
                SELECT id, name, price, stock_quantity, is_active
                FROM products
                WHERE id = ?
                """,
                (item.product_id,),
            ).fetchone()

            if product is None:
                raise ValueError(f"Product {item.product_id} not found")

            if not product["is_active"]:
                raise ValueError(f"Product {item.product_id} is inactive")

            if product["stock_quantity"] < item.quantity:
                raise ValueError(
                    f"Insufficient stock for {product['name']}. "
                    f"Available: {product['stock_quantity']}, "
                    f"Requested: {item.quantity}"
                )

            unit_price = product["price"]
            line_total = unit_price * item.quantity

            total_amount += line_total

            order_lines.append(
                {
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "unit_price": unit_price,
                    "line_total": line_total,
                }
            )

        # 2. Create the order
        cursor = db.execute(
            """
            INSERT INTO orders
                (customer_name, customer_phone, total_amount)
            VALUES (?, ?, ?)
            """,
            (
                data.customer_name,
                data.customer_phone,
                total_amount,
            ),
        )

        order_id = cursor.lastrowid

        if order_id is None:
            raise RuntimeError("Failed to retrieve order ID")

        # 3. Insert items, deduct stock, and record movements
        for line in order_lines:
            db.execute(
                """
                INSERT INTO order_items
                    (order_id, product_id, quantity, unit_price)
                VALUES (?, ?, ?, ?)
                """,
                (
                    order_id,
                    line["product_id"],
                    line["quantity"],
                    line["unit_price"],
                ),
            )

            update_cursor = db.execute(
                """
                UPDATE products
                SET stock_quantity = stock_quantity - ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                  AND is_active = 1
                  AND stock_quantity >= ?
                """,
                (
                    line["quantity"],
                    line["product_id"],
                    line["quantity"],
                ),
            )

            if update_cursor.rowcount != 1:
                raise ValueError(
                    f"Stock update failed for product {line['product_id']}"
                )
            db.execute(
                """
                INSERT INTO stock_movements
                    (product_id, change, reason, order_id)
                VALUES (?, ?, 'order', ?)
                """,
                (
                    line["product_id"],
                    -line["quantity"],
                    order_id,
                ),
            )

        # 4. Get the order creation timestamp
        order = db.execute(
            """
            SELECT created_at
            FROM orders
            WHERE id = ?
            """,
            (order_id,),
        ).fetchone()

        if order is None:
            raise RuntimeError("Created order not found")

        created_at = order["created_at"]

        # 5. Commit everything together
        db.commit()

    except Exception:
        db.rollback()
        raise

    # 6. Return the API-ready response
    return {
        "id": order_id,
        "customer_name": data.customer_name,
        "customer_phone": data.customer_phone,
        "status": "pending",
        "total_amount": total_amount / 100,
        "items": [
            {
                "product_id": line["product_id"],
                "quantity": line["quantity"],
                "unit_price": line["unit_price"] / 100,
                "line_total": line["line_total"] / 100,
            }
            for line in order_lines
        ],
        "created_at": created_at,
    }
