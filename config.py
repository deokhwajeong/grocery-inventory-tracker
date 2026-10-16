"""
Configuration settings for the Grocery Inventory Tracker application.
"""
import os
import secrets
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    """Base configuration class"""

    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(16))

    # Upload settings
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(BASE_DIR, 'uploads'))
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_UPLOAD_MB', '16')) * 1024 * 1024  # receipt photo size limit
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

    # Database settings
    DATABASE_PATH = os.environ.get('DATABASE_PATH', os.path.join(BASE_DIR, 'groceries.db'))
    SCHEMA_PATH = os.path.join(BASE_DIR, 'schema.sql')

    # Receipt images are kept for the review screen and the receipt history.
    # They are re-encoded as JPEG no larger than RECEIPT_MAX_DIMENSION pixels on
    # the long side, and only the newest RECEIPT_KEEP images per account are kept.
    RECEIPT_FOLDER = os.environ.get('RECEIPT_FOLDER', os.path.join(UPLOAD_FOLDER, 'receipts'))
    STORE_RECEIPT_IMAGES = os.environ.get('STORE_RECEIPT_IMAGES', 'true').lower() in ('true', '1', 'yes')
    RECEIPT_MAX_DIMENSION = int(os.environ.get('RECEIPT_MAX_DIMENSION', '1600'))
    RECEIPT_KEEP = int(os.environ.get('RECEIPT_KEEP', '100'))

    # Batch receipt upload: at most this many images per batch.
    BATCH_MAX_FILES = int(os.environ.get('BATCH_MAX_FILES', '10'))

    # Barcode lookup. The bundled offline catalog is always used first. Setting
    # BARCODE_ONLINE_LOOKUP=true also asks Open Food Facts for unknown codes.
    BARCODE_ONLINE_LOOKUP = os.environ.get('BARCODE_ONLINE_LOOKUP', 'false').lower() in ('true', '1', 'yes')
    BARCODE_LOOKUP_TIMEOUT = float(os.environ.get('BARCODE_LOOKUP_TIMEOUT', '4'))

    # Household accounts
    MIN_PASSWORD_LENGTH = 8

    # OCR settings
    OCR_LANGUAGES = os.environ.get('OCR_LANGUAGES', 'eng+kor')
    OCR_TIMEOUT = int(os.environ.get('OCR_TIMEOUT', '30'))  # seconds

    # Categories
    CATEGORIES = [
        'Dairy', 'Meat', 'Produce', 'Bakery',
        'Frozen', 'Pantry', 'Beverages', 'Snacks', 'Other'
    ]

    # Expiry settings
    EXPIRY_WARNING_DAYS = int(os.environ.get('EXPIRY_WARNING_DAYS', '7'))

    # Adding an item that is already in stock (same name and category) merges
    # it into the existing row when the expiry dates are at most this far apart.
    MERGE_EXPIRY_WINDOW_DAYS = int(os.environ.get('MERGE_EXPIRY_WINDOW_DAYS', '3'))

    # CSRF tokens stay valid for the whole session instead of expiring after an
    # hour, so a form left open in a tab still submits.
    WTF_CSRF_TIME_LIMIT = None

    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', os.path.join(BASE_DIR, 'app.log'))

    # Debug mode
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')

    # Server settings
    HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
    PORT = int(os.environ.get('FLASK_PORT', '5000'))

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    # In production, SECRET_KEY should always be set via environment variable
    @property
    def SECRET_KEY(self):
        key = os.environ.get('SECRET_KEY')
        if not key:
            raise ValueError("SECRET_KEY environment variable must be set in production")
        return key

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
