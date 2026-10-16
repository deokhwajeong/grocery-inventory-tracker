"""
Inventory write helpers shared by the manual add form and the receipt review.

Adding an item that is already in stock merges it into the existing row
instead of creating a duplicate. Two rows are treated as the same stock when:

- their normalized names match (case, spacing, punctuation, and a trailing
  plural "s" are ignored, so "Greek yogurt" matches "greek  Yogurts"),
- they are in the same category, and
- their expiry dates are close: both missing, or both set and no more than
  ``window_days`` apart. Items with very different dates (a new carton of milk
  versus last week's) stay separate so the expiry warnings stay accurate.

On a merge the quantities are added, the earlier expiry date is kept (the
warning should fire for the oldest units), the later purchase date is kept,
and new notes are appended.
"""
import re
import sqlite3
from datetime import date
from typing import NamedTuple, Optional

MAX_QUANTITY = 10000


def normalize_name(name: str) -> str:
    """Return a comparison key for an item name."""
    text = re.sub(r"[^\w\s]", " ", (name or "").casefold())
    words = text.split()
    if words and len(words[-1]) > 3 and words[-1].endswith("s") and not words[-1].endswith("ss"):
        words[-1] = words[-1][:-1]
    return " ".join(words)


def _days_apart(a: str, b: str) -> Optional[int]:
    try:
        return abs((date.fromisoformat(a) - date.fromisoformat(b)).days)
    except (TypeError, ValueError):
        return None


def expiry_close(a: Optional[str], b: Optional[str], window_days: int) -> bool:
    """True when both expiry dates are missing, or both are set and within the window."""
    if not a and not b:
        return True
    if not a or not b:
        return False
    gap = _days_apart(a, b)
    return gap is not None and gap <= window_days


def find_merge_candidate(conn: sqlite3.Connection, name: str, category: str,
                         expiry_date: Optional[str], window_days: int) -> Optional[sqlite3.Row]:
    """Find the existing row a new item should merge into, or None."""
    key = normalize_name(name)
    best, best_gap = None, None
    rows = conn.execute("SELECT * FROM groceries WHERE category = ?", (category,)).fetchall()
    for row in rows:
        if normalize_name(row["name"]) != key or not expiry_close(row["expiry_date"], expiry_date, window_days):
            continue
        gap = _days_apart(row["expiry_date"], expiry_date) if expiry_date else 0
        if best is None or gap < best_gap:
            best, best_gap = row, gap
    return best


class AddResult(NamedTuple):
    item_id: int
    merged: bool
    name: str
    quantity: int


def add_or_merge(conn: sqlite3.Connection, name: str, quantity: int, purchase_date: str,
                 expiry_date: Optional[str], category: str, notes: str = "",
                 window_days: int = 3, merge: bool = True) -> AddResult:
    """Insert a grocery item, or merge it into a matching row already in stock.

    The caller commits the transaction.
    """
    expiry_date = expiry_date or None
    existing = find_merge_candidate(conn, name, category, expiry_date, window_days) if merge else None
    if existing is None:
        cur = conn.execute(
            "INSERT INTO groceries (name, quantity, purchase_date, expiry_date, category, notes) VALUES (?, ?, ?, ?, ?, ?)",
            (name, quantity, purchase_date, expiry_date, category, notes),
        )
        return AddResult(cur.lastrowid, False, name, quantity)

    new_qty = min(existing["quantity"] + quantity, MAX_QUANTITY)
    expiries = [d for d in (existing["expiry_date"], expiry_date) if d]
    new_expiry = min(expiries) if expiries else None
    new_purchase = max(existing["purchase_date"], purchase_date)
    old_notes = existing["notes"] or ""
    new_notes = old_notes
    if notes and notes.casefold() not in old_notes.casefold():
        new_notes = f"{old_notes}; {notes}" if old_notes else notes
    conn.execute(
        "UPDATE groceries SET quantity = ?, expiry_date = ?, purchase_date = ?, notes = ? WHERE id = ?",
        (new_qty, new_expiry, new_purchase, new_notes, existing["id"]),
    )
    return AddResult(existing["id"], True, existing["name"], new_qty)
