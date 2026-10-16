# Roadmap

Status of the roadmap issues as of October 2026. Numbers for the OCR work come from `scripts/ocr_accuracy.py` on the synthetic dataset; see "Receipt OCR accuracy" in the README for how to read them.

## Done

| Issue | What was built | Main files |
| --- | --- | --- |
| #1 Expand product database | 558 hand-written grocery products in 9 categories, with spelling, brand (for example Coca-Cola) and romanized Korean variants, a receipt abbreviation table, word-order, prefix and fuzzy matching. Name normalization on the dataset went from 15.5% to 99.5%. | `product_catalog.py`, `ocr_advanced.py`, `tests/test_catalog.py` |
| #2 Receipt type-specific parsing | Layout detection (supermarket, convenience, warehouse club, online order) from structure, not only store names, and a reading strategy per layout. Layout detection on the dataset: 100%. | `receipt_parser.py`, `tests/test_parser.py` |
| #3 Price and quantity extraction | Line totals and unit prices, `N @ price` lines attached by arithmetic, QTY columns, `Qty N x $p`, weighed items, discounts, decimal commas and thousands separators. With OCR: price 67.4% to 98.4%, quantity 50.8% to 98.6%. | `receipt_parser.py`, `tests/test_parser.py` |
| #4 OCR test dataset | A reproducible synthetic dataset (60 receipts, 395 items, 4 layouts, 7 date formats, photo-like noise) with committed ground truth, plus an accuracy script that CI runs. Real receipts are not collected or committed. | `scripts/receipt_dataset.py`, `scripts/ocr_accuracy.py`, `datasets/receipts/ground_truth.json`, `tests/test_accuracy.py` |
| #5 Batch receipt processing | Up to 10 receipts per batch, read one after another with per-file status and overall progress, then reviewed together. Works without JavaScript too. | `templates/ocr.html`, `app.py` (`/ocr`, `/api/ocr/scan`), `tests/test_receipts.py` |
| #6 OCR processing time | Glyph-size based rescaling, one Tesseract pass when the result already looks complete, parallel fallback passes, a per-call timeout. Mean time per receipt on this machine: 11.4 s to 0.44 s (median 8.72 s to 0.42 s). | `ocr_processor.py`, `tests/test_accuracy.py` |
| #8 Barcode scanning with real lookup | Optional Open Food Facts lookup (`BARCODE_ONLINE_LOOKUP=true`) after the offline catalog, with a timeout, caching, and a manual-entry fallback. Camera scanning (ZXing) was already in place. | `barcode_catalog.py`, `templates/barcode.html`, `tests/test_receipts.py` |
| #12 Receipt date extraction | Was partly implemented; rewritten and tested for YYYY-MM-DD, YYYY/MM/DD, YYYY.MM.DD, MM/DD/YYYY, MM/DD/YY, DD/MM/YYYY (first number above 12), DD.MM.YYYY, "Jan 5, 2026", "5 Jan 2026" and the Korean form. Phone numbers, future dates and impossible dates are ignored. Date accuracy with OCR: 35.0% to 98.3%. | `receipt_parser.py`, `tests/test_parser.py` |
| #15 User authentication | Household accounts with salted password hashes, per-household data isolation on every query and file, migration of existing databases. | `app.py`, `schema.sql`, `templates/login.html`, `templates/register.html`, `tests/test_auth.py` |
| #16 Dark mode | Follows `prefers-color-scheme`, toggle in the navbar, applied before paint, WCAG AA contrast checked in CI. | `static/styles.css`, `static/theme.js`, `templates/layout.html`, `scripts/check_contrast.py` |
| #20 Receipt image storage | Downscaled JPEG copies, a per-household limit, owner-only image URLs, a receipt history page, and links from items back to their receipt. | `receipt_store.py`, `templates/receipts.html`, `templates/ocr_review.html`, `tests/test_receipts.py` |

## Not planned

| Issue | Reason |
| --- | --- |
| #18 Mobile camera UX (zoom, focus, exposure) | The receipt page uses the phone's own camera app through the file picker, which already has these controls. Building them into the page would need per-browser `getUserMedia` track constraints that are unevenly supported on phones, for little gain over the native camera. |
| #19 Offline-first architecture | The service worker already serves cached pages and static files when offline. Full offline editing would need a local database plus conflict-safe sync with the server and per-household auth, which is a project of its own and out of scope for this app. |
