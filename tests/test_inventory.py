"""Merging new items into matching stock instead of creating duplicate rows (issue #13)."""
from datetime import date, timedelta

import pytest

from inventory import add_or_merge, expiry_close, normalize_name


def iso(days_from_today):
    return (date.today() + timedelta(days=days_from_today)).isoformat()


def add_form(client, name, qty="1", expiry=None, category="Dairy", purchase=0, **extra):
    data = {"name": name, "quantity": qty, "purchase_date": iso(purchase), "category": category}
    if expiry is not None:
        data["expiry_date"] = iso(expiry)
    data.update(extra)
    return client.post("/add", data=data, follow_redirects=True)


def rows(db):
    return [dict(r) for r in db.execute("SELECT * FROM groceries ORDER BY id")]


@pytest.mark.parametrize("a, b", [
    ("Greek Yogurt", "greek yogurt"),
    ("Greek  Yogurt ", "Greek-Yogurt"),
    ("Banana", "Bananas"),
    ("Large Eggs", "large egg"),
])
def test_normalize_name_matches_variants(a, b):
    assert normalize_name(a) == normalize_name(b)


@pytest.mark.parametrize("a, b", [("Milk", "Oat Milk"), ("Swiss", "Swis"), ("Peas", "Pears")])
def test_normalize_name_keeps_different_items_apart(a, b):
    assert normalize_name(a) != normalize_name(b)


def test_expiry_close_rules():
    assert expiry_close(None, None, 3)
    assert expiry_close("2026-01-10", "2026-01-13", 3)
    assert not expiry_close("2026-01-10", "2026-01-14", 3)
    assert not expiry_close("2026-01-10", None, 3)
    assert not expiry_close("not a date", "2026-01-10", 3)


def test_adding_same_item_merges_quantities(client, db):
    add_form(client, "Greek Yogurt", qty="2", expiry=6, notes="Plain")
    response = add_form(client, "greek yogurt", qty="3", expiry=5, notes="Vanilla")
    assert b"already in stock" in response.data and b"You now have 5" in response.data
    [row] = rows(db)
    assert row["name"] == "Greek Yogurt"          # original spelling is kept
    assert row["quantity"] == 5
    assert row["expiry_date"] == iso(5)           # earlier expiry wins
    assert row["notes"] == "Plain; Vanilla"


def test_items_without_expiry_merge(client, db):
    add_form(client, "Sparkling Water", qty="6", category="Beverages")
    add_form(client, "Sparkling Water", qty="6", category="Beverages")
    assert [r["quantity"] for r in rows(db)] == [12]


def test_distant_expiry_stays_separate(client, db):
    add_form(client, "Whole Milk", expiry=2)
    response = add_form(client, "Whole Milk", expiry=10)
    assert b"Item added successfully" in response.data
    assert len(rows(db)) == 2


def test_different_category_or_missing_expiry_stays_separate(client, db):
    add_form(client, "Tofu", expiry=5, category="Other")
    add_form(client, "Tofu", expiry=5, category="Produce")
    add_form(client, "Tofu", category="Other")
    assert len(rows(db)) == 3


def test_keep_separate_opt_out(client, db):
    add_form(client, "Bagels", category="Bakery", expiry=3)
    add_form(client, "Bagels", category="Bakery", expiry=3, keep_separate="1")
    assert len(rows(db)) == 2


def test_merge_picks_the_closest_expiry(db):
    add_or_merge(db, "Eggs", 6, iso(-2), iso(10), "Dairy", window_days=3, merge=False)
    add_or_merge(db, "Eggs", 6, iso(-1), iso(14), "Dairy", window_days=3, merge=False)
    result = add_or_merge(db, "eggs", 12, iso(0), iso(13), "Dairy", window_days=3)
    db.commit()
    assert result.merged
    by_expiry = {r["expiry_date"]: r for r in rows(db)}
    assert by_expiry[iso(13)]["quantity"] == 18    # merged into the day-14 row, which now expires day 13
    assert by_expiry[iso(13)]["purchase_date"] == iso(0)
    assert by_expiry[iso(10)]["quantity"] == 6


def test_merge_caps_quantity(db):
    add_or_merge(db, "Rice", 9999, iso(0), None, "Pantry")
    result = add_or_merge(db, "Rice", 50, iso(0), None, "Pantry")
    assert result.merged and result.quantity == 10000


def test_receipt_review_merges_with_existing_stock(client, db):
    add_form(client, "Orange Juice", qty="1", category="Beverages")
    with client.session_transaction() as sess:
        sess["ocr_items"] = [
            {"name": "Orange Juice", "quantity": 1, "purchase_date": iso(0), "category": "Beverages", "confidence": 90},
            {"name": "Broccoli", "quantity": 1, "purchase_date": iso(0), "category": "Produce", "confidence": 90},
        ]
    response = client.post("/ocr/review", data={
        "selected": ["0", "1"],
        "name_0": "Orange Juice", "quantity_0": "2", "purchase_date_0": iso(0), "category_0": "Beverages",
        "name_1": "Broccoli", "quantity_1": "1", "purchase_date_1": iso(0), "category_1": "Produce",
    }, follow_redirects=True)
    assert b"Successfully added 2 items (1 combined with items already in stock)" in response.data
    assert {r["name"]: r["quantity"] for r in rows(db)} == {"Orange Juice": 3, "Broccoli": 1}
