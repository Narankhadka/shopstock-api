CREATE TABLE IF NOT EXISTS categories (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    name TEXT NOT NULL UNIQUE
                   CHECK (LENGTH(TRIM(name)) > 0),

    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);