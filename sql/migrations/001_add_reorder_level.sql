ALTER TABLE products
    ADD COLUMN reorder_level INTEGER NOT NULL DEFAULT 5 CHECK (reorder_level >= 0);
