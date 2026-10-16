#!/usr/bin/env python3
"""
Fill the database with synthetic demo data (no real personal information).

Dates are relative to today, so the dashboard always shows a realistic mix
of fresh, expiring, and expired items.

Usage:
    python scripts/seed_demo_data.py            # add demo items
    python scripts/seed_demo_data.py --reset    # wipe the table first
"""
import argparse
import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import get_db_connection, init_db  # noqa: E402

# (name, quantity, category, days since purchase, days until expiry or None, notes)
DEMO_ITEMS = [
    ("Whole Milk", 1, "Dairy", 5, 2, "Half gallon"),
    ("Greek Yogurt", 4, "Dairy", 3, 6, "Plain, 5.3 oz cups"),
    ("Cheddar Cheese", 1, "Dairy", 10, 24, "Sharp, 8 oz block"),
    ("Unsalted Butter", 2, "Dairy", 12, 45, ""),
    ("Large Eggs", 12, "Dairy", 4, 18, "Free range"),
    ("Chicken Thighs", 2, "Meat", 2, 1, "Boneless, 1.5 lb"),
    ("Ground Turkey", 1, "Meat", 6, -1, "93% lean"),
    ("Salmon Fillet", 1, "Meat", 1, 2, "Wild caught"),
    ("Baby Spinach", 1, "Produce", 5, 0, "5 oz clamshell"),
    ("Strawberries", 1, "Produce", 3, 3, "1 lb"),
    ("Bananas", 6, "Produce", 2, 4, ""),
    ("Avocados", 3, "Produce", 2, 5, "Ripen on counter"),
    ("Carrots", 1, "Produce", 8, 16, "2 lb bag"),
    ("Honeycrisp Apples", 5, "Produce", 4, 20, ""),
    ("Sourdough Bread", 1, "Bakery", 3, 2, "Sliced loaf"),
    ("Bagels", 4, "Bakery", 9, -2, "Everything"),
    ("Frozen Peas", 2, "Frozen", 20, 200, "12 oz bags"),
    ("Vanilla Ice Cream", 1, "Frozen", 14, 90, "1.5 qt"),
    ("Basmati Rice", 1, "Pantry", 40, 400, "5 lb bag"),
    ("Spaghetti", 3, "Pantry", 25, 380, "16 oz"),
    ("Crushed Tomatoes", 4, "Pantry", 30, 540, "28 oz cans"),
    ("Extra Virgin Olive Oil", 1, "Pantry", 35, 300, "750 ml"),
    ("Orange Juice", 1, "Beverages", 4, 5, "No pulp, 52 oz"),
    ("Sparkling Water", 12, "Beverages", 10, None, "Lime"),
    ("Ground Coffee", 1, "Beverages", 15, 150, "Medium roast"),
    ("Granola Bars", 2, "Snacks", 18, 120, "Oats and honey"),
    ("Hummus", 1, "Snacks", 6, 3, "Classic, 10 oz"),
    ("Tofu", 2, "Other", 5, 9, "Extra firm"),
]

def seed(reset=False):
    init_db()
    today = date.today()
    conn = get_db_connection()
    if reset:
        conn.execute("DELETE FROM groceries")
    for name, qty, category, bought_ago, expires_in, notes in DEMO_ITEMS:
        purchase = (today - timedelta(days=bought_ago)).isoformat()
        expiry = (today + timedelta(days=expires_in)).isoformat() if expires_in is not None else None
        conn.execute(
            "INSERT INTO groceries (name, quantity, purchase_date, expiry_date, category, notes) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (name, qty, purchase, expiry, category, notes),
        )
    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM groceries").fetchone()[0]
    conn.close()
    print(f"Seeded demo data. Inventory now has {count} items.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reset", action="store_true", help="delete existing items first")
    seed(parser.parse_args().reset)
