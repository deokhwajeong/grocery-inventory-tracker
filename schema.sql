-- Household accounts. One login is shared by everyone in the household.
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS groceries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    purchase_date TEXT NOT NULL,
    expiry_date TEXT,
    category TEXT DEFAULT 'Other',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER REFERENCES users(id),
    receipt_id INTEGER REFERENCES receipts(id)
);

-- Scanned receipts: parsed items wait here for review, and the stored image
-- (if any) stays available in the receipt history.
CREATE TABLE IF NOT EXISTS receipts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    image_filename TEXT,
    original_name TEXT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    receipt_date TEXT,
    store TEXT,
    receipt_type TEXT,
    items_json TEXT NOT NULL DEFAULT '[]',
    item_count INTEGER NOT NULL DEFAULT 0,
    imported_count INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending',
    ocr_seconds REAL
);

CREATE INDEX IF NOT EXISTS idx_category ON groceries(category);
CREATE INDEX IF NOT EXISTS idx_expiry_date ON groceries(expiry_date);
CREATE INDEX IF NOT EXISTS idx_receipts_user ON receipts(user_id, uploaded_at);
