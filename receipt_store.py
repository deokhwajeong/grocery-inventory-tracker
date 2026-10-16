"""
Receipt records and stored receipt images.

Each scanned receipt becomes a row in the receipts table. The parsed items wait
there (status "pending") until the user reviews them, so a batch of receipts
does not have to fit in the session cookie. Once reviewed, the receipt is
marked "imported" and the inventory rows it created point back to it.

Images are re-encoded before they are kept: EXIF orientation applied, metadata
dropped, scaled down to at most ``max_dimension`` pixels on the long side, and
saved as JPEG under a random file name. Only the newest ``keep`` images per
account are kept; older receipts keep their items and details but lose the
picture.
"""
import json
import os
import secrets
import sqlite3
from typing import Dict, List, Optional

from PIL import Image, ImageOps

STATUSES = ("pending", "imported", "discarded")


def save_image(source_path: str, folder: str, max_dimension: int = 1600, quality: int = 82) -> str:
    """Store a downscaled JPEG copy of the image and return its file name (relative to ``folder``)."""
    os.makedirs(folder, exist_ok=True)
    name = f"{secrets.token_hex(12)}.jpg"
    with Image.open(source_path) as img:
        img = ImageOps.exif_transpose(img)
        img = img.convert("RGB")
        img.thumbnail((max_dimension, max_dimension), Image.LANCZOS)
        img.save(os.path.join(folder, name), format="JPEG", quality=quality, optimize=True)
    return name


def image_path(folder: str, filename: Optional[str]) -> Optional[str]:
    """Absolute path of a stored image, or None if it is missing or the name is unsafe."""
    if not filename or os.path.basename(filename) != filename:
        return None
    path = os.path.join(folder, filename)
    return path if os.path.isfile(path) else None


def remove_image(folder: str, filename: Optional[str]) -> None:
    path = image_path(folder, filename)
    if path:
        try:
            os.remove(path)
        except OSError:
            pass


def create(conn: sqlite3.Connection, user_id: int, result: Dict, original_name: str,
           image_filename: Optional[str]) -> int:
    """Insert a pending receipt with its parsed items. The caller commits."""
    items = result.get("items", [])
    cur = conn.execute(
        "INSERT INTO receipts (user_id, image_filename, original_name, receipt_date, store, receipt_type, "
        "items_json, item_count, ocr_seconds) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (user_id, image_filename, original_name, result.get("date"), result.get("store"), result.get("receipt_type"),
         json.dumps(items), len(items), result.get("ocr_seconds")),
    )
    return cur.lastrowid


def get(conn: sqlite3.Connection, user_id: int, receipt_id: int) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM receipts WHERE id = ? AND user_id = ?", (receipt_id, user_id)).fetchone()


def pending(conn: sqlite3.Connection, user_id: int, ids: List[int]) -> List[Dict]:
    """The given receipts that belong to the user and still await review, with their items decoded."""
    out = []
    for rid in ids:
        row = conn.execute("SELECT * FROM receipts WHERE id = ? AND user_id = ? AND status = 'pending'",
                           (rid, user_id)).fetchone()
        if row:
            receipt = dict(row)
            receipt["items"] = json.loads(row["items_json"] or "[]")
            out.append(receipt)
    return out


def history(conn: sqlite3.Connection, user_id: int, limit: int = 100) -> List[sqlite3.Row]:
    return conn.execute("SELECT * FROM receipts WHERE user_id = ? ORDER BY uploaded_at DESC, id DESC LIMIT ?",
                        (user_id, limit)).fetchall()


def mark(conn: sqlite3.Connection, user_id: int, receipt_id: int, status: str, imported_count: int = 0) -> None:
    assert status in STATUSES
    conn.execute("UPDATE receipts SET status = ?, imported_count = ? WHERE id = ? AND user_id = ?",
                 (status, imported_count, receipt_id, user_id))


def delete(conn: sqlite3.Connection, folder: str, user_id: int, receipt_id: int) -> bool:
    """Delete a receipt and its image. Inventory items it created stay, unlinked."""
    row = get(conn, user_id, receipt_id)
    if row is None:
        return False
    remove_image(folder, row["image_filename"])
    conn.execute("UPDATE groceries SET receipt_id = NULL WHERE receipt_id = ? AND user_id = ?", (receipt_id, user_id))
    conn.execute("DELETE FROM receipts WHERE id = ?", (receipt_id,))
    return True


def prune_images(conn: sqlite3.Connection, folder: str, user_id: int, keep: int) -> int:
    """Remove images beyond the newest ``keep`` for this account. Returns how many were removed."""
    rows = conn.execute(
        "SELECT id, image_filename FROM receipts WHERE user_id = ? AND image_filename IS NOT NULL "
        "ORDER BY uploaded_at DESC, id DESC LIMIT -1 OFFSET ?", (user_id, max(keep, 0))).fetchall()
    for row in rows:
        remove_image(folder, row["image_filename"])
        conn.execute("UPDATE receipts SET image_filename = NULL WHERE id = ?", (row["id"],))
    return len(rows)
