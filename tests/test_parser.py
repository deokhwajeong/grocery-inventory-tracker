"""Receipt text parsing: dates (#12), prices and quantities (#3), receipt layouts (#2)."""
from datetime import date

import pytest

import ocr_processor
import receipt_parser
from receipt_parser import detect_receipt_type, find_receipt_date, parse_receipt_items

TODAY = date(2026, 6, 30)


# ---------------------------------------------------------------- dates (#12)

@pytest.mark.parametrize("text, expected", [
    ("Date: 2026-01-23", "2026-01-23"),
    ("2026/01/23 14:02", "2026-01-23"),
    ("2026.01.23", "2026-01-23"),
    ("2026. 1. 5", "2026-01-05"),
    ("01/23/2026 08:15", "2026-01-23"),          # US month first
    ("1/5/2026", "2026-01-05"),
    ("06/19/26 TIME 16:38", "2026-06-19"),        # two-digit year
    ("23/01/2026", "2026-01-23"),                 # first number > 12, so day first
    ("23.01.2026", "2026-01-23"),                 # dotted European
    ("Delivered Jan 5, 2026", "2026-01-05"),
    ("Ordered January 23rd, 2026", "2026-01-23"),
    ("Sept 3, 2025", "2025-09-03"),
    ("23 JAN 2026", "2026-01-23"),
    ("5 Mar. 2026", "2026-03-05"),
    ("2026nyeon 1wol 23il", "2026-01-23"),
    ("2026년 1월 23일", "2026-01-23"),
])
def test_date_formats(text, expected):
    assert find_receipt_date(text, today=TODAY) == expected


def test_day_first_option_for_ambiguous_slash_dates():
    assert find_receipt_date("05/04/2026", today=TODAY) == "2026-05-04"
    assert find_receipt_date("05/04/2026", day_first=True, today=TODAY) == "2026-04-05"


@pytest.mark.parametrize("text", [
    "TEL 555-266-2604",                    # phone number
    "MEMBER 878628668735",
    "Order #642-7488270",
    "13/13/2026",                          # impossible month and day
    "02/30/2026",                          # no such day
    "12/01/2031",                          # in the future
    "01/02/1999",                          # implausibly old
    "TOTAL 18.76",
])
def test_non_dates_are_ignored(text):
    assert find_receipt_date(text, today=TODAY) is None


def test_date_line_with_keyword_wins_over_other_numbers():
    text = "STORE 12.03.2024 REMODEL\nItems\nDate: 06/19/2026\nMilk 3.99"
    assert find_receipt_date(text, today=TODAY) == "2026-06-19"


def test_missing_date_falls_back_to_today():
    assert ocr_processor.extract_dates_from_text("Milk 3.99") == date.today().isoformat()


# ---------------------------------------------------------------- prices and quantities (#3)

def items(text, kind=None):
    return [(i["name"], i["quantity"], i["price"]) for i in parse_receipt_items(text, kind)]


def test_supermarket_quantity_line_after_item():
    text = "GREEN MARKET\nRLD OATS        7.32\n  2 @ 3.66\nBAGELS 3.99 F\nSUBTOTAL 11.31\nTOTAL 11.31"
    assert items(text) == [("RLD OATS", 2, "7.32"), ("BAGELS", 1, "3.99")]
    oats = parse_receipt_items(text)[0]
    assert oats["unit_price"] == "3.66"


def test_weighed_produce():
    text = "YLW ONION\n  2.37 lb @ 1.23 /lb   2.92 T\nBANANAS\n 1.10 kg @ 1.50 /kg"
    parsed = parse_receipt_items(text, "supermarket")
    assert [(i["name"], i["quantity"], i["price"]) for i in parsed] == [("YLW ONION", 1, "2.92"), ("BANANAS", 1, "1.65")]
    assert parsed[0]["weight"] == "2.37 lb" and parsed[0]["unit_price"] == "1.23"


def test_savings_become_a_discount_not_an_item():
    text = "BTL WTR   19.56 T\n  4 @ 4.89\n  SAVINGS   -0.50\nCOUPON 1.00-\nPOPCORN 6.74"
    parsed = parse_receipt_items(text, "supermarket")
    assert [(i["name"], i["quantity"]) for i in parsed] == [("BTL WTR", 4), ("POPCORN", 1)]
    assert parsed[0]["discount"] == "1.50"          # both discounts follow the water


def test_warehouse_quantity_line_before_item_and_item_codes():
    text = "BULKWAY WHOLESALE\nMEMBER 111122223333\n2 @ 5.80\n807141 KIRK HONEY 11.60 A\n765314 RED BELL PEPPER 1.52"
    assert items(text) == [("KIRK HONEY", 2, "11.60"), ("RED BELL PEPPER", 1, "1.52")]


def test_convenience_quantity_column():
    text = "QUICKSTOP #22\nQTY ITEM          AMOUNT\n1  ROMAINE LTTC     2.26\n2  GROUND BEEF     12.02\nTOTAL 14.28"
    assert items(text) == [("ROMAINE LTTC", 1, "2.26"), ("GROUND BEEF", 2, "12.02")]


def test_online_two_line_items():
    text = ("FRESHCART DELIVERY\nOrder #642-7488270\nDelivered Jan 5, 2026\nChicken Thighs\n  Qty 2 x $6.60   $13.20\n"
            "Heavy Cream\n  Qty 1    $3.88\nDelivery fee $5.99\nTOTAL $23.07")
    assert items(text) == [("Chicken Thighs", 2, "13.20"), ("Heavy Cream", 1, "3.88")]


@pytest.mark.parametrize("line, qty, price", [
    ("2x Greek Yogurt 5.98", 2, "5.98"),
    ("Greek Yogurt x3 $8.97", 3, "8.97"),
    ("Greek Yogurt 2x $1.29", 2, "1.29"),
    ("Greek Yogurt 4 EA 5.16", 4, "5.16"),
    ("Greek Yogurt 2 @ 2.99 5.98", 2, "5.98"),
    ("Greek Yogurt $1,299.00", 1, "1299.00"),
    ("Greek Yogurt 3,49", 1, "3.49"),             # decimal comma
    ("Greek Yogurt 3. 49 F", 1, "3.49"),          # OCR split the decimal
])
def test_inline_quantity_and_price_formats(line, qty, price):
    assert ocr_processor.extract_quantity_and_price(line) == (qty, price)


def test_quantity_line_alone_and_lines_without_price():
    assert ocr_processor.extract_quantity_and_price("3 @ 1.50") == (3, "4.50")
    assert ocr_processor.extract_quantity_and_price("THANK YOU") == (1, None)


@pytest.mark.parametrize("text", [
    "SUBTOTAL 21.55", "TAX 0.62", "TOTAL 22.17", "VISA ************6494", "CHANGE DUE 0.00", "CASH 40.00",
    "Delivery fee $5.99", "8923 OAK AVE", "TEL 555-266-2604", "Charged to card ending 1234",
])
def test_header_and_footer_lines_are_not_items(text):
    assert parse_receipt_items(text) == []


def test_skip_words_match_whole_words_only():
    # "cashews" contains "cash" and "coffee" contains "off"; both are real items
    assert items("CASHEWS 6.99\nGROUND COFFEE 9.99") == [("CASHEWS", 1, "6.99"), ("GROUND COFFEE", 1, "9.99")]


def test_zero_read_for_the_letter_o_is_fixed_in_names():
    assert items("0J NO PULP 3.49\nC0LA 20OZ 2.29") == [("OJ NO PULP", 1, "3.49"), ("COLA 20OZ", 1, "2.29")]
    assert ocr_processor.parse_receipt("MARKET\n0J NO PULP 3.49\nTOTAL 3.49")["items"][0]["name"] == "Orange Juice"


def test_to_amount():
    assert receipt_parser.to_amount("$1,234.50") == 1234.5
    assert receipt_parser.to_amount("3,49") == 3.49
    assert receipt_parser.to_amount("abc") is None
    assert receipt_parser.to_amount(None) is None


# ---------------------------------------------------------------- receipt types (#2)

@pytest.mark.parametrize("text, kind", [
    ("GREENLEAF MARKET\nMILK 3.99 F\n  2 @ 1.99\nTOTAL 3.99", "supermarket"),
    ("CORNER MART 24HR\nQTY ITEM AMOUNT\n1  COLA 2.29\n2  CHIPS 7.98", "convenience"),
    ("BULKWAY WHOLESALE\nMEMBER 111122223333\n512345 KS MILK 4.99 E\n223344 EGGS 6.49 E", "warehouse"),
    ("Order #123-4567\nDelivered Jan 5, 2026\nMilk\n Qty 1  $3.99", "online"),
    ("E-MART Seongsu\nUYU 2,980", "supermarket"),
    ("GS25 Gangnam\nSAIDA 1,500", "convenience"),
    ("Coupang order\nRAMYEON 4,500", "online"),
    ("hello world", "unknown"),
])
def test_detect_receipt_type(text, kind):
    assert detect_receipt_type(text) == kind


def test_short_chain_names_do_not_match_inside_words():
    # "cu" (a convenience chain) must not match "cucumber"
    assert detect_receipt_type("FRESH FOODS\nCUCUMBER 0.89") == "supermarket"


# ---------------------------------------------------------------- whole pipeline

def test_parse_receipt_returns_items_date_type_and_categories():
    text = ("GREENLEAF MARKET\n8923 OAK AVE\n03/13/2026 20:08\nSTRAWB 3.88 F\nRLD OATS 7.32\n  2 @ 3.66\n"
            "GV HVY CRM 8.50\n  2 @ 4.25\nSUBTOTAL 19.70\nTOTAL 19.70")
    result = ocr_processor.parse_receipt(text)
    assert result["date"] == "2026-03-13"
    assert result["receipt_type"] == "supermarket"
    assert result["store"] == "GREENLEAF MARKET"
    got = {(i["name"], i["quantity"], i["price"], i["category"]) for i in result["items"]}
    assert got == {("Strawberries", 1, "3.88", "Produce"), ("Rolled Oats", 2, "7.32", "Pantry"),
                   ("Heavy Cream", 2, "8.50", "Dairy")}
    assert all(i["raw_name"] for i in result["items"])


def test_hand_written_receipt_not_from_the_generator():
    """A layout written by hand for this test, so the parser is not only checked against its own dataset."""
    text = """Neighborhood Co-op
    Receipt 0042   Cashier: Sam
    2026-02-14 10:31
    ORGANIC BANANAS        1.98
    OAT MILK 64OZ          4.79
    3 X LIMES              1.50
    SOURDOUGH LOAF         6.25
      MEMBER DISCOUNT     -0.62
    EGGS DOZEN LG          5.49
    ITEMS SOLD 6
    TOTAL                 19.39
    DEBIT                 19.39"""
    result = ocr_processor.parse_receipt(text)
    got = {(i["name"], i["quantity"], i["price"]) for i in result["items"]}
    assert got == {("Bananas", 1, "1.98"), ("Oat Milk", 1, "4.79"), ("Limes", 3, "1.50"),
                   ("Sourdough Bread", 1, "6.25"), ("Large Eggs", 1, "5.49")}
    assert result["date"] == "2026-02-14"


def test_duplicate_lines_are_merged_with_summed_prices():
    result = ocr_processor.parse_receipt("MARKET\nMILK 3.99\nBREAD 2.49\nMILK 3.99\nTOTAL 10.47")
    milk = next(i for i in result["items"] if i["name"] == "Milk")
    assert milk["quantity"] == 2 and milk["price"] == "7.98"
