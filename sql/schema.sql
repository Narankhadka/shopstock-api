CREATE TABLE IF NOT EXISTS categories (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    name TEXT NOT NULL UNIQUE
                   CHECK (LENGTH(TRIM(name)) > 0),

    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT, 

    sku TEXT NOT NULL UNIQUE 
                      CHECK (sku GLOB '[A-Z][A-Z][A-Z]-[0-9][0-9][0-9][0-9]'),
    name  TEXT NOT NULL 
                    CHECK (LENGTH(TRIM(name))BETWEEN 2 AND 100),

    category_id INTEGER NOT NULL REFERENCES categories(id),
    
    price INTEGER NOT NULL 
                        CHECK (price > 0 AND price <= 100000000),

    stock_quantity INTEGER NOT NULL DEFAULT 0
                            CHECK (stock_quantity >=0),

    is_active INTEGER NOT NULL DEFAULT 1 
                        CHECK (is_active IN (0,1)),
    
    created_at TEXT NOT NULL DEFAULT (datetime('now')),

    updated_at TEXT NOT NULL DEFAULT (datetime('now'))

);


CREATE TABLE IF NOT EXISTS orders(
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    customer_name TEXT NOT NULL 
                   CHECK (LENGTH(TRIM(customer_name)) > 0),

    customer_phone TEXT NOT NULL 
                    CHECK (
                        LENGTH(customer_phone) = 10
                        AND (customer_phone LIKE '97%' OR customer_phone LIKE '98%')
                        AND customer_phone NOT GLOB '*[^0-9]*'
                    ),

    status TEXT NOT NULL DEFAULT 'pending' 
                    CHECK (status IN (
                        'pending',
                        'confirmed',
                        'delivered',
                        'cancelled' )),

    total_amount INTEGER NOT NULL CHECK (total_amount >=0),

    created_at TEXT NOT NULL DEFAULT (datetime('now')),

    updated_at TEXT NOT NULL DEFAULT (datetime('now'))

);


