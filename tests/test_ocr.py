"""Tests for receipt parsing. OCR-engine tests are skipped when Tesseract is absent."""
import os

import pytest
from PIL import Image, ImageDraw, ImageFont

import ocr_processor
from ocr_advanced import get_category_suggestion, normalize_product_name

SAMPLE_TEXT = """FRESH MART
123 Example Ave
Milk $3.99
Sourdough Bread $4.49
Bananas 2x $1.29
Chicken Breast $8.99
SUBTOTAL $18.76
TAX $0.00
TOTAL $18.76
Date: 2026-01-23
"""


def test_post_processing_keeps_line_breaks():
    text = ocr_processor.post_process_ocr_text("Milk   $3.99\n\n  Bread\t$2.49  \n")
    assert text == "Milk $3.99\nBread $2.49"


def test_parse_receipt_text_extracts_items_and_skips_totals():
    items = ocr_processor.parse_receipt_text(ocr_processor.post_process_ocr_text(SAMPLE_TEXT))
    names = {item["name"] for item in items}
    assert {"Milk", "Sourdough Bread", "Bananas", "Chicken Breast"} <= names
    assert not any("TOTAL" in name.upper() or "TAX" in name.upper() for name in names)
    bananas = next(i for i in items if i["name"] == "Bananas")
    assert bananas["quantity"] == 2
    assert all(i["purchase_date"] == "2026-01-23" for i in items)


def test_name_normalization_does_not_corrupt_letters():
    assert normalize_product_name("Olive Oil")[0] == "Olive Oil"
    assert normalize_product_name("milk")[0] == "Milk"


@pytest.mark.parametrize("name,category", [
    ("Whole Milk", "Dairy"), ("Chicken Breast", "Meat"), ("Bananas", "Produce"),
    ("Orange Juice", "Beverages"), ("Basmati Rice", "Pantry"),
])
def test_category_suggestion(name, category):
    assert get_category_suggestion(name) == category


@pytest.mark.skipif(not ocr_processor.is_tesseract_available(), reason="Tesseract not installed")
def test_end_to_end_receipt_image(tmp_path):
    img = Image.new("RGB", (480, 520), "white")
    draw = ImageDraw.Draw(img)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    font = ImageFont.truetype(font_path, 22) if os.path.exists(font_path) else ImageFont.load_default()
    lines = ["FRESH MART", "Milk $3.99", "Bread $2.49", "Chicken Breast $8.99",
             "Orange Juice $3.49", "TOTAL $18.96", "Date: 2026-01-23"]
    for i, line in enumerate(lines):
        draw.text((40, 40 + i * 50), line, fill="black", font=font)
    path = tmp_path / "receipt.png"
    img.save(path)

    items = ocr_processor.process_receipt_image(str(path), "eng")
    names = {item["name"].lower() for item in items}
    assert {"milk", "bread", "chicken breast", "orange juice"} <= names
