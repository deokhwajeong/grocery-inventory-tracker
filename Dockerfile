FROM python:3.12-slim

WORKDIR /app

# Tesseract OCR engine with English and Korean language packs
RUN apt-get update && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-eng \
        tesseract-ocr-kor \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# The SQLite database lives in a volume so data survives container rebuilds.
# Tables are created automatically on startup.
ENV DATABASE_PATH=/app/data/groceries.db \
    FLASK_ENV=production
RUN mkdir -p /app/data

EXPOSE 5000

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000", "--workers", "1"]
