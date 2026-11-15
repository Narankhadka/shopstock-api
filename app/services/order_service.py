import logging
import sqlite3

from app.exceptions import (
    ConflictError,
    InsufficientStockError,
    InvalidTransitionError,
    NotFoundError,
)
from app.schemas.order import OrderCreate, OrderStatusUpdate

ALLOWED_TRANSITIONS = {
    "pending": {"confirmed", "cancelled"},
    "confirmed": {"delivered", "cancelled"},
    "delivered": set(),
    "cancelled": set(),
}
logger = logging.getLogger(__name__)


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
                raise NotFoundError(f"Product with id {item.product_id} not found")

            if not product["is_active"]:
                raise ConflictError(f"Product with id {item.product_id} is inactive")

            if product["stock_quantity"] < item.quantity:
                raise InsufficientStockError(
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
                raise RuntimeError(
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

    logger.info("order_created order_id=%s item_count=%s", order_id, len(order_lines))

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


def get_order_by_id(
    db: sqlite3.Connection,
    order_id: int,
) -> dict:
    order = db.execute(
        """
        SELECT id, customer_name, customer_phone,
               status, total_amount, created_at
        FROM orders
        WHERE id = ?
        """,
        (order_id,),
    ).fetchone()

    if order is None:
        raise NotFoundError(f"Order with id {order_id} not found")
    items = db.execute(
        """
    SELECT
        oi.product_id,
        p.name AS product_name,
        oi.quantity,
        oi.unit_price,
        oi.quantity * oi.unit_price AS line_total
    FROM order_items AS oi
    JOIN products AS p ON oi.product_id = p.id
    WHERE oi.order_id = ?
    ORDER BY oi.id ASC
    """,
        (order_id,),
    ).fetchall()
    order_items = []

    for item in items:
        order_items.append(
            {
                "product_id": item["product_id"],
                "product_name": item["product_name"],
                "quantity": item["quantity"],
                "unit_price": item["unit_price"] / 100,
                "line_total": item["line_total"] / 100,
            }
        )
    return {
        "id": order["id"],
        "customer_name": order["customer_name"],
        "customer_phone": order["customer_phone"],
        "status": order["status"],
        "total_amount": order["total_amount"] / 100,
        "items": order_items,
        "created_at": order["created_at"],
    }


_ORDER_LIST_SQL = """
    SELECT o.id, o.customer_name, o.customer_phone, o.status, o.total_amount,
           COUNT(oi.id) AS item_count, o.created_at
    FROM orders AS o
    LEFT JOIN order_items AS oi ON oi.order_id = o.id
    {where}
    GROUP BY o.id
    ORDER BY o.created_at DESC, o.id DESC
    LIMIT ? OFFSET ?
"""


def _build_order_filters(
    status: str | None,
    customer_phone: str | None,
    date_from: str | None,
    date_to: str | None,
) -> tuple[str, list]:
    """Return a WHERE clause made only of fixed text, plus its ? values."""
    conditions: list[str] = []
    params: list = []

    if status is not None:
        conditions.append("o.status = ?")
        params.append(status)
    if customer_phone is not None:
        conditions.append("o.customer_phone = ?")
        params.append(customer_phone)
    if date_from is not None:
        conditions.append("date(o.created_at) >= ?")
        params.append(date_from)
    if date_to is not None:
        conditions.append("date(o.created_at) <= ?")
        params.append(date_to)

    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
    return where, params


def _order_summary(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "customer_name": row["customer_name"],
        "customer_phone": row["customer_phone"],
        "status": row["status"],
        "total_amount": row["total_amount"] / 100,
        "item_count": row["item_count"],
        "created_at": row["created_at"],
    }


def list_orders(
    db: sqlite3.Connection,
    status: str | None = None,
    customer_phone: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> dict:
    where, params = _build_order_filters(status, customer_phone, date_from, date_to)

    total = db.execute(f"SELECT COUNT(*) FROM orders AS o{where}", params).fetchone()[0]
    total_pages = (total + page_size - 1) // page_size

    offset = (page - 1) * page_size
    rows = db.execute(
        _ORDER_LIST_SQL.format(where=where), (*params, page_size, offset)
    ).fetchall()

    return {
        "items": [_order_summary(row) for row in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


def update_order_status(
    db: sqlite3.Connection,
    order_id: int,
    data: OrderStatusUpdate,
) -> dict:
    try:
        db.execute("BEGIN IMMEDIATE")

        # 1. Fetch the order's current status
        order = db.execute(
            """
            SELECT id, status
            FROM orders
            WHERE id = ?
            """,
            (order_id,),
        ).fetchone()

        if order is None:
            raise NotFoundError(f"Order with id {order_id} not found")

        # 2. Validate the requested status transition
        current_status = order["status"]

        if data.status not in ALLOWED_TRANSITIONS[current_status]:
            raise InvalidTransitionError(
                f"Invalid status transition from {current_status} to {data.status}"
            )

        # 3. Update order status and timestamp
        cursor = db.execute(
            """
            UPDATE orders
            SET status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (data.status, order_id),
        )

        if cursor.rowcount != 1:
            raise RuntimeError("Failed to update order status")

        # 4. Restore stock if the order is cancelled
        if data.status == "cancelled":
            items = db.execute(
                """
                SELECT product_id, quantity
                FROM order_items
                WHERE order_id = ?
                """,
                (order_id,),
            ).fetchall()

            for item in items:
                update_cursor = db.execute(
                    """
                    UPDATE products
                    SET stock_quantity = stock_quantity + ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (
                        item["quantity"],
                        item["product_id"],
                    ),
                )

                if update_cursor.rowcount != 1:
                    raise RuntimeError(
                        f"Stock restoration failed for product {item['product_id']}"
                    )

                # 5. Record the stock restoration
                db.execute(
                    """
                    INSERT INTO stock_movements
                        (product_id, change, reason, order_id)
                    VALUES (?, ?, 'order_cancelled', ?)
                    """,
                    (
                        item["product_id"],
                        item["quantity"],
                        order_id,
                    ),
                )

        # 6. Prepare updated order details
        updated_order = get_order_by_id(db, order_id)

        # 7. Commit all changes together
        db.commit()

    except Exception:
        db.rollback()
        raise
    logger.info(
        "order_status_changed order_id=%s from=%s to=%s",
        order_id,
        current_status,
        data.status,
    )
    if data.status == "cancelled":
        logger.info("order_cancelled order_id=%s", order_id)

    return updated_order
