# Grocery Inventory Tracker

[![CI](https://github.com/deokhwajeong/grocery-inventory-tracker/actions/workflows/ci.yml/badge.svg)](https://github.com/deokhwajeong/grocery-inventory-tracker/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A Flask and SQLite web app for keeping track of what is in the fridge and pantry. Add groceries by hand or by photographing a receipt (Tesseract OCR reads the line items, you review them before saving), and the dashboard surfaces what is expired or about to expire so it gets used first. I built it as my final project for HarvardX CS50 (Introduction to Computer Science) to solve a small everyday problem: losing track of what we already have, buying duplicates, and throwing food away.

![Inventory dashboard](docs/screenshots/dashboard.png)

| Expiry warnings | Receipt OCR review |
| --- | --- |
| ![Use-these-first panel and table sorted by expiry](docs/screenshots/expiry-warnings.png) | ![Items read from a receipt, ready to review](docs/screenshots/ocr-review.png) |

| Receipt upload | Insights | Mobile |
| --- | --- | --- |
| ![Receipt upload with preview](docs/screenshots/ocr-upload.png) | ![Insights page](docs/screenshots/statistics.png) | ![Dashboard on a 390px wide phone](docs/screenshots/mobile.png) |

All screenshots use synthetic demo data from `scripts/seed_demo_data.py`.

## Features

- **Inventory CRUD.** Add, edit, and delete items with name, quantity, category (9 built-in), purchase date, expiry date, and notes. Server-side validation rejects bad quantities, malformed dates, and expiry dates before the purchase date.
- **Expiry tracking.** Each item is marked fresh, expiring soon, or expired. A "Use these first" panel lists expired items and items expiring within the warning window (7 days by default, adjustable to 3 or 14 on the Settings page).
- **Receipt scanning with OCR.** Upload or photograph a receipt. OpenCV preprocesses the image (deskew, contrast, thresholding, denoising), Tesseract extracts text, and a parser pulls out item lines, quantities such as `2x`, prices, and the purchase date while skipping totals, tax, and payment lines. Names are normalized against a small product dictionary and given a suggested category. Nothing is saved until you confirm on the review screen.
- **Search, filter, and sort** by name, category, purchase date, expiry date, or quantity.
- **Shopping list suggestions** from low-stock items, items that expired in the last week, and repeat purchases. The list itself is stored in the browser.
- **Insights page** with category distribution, monthly purchase counts, expired items by category, and average shelf life.
- **CSV export**, a one-click "clear expired items" action, and a full reset on the Settings page.
- **Installable PWA.** Web app manifest plus a service worker that serves static assets from cache and falls back to the last loaded pages when offline. With permission, the open app shows browser notifications for items expiring today or tomorrow.
- **Graceful OCR fallback.** If Tesseract is not installed the app still runs, and the scan page explains how to enable OCR. Missing language packs (for example Korean) are skipped automatically.

## Quickstart

Requirements: Python 3.12 (the version CI tests). Tesseract is optional and only needed for receipt scanning.

```bash
git clone https://github.com/deokhwajeong/grocery-inventory-tracker.git
cd grocery-inventory-tracker
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python scripts/seed_demo_data.py   # optional: load synthetic demo items
flask --app app run                # open http://127.0.0.1:5000
```

The SQLite database (`groceries.db`) and its tables are created automatically on first start. `python app.py` also works and reads host, port, and debug settings from `.env` (see `.env.example`).

To enable receipt scanning, install Tesseract:

```bash
sudo apt-get install tesseract-ocr     # Debian/Ubuntu (add tesseract-ocr-kor for Korean receipts)
brew install tesseract                 # macOS
```

### Run the tests

```bash
pip install -r requirements-dev.txt
ruff check .
pytest
```

The suite covers the routes, validation, expiry logic, the OCR review flow, the no-Tesseract fallback, and receipt parsing. One end-to-end test renders a synthetic receipt image and runs real OCR on it; it is skipped when Tesseract is not installed. GitHub Actions runs lint and tests on every push.

### Docker

```bash
export SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
docker compose up --build              # http://localhost:5000, data persists in ./data
```

The image includes Tesseract with English and Korean language packs and serves the app with gunicorn. `FLASK_ENV=production` requires `SECRET_KEY` to be set.

## Tech stack

| Layer | Tools |
| --- | --- |
| Backend | Python 3.12, Flask 3, SQLite (`sqlite3`), gunicorn |
| OCR | Tesseract via `pytesseract`, OpenCV and NumPy for preprocessing, `fuzzywuzzy` for name matching |
| Frontend | Jinja templates, Bootstrap 5.3 (vendored in `static/vendor/`), a small custom theme, vanilla JavaScript |
| PWA | Web app manifest, service worker, Notifications API |
| Quality | pytest, ruff, GitHub Actions |

## Project layout

```
app.py                 Flask routes: inventory, OCR upload/review, shopping list, insights, settings, JSON/CSV endpoints
config.py              Settings loaded from environment variables (.env supported)
schema.sql             SQLite schema (groceries table and indexes)
ocr_processor.py       Image preprocessing, Tesseract calls, receipt text parsing
ocr_advanced.py        Product name normalization, duplicate merging, category suggestions
scripts/
  seed_demo_data.py    Loads synthetic demo items with dates relative to today
templates/             Jinja templates (layout.html is the shared shell)
static/
  styles.css           App theme on top of Bootstrap
  camera-handler.js    Camera and file picker helper for the receipt page
  service-worker.js    PWA caching and notifications
  manifest.json, icons/
  vendor/bootstrap/    Bootstrap 5.3.3 CSS and JS bundle (MIT)
tests/                 pytest suite
docs/screenshots/      Images used in this README
Dockerfile, docker-compose.yml, Procfile, Aptfile, runtime.txt   Deployment configs
```

## Design notes

- **Review before save.** OCR output goes into the session and onto an editable review table, so a misread receipt never pollutes the inventory.
- **Local OCR instead of a cloud API.** Tesseract is free and keeps receipt images on the server; uploads are deleted right after processing.
- **SQLite over a database server.** Zero setup for a single household; indexes on `category` and `expiry_date` keep filtering fast.
- **Assets vendored, not loaded from a CDN.** The UI renders the same offline, behind restrictive networks, and in the PWA.

## Known limitations and roadmap

- Single household, no user accounts or authentication. Anyone who can reach the server can edit the data, so run it locally or behind your own auth.
- OCR works well on clean, printed receipts with one item per line. Crumpled photos, unusual layouts, and abbreviated product codes still need manual fixes on the review screen. Accuracy has not been benchmarked on a real receipt dataset yet.
- Expiry dates are not inferred from receipts; they are entered on the review screen or the edit form. Suggesting default shelf lives per category is a natural next step.
- The barcode page is a prototype: the camera scanner loads ZXing from a CDN and the lookup endpoint returns a placeholder name instead of querying a product database such as Open Food Facts.
- Notifications only fire while the app is open; there is no server-side push.
- The "consumed" state is not modeled, so the insights treat every item that has not expired as still in use.

## Author

Deokhwa Jeong. HarvardX CS50 final project.

## License

[MIT](LICENSE)
