CREATE TABLE IF NOT EXISTS groceries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    purchase_date TEXT NOT NULL,
    expiry_date TEXT,
    category TEXT DEFAULT 'Other',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_category ON groceries(category);
CREATE INDEX IF NOT EXISTS idx_expiry_date ON groceries(expiry_date);
