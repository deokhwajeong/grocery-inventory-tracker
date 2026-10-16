"""The synthetic receipt dataset (#4) and accuracy gates for the parser and the OCR pipeline (#3, #2, #6)."""
import os

import pytest

import ocr_accuracy
import ocr_processor
import receipt_dataset


def test_dataset_is_reproducible_and_covers_all_layouts_and_date_formats():
    a, b = receipt_dataset.generate(40, seed=11), receipt_dataset.generate(40, seed=11)
    assert a == b
    assert receipt_dataset.generate(5, seed=12) != receipt_dataset.generate(5, seed=11)
    assert {r["type"] for r in a} == set(receipt_dataset.RECEIPT_TYPES)
    assert {r["date_format"] for r in a} == set(receipt_dataset.DATE_FORMATS)
    for r in a:
        assert r["items"] and r["date"] and r["text"].count("\n") > 5
        assert abs(sum(i["price"] for i in r["items"]) - r["subtotal"]) < 10   # savings are the only difference


def test_parser_accuracy_on_dataset_text():
    """Text mode isolates the parser. The thresholds leave a little room below today's results."""
    report = ocr_accuracy.evaluate("text", receipts=receipt_dataset.generate(60, seed=99))
    o = report["overall"]
    assert o["item_recall"] >= 97 and o["item_precision"] >= 97
    assert o["price_accuracy"] >= 97 and o["quantity_accuracy"] >= 97
    assert o["name_accuracy"] >= 95
    assert o["date_accuracy"] >= 97 and o["type_accuracy"] >= 95
    assert set(report["by_type"]) == set(receipt_dataset.RECEIPT_TYPES)
    assert "| Item recall |" in ocr_accuracy.markdown(report)


def test_matching_is_one_to_one():
    truth = [{"name": "Whole Milk", "printed": "WHL MLK", "quantity": 1, "price": 3.0}]
    parsed = [{"name": "Whole Milk", "quantity": 1, "price": "3.00"}, {"name": "Whole Milk", "quantity": 1, "price": "3.00"}]
    assert len(ocr_accuracy.match_items(truth, parsed)) == 1
    score = ocr_accuracy.score_receipt({"items": truth, "date": "2026-01-01", "type": "online"},
                                       {"items": parsed, "date": "2026-01-01", "receipt_type": "online"})
    assert score["matched"] == 1 and score["parsed_items"] == 2 and score["date"] and score["type"]


@pytest.mark.skipif(not ocr_processor.is_tesseract_available(), reason="Tesseract not installed")
def test_ocr_pipeline_accuracy_and_speed_on_rendered_receipts(tmp_path):
    manifest = receipt_dataset.write_dataset(str(tmp_path), count=8, seed=5)
    assert all(os.path.exists(tmp_path / r["image"]) for r in manifest["receipts"])
    report = ocr_accuracy.evaluate("ocr", dataset_dir=str(tmp_path))
    o = report["overall"]
    # Loose gates: OCR output depends on the Tesseract build and fonts on the machine.
    assert o["item_recall"] >= 75 and o["item_precision"] >= 80 and o["price_accuracy"] >= 80
    assert o["date_accuracy"] >= 60
    assert o["seconds_median"] < 10       # issue #6 target; this machine measures well under a second


@pytest.mark.skipif(not ocr_processor.is_tesseract_available(), reason="Tesseract not installed")
def test_large_photos_are_scaled_down_before_ocr(tmp_path):
    from PIL import Image
    receipt = receipt_dataset.write_dataset(str(tmp_path), count=1, seed=3)["receipts"][0]
    src = tmp_path / receipt["image"]
    with Image.open(src) as img:
        big = img.resize((img.width * 4, img.height * 4))
    big_path = tmp_path / "big.jpg"
    big.save(big_path)
    gray = ocr_processor.load_grayscale(str(big_path))
    assert gray.shape[1] < big.width                  # shrunk so glyphs are a readable size
    stats = {}
    text = ocr_processor.extract_text_from_image(str(big_path), "eng", stats=stats)
    assert "TOTAL" in text.upper() and stats["total_s"] < 30
