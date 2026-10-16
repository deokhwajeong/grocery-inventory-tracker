"""
Grocery Inventory Tracker - Main Application
A Flask-based web application for managing grocery inventory with OCR receipt scanning.

Every inventory row, receipt, and API response belongs to a household account
(see the auth routes below). Queries always filter on the signed-in account.
"""
import csv
import logging
import os
import sqlite3
import tempfile
from datetime import datetime
from functools import wraps
from io import StringIO

import pytesseract
from flask import (Flask, abort, flash, g, make_response, redirect, render_template, request, send_file, session,
                   url_for)
from flask_wtf.csrf import CSRFError, CSRFProtect
from PIL import Image, UnidentifiedImageError
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

import barcode_catalog
import receipt_store
from config import config
from inventory import add_or_merge
from ocr_processor import analyze_receipt_image, is_tesseract_available

# Initialize Flask app
app = Flask(__name__)

# Load configuration
env = os.environ.get('FLASK_ENV', 'development')
# Instantiate the config class so property-based settings (such as the
# production SECRET_KEY check) are evaluated instead of copied as raw
# property objects by from_object().
app.config.from_object(config.get(env, config['default'])())

# Every POST form carries a CSRF token; fetch() calls send it as X-CSRFToken.
csrf = CSRFProtect(app)

# Setup logging
logging.basicConfig(
    level=getattr(logging, app.config['LOG_LEVEL']),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(app.config['LOG_FILE']),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Categories for grocery items
CATEGORIES = app.config['CATEGORIES']

# Create upload folders if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RECEIPT_FOLDER'], exist_ok=True)
logger.info(f"Upload folder created/verified: {app.config['UPLOAD_FOLDER']}")

# Endpoints reachable without signing in
PUBLIC_ENDPOINTS = {'login', 'register', 'static'}


def allowed_file(filename):
    """True if the file name has an allowed image extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def is_image_upload(file_storage):
    """
    Check that an uploaded file really is an image Pillow can decode, not just
    a file with an image extension. The stream is rewound afterwards.
    """
    try:
        with Image.open(file_storage.stream) as img:
            img.verify()
        return True
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError):
        return False
    finally:
        file_storage.stream.seek(0)


def wants_json():
    return request.path.startswith('/api/')


@app.errorhandler(CSRFError)
def handle_csrf_error(error):
    logger.warning(f"CSRF check failed on {request.path}: {error.description}")
    if wants_json():
        return {'error': 'Missing or invalid CSRF token. Reload the page and try again.'}, 400
    flash('Your session expired or the form was out of date. Please try again.', 'error')
    return redirect(request.referrer or url_for('index'))


@app.errorhandler(RequestEntityTooLarge)
def handle_too_large(error):
    limit_mb = app.config['MAX_CONTENT_LENGTH'] // (1024 * 1024)
    if wants_json():
        return {'error': f'That file is too large. The limit is {limit_mb} MB.'}, 413
    flash(f'That file is too large. The limit is {limit_mb} MB.', 'error')
    return redirect(url_for('ocr_upload'))


# ---------------------------------------------------------------- database

def get_db_connection():
    """Create and return a database connection with Row factory."""
    try:
        conn = sqlite3.connect(app.config['DATABASE_PATH'])
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        raise


def migrate(conn):
    """Bring databases created before accounts and receipt storage up to date."""
    columns = {row['name'] for row in conn.execute('PRAGMA table_info(groceries)')}
    if 'user_id' not in columns:
        conn.execute('ALTER TABLE groceries ADD COLUMN user_id INTEGER REFERENCES users(id)')
    if 'receipt_id' not in columns:
        conn.execute('ALTER TABLE groceries ADD COLUMN receipt_id INTEGER REFERENCES receipts(id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_groceries_user ON groceries(user_id)')


def init_db():
    """Create tables and indexes if they don't exist, then run migrations."""
    try:
        conn = get_db_connection()
        with open(app.config['SCHEMA_PATH'], 'r') as f:
            conn.executescript(f.read())
        migrate(conn)
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise


# Create tables on startup so `flask run` and gunicorn work from a clean
# clone, not only `python app.py`.
init_db()


# ---------------------------------------------------------------- accounts

def current_user_id():
    return g.user['id'] if g.get('user') else None


def fetch_user(user_id):
    conn = get_db_connection()
    try:
        return conn.execute('SELECT id, username FROM users WHERE id = ?', (user_id,)).fetchone()
    finally:
        conn.close()


@app.before_request
def load_user():
    """Attach the signed-in account to g and send everyone else to the login page."""
    g.user = None
    user_id = session.get('user_id')
    if user_id is not None:
        try:
            g.user = fetch_user(user_id)
        except sqlite3.Error as e:
            logger.error(f"Could not load account {user_id}: {e}")
            if wants_json():
                return {'error': 'Internal server error'}, 500
            return render_template('error.html', message='The database is unavailable. Please try again shortly.'), 500
        if g.user is None:
            session.clear()
    if g.user is None and request.endpoint not in PUBLIC_ENDPOINTS:
        if wants_json():
            return {'error': 'Sign in required'}, 401
        return redirect(url_for('login', next=request.full_path if request.method == 'GET' else None))


@app.context_processor
def inject_user():
    return {'current_user': g.get('user')}


def safe_next(target):
    """Only follow redirects to paths on this site."""
    if target and target.startswith('/') and not target.startswith('//'):
        return target
    return url_for('index')


def sign_in(user_id):
    session.clear()  # new session on sign-in (avoids session fixation)
    session['user_id'] = user_id


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Create a household account. The first account also claims items saved before accounts existed."""
    if g.user:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')
        error = None
        if not (3 <= len(username) <= 40) or not username.replace('_', '').replace('-', '').replace('.', '').isalnum():
            error = 'Choose a username of 3 to 40 letters, digits, dots, dashes or underscores.'
        elif len(password) < app.config['MIN_PASSWORD_LENGTH']:
            error = f"Use a password of at least {app.config['MIN_PASSWORD_LENGTH']} characters."
        elif password != confirm:
            error = 'The two passwords do not match.'
        if error:
            return render_template('register.html', error=error, username=username), 400

        conn = get_db_connection()
        try:
            first_account = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0] == 0
            cur = conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                               (username, generate_password_hash(password)))
            user_id = cur.lastrowid
            if first_account:
                claimed = conn.execute('UPDATE groceries SET user_id = ? WHERE user_id IS NULL', (user_id,)).rowcount
                if claimed:
                    logger.info(f"First account claimed {claimed} existing items")
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return render_template('register.html', error='That username is taken.', username=username), 400
        conn.close()
        sign_in(user_id)
        logger.info(f"Account created: {username}")
        flash(f'Welcome, {username}! Your household inventory is ready.', 'success')
        return redirect(url_for('index'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        if user is None or not check_password_hash(user['password_hash'], password):
            logger.warning(f"Failed sign-in for '{username}'")
            return render_template('login.html', error='Wrong username or password.', username=username), 401
        sign_in(user['id'])
        return redirect(safe_next(request.form.get('next')))
    return render_template('login.html', next=request.args.get('next', ''))


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    flash('You have been signed out.', 'info')
    return redirect(url_for('login'))


def login_required(view):
    """Explicit marker for views; the before_request hook already enforces sign-in."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:  # pragma: no cover - load_user() redirects first
            return redirect(url_for('login'))
        return view(*args, **kwargs)
    return wrapped


# ---------------------------------------------------------------- inventory

def validate_grocery_item(name, quantity, purchase_date):
    """
    Validate grocery item input data.

    Returns:
        tuple: (is_valid, error_message, validated_quantity)
    """
    if not name or not quantity or not purchase_date:
        return False, 'Name, quantity, and purchase date are required', None

    try:
        qty = int(quantity)
        if qty <= 0:
            return False, 'Quantity must be a positive number', None
        if qty > 10000:
            return False, 'Quantity seems unreasonably high', None
    except ValueError:
        return False, 'Quantity must be a valid number', None

    try:
        datetime.strptime(purchase_date, '%Y-%m-%d')
    except ValueError:
        return False, 'Invalid date format. Use YYYY-MM-DD', None

    if len(name) > 100:
        return False, 'Item name is too long (max 100 characters)', None
    if len(name) < 2:
        return False, 'Item name is too short (min 2 characters)', None

    return True, None, qty


def get_item(conn, item_id):
    return conn.execute('SELECT * FROM groceries WHERE id = ? AND user_id = ?', (item_id, current_user_id())).fetchone()


@app.route('/')
@login_required
def index():
    """Inventory dashboard with search, filter, sort, and expiry status."""
    uid = current_user_id()
    try:
        search = request.args.get('search', '').strip()
        category = request.args.get('category', '')
        sort_by = request.args.get('sort', 'purchase_date')

        conn = get_db_connection()

        query = 'SELECT * FROM groceries WHERE user_id = ?'
        params = [uid]
        if search:
            query += ' AND name LIKE ?'
            params.append(f'%{search}%')
        if category:
            query += ' AND category = ?'
            params.append(category)

        # Soonest expiry and A-Z names first; newest purchases and largest
        # quantities first. Items without an expiry date sort last.
        valid_sorts = {
            'name': 'name COLLATE NOCASE ASC',
            'purchase_date': 'purchase_date DESC',
            'expiry_date': 'expiry_date IS NULL, expiry_date ASC',
            'quantity': 'quantity DESC',
            'category': 'category ASC, name COLLATE NOCASE ASC',
        }
        query += f" ORDER BY {valid_sorts.get(sort_by, valid_sorts['purchase_date'])}"
        groceries = conn.execute(query, params).fetchall()

        total_items = conn.execute('SELECT COUNT(*) FROM groceries WHERE user_id = ?', (uid,)).fetchone()[0]

        warning_days = int(session.get('expiry_warning_days', app.config['EXPIRY_WARNING_DAYS']))
        warning_window = f"+{warning_days} days"
        expiring_soon = conn.execute(
            "SELECT COUNT(*) FROM groceries WHERE user_id = ? AND expiry_date >= date('now', 'localtime') "
            "AND expiry_date <= date('now', 'localtime', ?)",
            (uid, warning_window)
        ).fetchone()[0]
        expired_count = conn.execute(
            "SELECT COUNT(*) FROM groceries WHERE user_id = ? AND expiry_date < date('now', 'localtime')", (uid,)
        ).fetchone()[0]
        use_soon = conn.execute(
            "SELECT * FROM groceries WHERE user_id = ? AND expiry_date IS NOT NULL "
            "AND expiry_date <= date('now', 'localtime', ?) ORDER BY expiry_date, name",
            (uid, warning_window)
        ).fetchall()
        categories_count = conn.execute(
            'SELECT category, COUNT(*) as count FROM groceries WHERE user_id = ? GROUP BY category', (uid,)
        ).fetchall()
        conn.close()

        today = datetime.now().date()
        items_with_expiry = []
        for item in groceries:
            item_dict = dict(item)
            if item['expiry_date']:
                try:
                    expiry = datetime.strptime(item['expiry_date'], '%Y-%m-%d').date()
                    days_left = (expiry - today).days
                    item_dict['days_until_expiry'] = days_left
                    if days_left < 0:
                        item_dict['expiry_status'] = 'expired'
                    elif days_left <= warning_days:
                        item_dict['expiry_status'] = 'warning'
                    else:
                        item_dict['expiry_status'] = 'good'
                except ValueError as e:
                    logger.warning(f"Invalid expiry date for item {item['id']}: {e}")
                    item_dict['days_until_expiry'] = None
                    item_dict['expiry_status'] = 'unknown'
            else:
                item_dict['days_until_expiry'] = None
                item_dict['expiry_status'] = 'none'
            items_with_expiry.append(item_dict)

        use_soon_items = []
        for item in use_soon:
            item_dict = dict(item)
            try:
                expiry = datetime.strptime(item['expiry_date'], '%Y-%m-%d').date()
            except ValueError:
                continue
            item_dict['days_until_expiry'] = (expiry - today).days
            use_soon_items.append(item_dict)

        logger.info(f"Dashboard loaded: {total_items} items, {expiring_soon} expiring soon")
        return render_template('index.html',
                               groceries=items_with_expiry,
                               categories=CATEGORIES,
                               total_items=total_items,
                               expiring_soon=expiring_soon,
                               expired_count=expired_count,
                               use_soon=use_soon_items,
                               warning_days=warning_days,
                               categories_count=categories_count,
                               current_search=search,
                               current_category=category,
                               current_sort=sort_by)

    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        flash('An error occurred while loading the dashboard', 'error')
        return render_template('index.html',
                               groceries=[],
                               categories=CATEGORIES,
                               total_items=0,
                               expiring_soon=0,
                               expired_count=0,
                               use_soon=[],
                               warning_days=app.config['EXPIRY_WARNING_DAYS'],
                               categories_count=[])


def check_expiry(purchase_date, expiry_date):
    """Error message for an invalid expiry date, or None."""
    if not expiry_date:
        return None
    try:
        if datetime.strptime(expiry_date, '%Y-%m-%d') < datetime.strptime(purchase_date, '%Y-%m-%d'):
            return 'Expiry date cannot be before purchase date'
    except ValueError:
        return 'Invalid expiry date format'
    return None


@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    """Add a new grocery item (or merge it into matching stock)."""
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            quantity = request.form.get('quantity', '').strip()
            purchase_date = request.form.get('purchase_date', '').strip()
            expiry_date = request.form.get('expiry_date', '').strip()
            category = request.form.get('category', 'Other')
            notes = request.form.get('notes', '').strip()

            is_valid, error_msg, validated_qty = validate_grocery_item(name, quantity, purchase_date)
            if not is_valid:
                logger.warning(f"Validation failed for add: {error_msg}")
                return render_template('add.html', error=error_msg, categories=CATEGORIES)
            error_msg = check_expiry(purchase_date, expiry_date)
            if error_msg:
                return render_template('add.html', error=error_msg, categories=CATEGORIES)
            if category not in CATEGORIES:
                category = 'Other'

            conn = get_db_connection()
            result = add_or_merge(
                conn, name, validated_qty, purchase_date, expiry_date, category, notes,
                window_days=app.config['MERGE_EXPIRY_WINDOW_DAYS'],
                merge=not request.form.get('keep_separate'),
                user_id=current_user_id(),
            )
            conn.commit()
            conn.close()

            if result.merged:
                logger.info(f"Item merged into {result.item_id}: {name} (+{validated_qty})")
                flash(f'{result.name} was already in stock, so the quantities were combined. '
                      f'You now have {result.quantity}.', 'success')
            else:
                logger.info(f"Item added: {name} (qty: {validated_qty}, category: {category})")
                flash('Item added successfully!', 'success')
            return redirect(url_for('index'))

        except sqlite3.Error as e:
            logger.error(f"Database error while adding item: {e}")
            flash('Database error occurred. Please try again.', 'error')
            return render_template('add.html', categories=CATEGORIES)

        except Exception as e:
            logger.error(f"Unexpected error while adding item: {e}")
            flash('An unexpected error occurred. Please try again.', 'error')
            return render_template('add.html', categories=CATEGORIES)

    return render_template('add.html', categories=CATEGORIES)


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit an existing grocery item of the signed-in account."""
    try:
        conn = get_db_connection()
        item = get_item(conn, id)
        if item is None:
            conn.close()
            logger.warning(f"Attempted to edit missing item {id}")
            flash('Item not found', 'error')
            return redirect(url_for('index'))
        receipt = receipt_store.get(conn, current_user_id(), item['receipt_id']) if item['receipt_id'] else None

        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            quantity = request.form.get('quantity', '').strip()
            purchase_date = request.form.get('purchase_date', '').strip()
            expiry_date = request.form.get('expiry_date', '').strip()
            category = request.form.get('category', 'Other')
            notes = request.form.get('notes', '').strip()

            is_valid, error_msg, validated_qty = validate_grocery_item(name, quantity, purchase_date)
            if is_valid:
                error_msg = check_expiry(purchase_date, expiry_date)
            if error_msg:
                logger.warning(f"Validation failed for edit item {id}: {error_msg}")
                conn.close()
                return render_template('edit.html', item=item, receipt=receipt, error=error_msg, categories=CATEGORIES)
            if category not in CATEGORIES:
                category = 'Other'

            conn.execute(
                'UPDATE groceries SET name = ?, quantity = ?, purchase_date = ?, expiry_date = ?, category = ?, notes = ? '
                'WHERE id = ? AND user_id = ?',
                (name, validated_qty, purchase_date, expiry_date or None, category, notes, id, current_user_id())
            )
            conn.commit()
            conn.close()
            logger.info(f"Item {id} updated: {name}")
            flash('Item updated successfully!', 'success')
            return redirect(url_for('index'))

        conn.close()
        return render_template('edit.html', item=item, receipt=receipt, categories=CATEGORIES)

    except sqlite3.Error as e:
        logger.error(f"Database error while editing item {id}: {e}")
        flash('Database error occurred. Please try again.', 'error')
        return redirect(url_for('index'))

    except Exception as e:
        logger.error(f"Unexpected error while editing item {id}: {e}")
        flash('An unexpected error occurred. Please try again.', 'error')
        return redirect(url_for('index'))


@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    """Delete a grocery item."""
    try:
        conn = get_db_connection()
        item = get_item(conn, id)
        if item is None:
            logger.warning(f"Attempted to delete missing item {id}")
            flash('Item not found', 'error')
            conn.close()
            return redirect(url_for('index'))
        conn.execute('DELETE FROM groceries WHERE id = ? AND user_id = ?', (id, current_user_id()))
        conn.commit()
        conn.close()
        logger.info(f"Item {id} deleted: {item['name']}")
        flash('Item deleted successfully!', 'success')

    except sqlite3.Error as e:
        logger.error(f"Database error while deleting item {id}: {e}")
        flash('Database error occurred. Please try again.', 'error')

    return redirect(url_for('index'))


@app.route('/use/<int:id>', methods=['POST'])
@login_required
def mark_used(id):
    """Mark one unit as used: the quantity goes down by one, and the item is removed at zero."""
    try:
        conn = get_db_connection()
        item = get_item(conn, id)
        if item is None:
            conn.close()
            flash('Item not found', 'error')
            return redirect(url_for('index'))

        if item['quantity'] > 1:
            conn.execute('UPDATE groceries SET quantity = quantity - 1 WHERE id = ?', (id,))
            message = f"Marked one {item['name']} as used. {item['quantity'] - 1} left."
        else:
            conn.execute('DELETE FROM groceries WHERE id = ?', (id,))
            message = f"Used the last {item['name']}. Removed it from the inventory."
        conn.commit()
        conn.close()
        logger.info(f"Item {id} used: {item['name']}")
        flash(message, 'success')

    except sqlite3.Error as e:
        logger.error(f"Database error while marking item {id} as used: {e}")
        flash('Database error occurred. Please try again.', 'error')

    return redirect(url_for('index'))


# ---------------------------------------------------------------- receipts

class UploadError(Exception):
    """A receipt upload that cannot be processed, with a message for the user."""


def scan_receipt(file_storage):
    """
    Validate, OCR, and record one uploaded receipt.

    Returns (receipt_id or None, items found, seconds). Raises UploadError with a
    user-facing message, or TesseractNotFoundError.
    """
    if not file_storage or not file_storage.filename:
        raise UploadError('No file selected')
    if not allowed_file(file_storage.filename):
        raise UploadError('Invalid file type. Please upload an image file.')
    if not is_image_upload(file_storage):
        raise UploadError('That file is not a readable image. Please upload a PNG, JPEG, or other photo.')

    original = secure_filename(file_storage.filename) or 'receipt'
    suffix = '.' + original.rsplit('.', 1)[-1].lower()
    fd, temp_path = tempfile.mkstemp(suffix=suffix, dir=app.config['UPLOAD_FOLDER'])
    os.close(fd)
    try:
        file_storage.save(temp_path)
        logger.info(f"Receipt uploaded: {original}")
        result = analyze_receipt_image(temp_path, app.config['OCR_LANGUAGES'])
        items = result.get('items', [])
        if not items:
            return None, 0, result.get('ocr_seconds')

        image_name = None
        if app.config['STORE_RECEIPT_IMAGES']:
            try:
                image_name = receipt_store.save_image(temp_path, app.config['RECEIPT_FOLDER'],
                                                      app.config['RECEIPT_MAX_DIMENSION'])
            except (OSError, ValueError) as e:
                logger.warning(f"Could not store receipt image: {e}")
        conn = get_db_connection()
        receipt_id = receipt_store.create(conn, current_user_id(), result, original, image_name)
        receipt_store.prune_images(conn, app.config['RECEIPT_FOLDER'], current_user_id(), app.config['RECEIPT_KEEP'])
        conn.commit()
        conn.close()
        logger.info(f"OCR processed: {len(items)} items found (receipt {receipt_id})")
        return receipt_id, len(items), result.get('ocr_seconds')
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def review_url(receipt_ids):
    return url_for('ocr_review', receipts=','.join(str(i) for i in receipt_ids))


@app.route('/ocr', methods=['GET', 'POST'])
@login_required
def ocr_upload():
    """
    Upload one or more receipt images (up to BATCH_MAX_FILES). Each is read
    in turn and the results open together on the review page. The page's
    script uses /api/ocr/scan instead to show progress per receipt.
    """
    if request.method == 'POST':
        files = [f for f in request.files.getlist('receipt') if f and f.filename]
        if not files:
            flash('No file selected' if 'receipt' in request.files else 'No file uploaded', 'error')
            return redirect(request.url)
        if not is_tesseract_available():
            flash('Receipt scanning needs the Tesseract OCR engine, which is not '
                  'installed on this server. You can still add items manually.', 'error')
            return redirect(request.url)
        limit = app.config['BATCH_MAX_FILES']
        if len(files) > limit:
            flash(f'Please upload at most {limit} receipts at a time.', 'error')
            return redirect(request.url)

        receipt_ids, problems, empty = [], [], 0
        for file in files:
            try:
                receipt_id, count, _ = scan_receipt(file)
                if receipt_id:
                    receipt_ids.append(receipt_id)
                else:
                    empty += 1
            except UploadError as e:
                problems.append(str(e))
            except pytesseract.TesseractNotFoundError:
                flash('Tesseract OCR is not installed on this server.', 'error')
                return redirect(request.url)
            except Exception as e:
                logger.error(f"Error processing receipt: {e}")
                problems.append('Could not read that receipt. Please try a clearer photo or add items manually.')

        for message in dict.fromkeys(problems):
            flash(message, 'error')
        if receipt_ids:
            total = sum(len(r['items']) for r in _pending(receipt_ids))
            note = f' from {len(receipt_ids)} receipts' if len(receipt_ids) > 1 else ''
            flash(f'Found {total} items{note}. Please review and edit before saving.', 'info')
            return redirect(review_url(receipt_ids))
        if empty:
            logger.warning("No items found in receipt")
            flash('No items found in receipt. Please try again or add manually.', 'warning')
            return render_template('ocr.html', ocr_available=True, batch_limit=limit)
        return redirect(request.url)

    return render_template('ocr.html', ocr_available=is_tesseract_available(), batch_limit=app.config['BATCH_MAX_FILES'])


@app.route('/api/ocr/scan', methods=['POST'])
@login_required
def api_scan_receipt():
    """Read one receipt image. Used by the upload page to process a batch one file at a time."""
    if not is_tesseract_available():
        return {'error': 'Tesseract OCR is not installed on this server.'}, 503
    try:
        receipt_id, count, seconds = scan_receipt(request.files.get('receipt'))
    except RequestEntityTooLarge:
        raise  # handled by handle_too_large()
    except UploadError as e:
        return {'error': str(e)}, 400
    except Exception as e:
        logger.error(f"Error processing receipt: {e}")
        return {'error': 'Could not read that receipt.'}, 500
    if not receipt_id:
        return {'receipt_id': None, 'items': 0, 'message': 'No items found on this receipt.'}
    return {'receipt_id': receipt_id, 'items': count, 'seconds': round(seconds or 0, 2),
            'review_url': review_url([receipt_id])}


def _parse_ids(raw):
    ids = []
    for part in (raw or '').split(','):
        if part.strip().isdigit():
            ids.append(int(part))
    return list(dict.fromkeys(ids))[:50]


def _pending(receipt_ids):
    conn = get_db_connection()
    receipts = receipt_store.pending(conn, current_user_id(), receipt_ids)
    conn.close()
    return receipts


@app.route('/ocr/review', methods=['GET', 'POST'])
@login_required
def ocr_review():
    """Review items read from one or more receipts and choose which to add."""
    receipt_ids = _parse_ids(request.values.get('receipts'))
    receipts = _pending(receipt_ids)
    if not receipts:
        logger.warning("OCR review opened without pending receipts")
        flash('No OCR items to review', 'warning')
        return redirect(url_for('ocr_upload'))

    # One flat list of rows; each row remembers the receipt it came from.
    rows = [(r, item) for r in receipts for item in r['items']]

    if request.method == 'POST':
        if request.form.get('action') == 'discard':
            conn = get_db_connection()
            for r in receipts:
                receipt_store.mark(conn, current_user_id(), r['id'], 'discarded')
            conn.commit()
            conn.close()
            flash('Scan discarded. Nothing was added.', 'info')
            return redirect(url_for('ocr_upload'))

        selected_indices = request.form.getlist('selected')
        if not selected_indices:
            flash('No items selected', 'warning')
            return redirect(review_url(receipt_ids))
        try:
            conn = get_db_connection()
            added_count = merged_count = 0
            per_receipt = {r['id']: 0 for r in receipts}
            errors = []
            for idx in selected_indices:
                try:
                    i = int(idx)
                    if not 0 <= i < len(rows):
                        continue
                    receipt, item = rows[i]
                    name = request.form.get(f'name_{i}', item['name']).strip()
                    quantity = request.form.get(f'quantity_{i}', str(item['quantity'])).strip()
                    purchase_date = request.form.get(f'purchase_date_{i}', item.get('purchase_date', '')).strip()
                    expiry_date = request.form.get(f'expiry_date_{i}', '').strip()
                    category = request.form.get(f'category_{i}', 'Other')

                    is_valid, error_msg, validated_qty = validate_grocery_item(name, quantity, purchase_date)
                    if is_valid:
                        error_msg = check_expiry(purchase_date, expiry_date)
                    if error_msg:
                        errors.append(f"{name}: {error_msg}")
                        continue
                    if category not in CATEGORIES:
                        category = 'Other'
                    result = add_or_merge(
                        conn, name, validated_qty, purchase_date, expiry_date, category,
                        window_days=app.config['MERGE_EXPIRY_WINDOW_DAYS'],
                        user_id=current_user_id(), receipt_id=receipt['id'],
                    )
                    added_count += 1
                    merged_count += int(result.merged)
                    per_receipt[receipt['id']] += 1
                except ValueError as e:
                    logger.warning(f"Error processing OCR item {idx}: {e}")
                    errors.append(f"Item {idx}: Invalid data")

            for rid, count in per_receipt.items():
                receipt_store.mark(conn, current_user_id(), rid, 'imported', count)
            conn.commit()
            conn.close()

            if added_count > 0:
                logger.info(f"OCR review completed: {added_count} items added")
                merged_note = f' ({merged_count} combined with items already in stock)' if merged_count else ''
                flash(f'Successfully added {added_count} items{merged_note}!', 'success')
            if errors:
                logger.warning(f"OCR review had {len(errors)} errors")
                flash(f'{len(errors)} items had errors and were not added', 'warning')
            return redirect(url_for('index'))

        except sqlite3.Error as e:
            logger.error(f"Database error during OCR review: {e}")
            flash('Database error occurred. Please try again.', 'error')
            return redirect(review_url(receipt_ids))

    return render_template('ocr_review.html', receipts=receipts, rows=rows, categories=CATEGORIES,
                           receipt_ids=','.join(str(r['id']) for r in receipts))


@app.route('/receipts')
@login_required
def receipts():
    """History of scanned receipts with their stored images."""
    conn = get_db_connection()
    rows = receipt_store.history(conn, current_user_id())
    conn.close()
    return render_template('receipts.html', receipts=rows, keep=app.config['RECEIPT_KEEP'],
                           max_dimension=app.config['RECEIPT_MAX_DIMENSION'],
                           storing=app.config['STORE_RECEIPT_IMAGES'])


@app.route('/receipts/<int:receipt_id>/image')
@login_required
def receipt_image(receipt_id):
    conn = get_db_connection()
    row = receipt_store.get(conn, current_user_id(), receipt_id)
    conn.close()
    path = receipt_store.image_path(app.config['RECEIPT_FOLDER'], row['image_filename']) if row else None
    if not path:
        abort(404)
    response = send_file(path, mimetype='image/jpeg', max_age=3600)
    response.headers['Cache-Control'] = 'private, max-age=3600'
    return response


@app.route('/receipts/<int:receipt_id>/delete', methods=['POST'])
@login_required
def delete_receipt(receipt_id):
    conn = get_db_connection()
    deleted = receipt_store.delete(conn, app.config['RECEIPT_FOLDER'], current_user_id(), receipt_id)
    conn.commit()
    conn.close()
    flash('Receipt deleted. Items already added to the inventory were kept.' if deleted else 'Receipt not found',
          'success' if deleted else 'error')
    return redirect(url_for('receipts'))


# ---------------------------------------------------------------- other pages and APIs

@app.route('/api/notifications/check', methods=['GET'])
@login_required
def check_notifications():
    """Items expiring today, tomorrow, and within three days."""
    uid = current_user_id()
    try:
        conn = get_db_connection()
        today_items = conn.execute(
            "SELECT * FROM groceries WHERE user_id = ? AND expiry_date = date('now', 'localtime') ORDER BY name", (uid,)
        ).fetchall()
        tomorrow_items = conn.execute(
            "SELECT * FROM groceries WHERE user_id = ? AND expiry_date = date('now', 'localtime', '+1 day') ORDER BY name",
            (uid,)
        ).fetchall()
        soon_items = conn.execute(
            "SELECT * FROM groceries WHERE user_id = ? AND expiry_date > date('now', 'localtime', '+1 day') "
            "AND expiry_date <= date('now', 'localtime', '+3 days') ORDER BY expiry_date, name", (uid,)
        ).fetchall()
        conn.close()
        return {
            'today': [dict(item) for item in today_items],
            'tomorrow': [dict(item) for item in tomorrow_items],
            'soon': [dict(item) for item in soon_items]
        }
    except Exception as e:
        logger.error(f"Error checking notifications: {e}")
        return {'error': 'Internal server error'}, 500


@app.route('/shopping-list')
@login_required
def shopping_list():
    """Suggestions: low stock, recently expired, and frequently bought items."""
    uid = current_user_id()
    try:
        conn = get_db_connection()
        low_stock = conn.execute(
            'SELECT * FROM groceries WHERE user_id = ? AND quantity <= 2 AND quantity > 0 ORDER BY quantity ASC', (uid,)
        ).fetchall()
        expired_recent = conn.execute(
            "SELECT * FROM groceries WHERE user_id = ? AND expiry_date < date('now', 'localtime') "
            "AND expiry_date >= date('now', 'localtime', '-7 days') ORDER BY expiry_date DESC", (uid,)
        ).fetchall()
        frequently_purchased = conn.execute(
            '''SELECT name, category, COUNT(*) as purchase_count,
               MAX(purchase_date) as last_purchase
               FROM groceries
               WHERE user_id = ?
               GROUP BY LOWER(name)
               HAVING purchase_count >= 2
               ORDER BY purchase_count DESC, last_purchase DESC
               LIMIT 10''', (uid,)
        ).fetchall()
        conn.close()
        return render_template('shopping_list.html',
                               low_stock=low_stock,
                               expired_recent=expired_recent,
                               frequently_purchased=frequently_purchased,
                               categories=CATEGORIES)

    except Exception as e:
        logger.error(f"Error loading shopping list: {e}")
        flash('An error occurred while loading the shopping list', 'error')
        return redirect(url_for('index'))


@app.route('/statistics')
@login_required
def statistics():
    """Category distribution, monthly trends, and waste tracking."""
    uid = current_user_id()
    try:
        conn = get_db_connection()
        category_stats = conn.execute(
            '''SELECT category, COUNT(*) as item_count, SUM(quantity) as total_quantity
               FROM groceries WHERE user_id = ?
               GROUP BY category
               ORDER BY item_count DESC''', (uid,)
        ).fetchall()
        monthly_trends = conn.execute(
            '''SELECT strftime('%Y-%m', purchase_date) as month,
               COUNT(*) as items_added, SUM(quantity) as total_quantity
               FROM groceries
               WHERE user_id = ? AND purchase_date >= date('now', 'localtime', '-6 months')
               GROUP BY month
               ORDER BY month DESC''', (uid,)
        ).fetchall()
        waste_stats = conn.execute(
            '''SELECT category, COUNT(*) as expired_count, SUM(quantity) as wasted_quantity
               FROM groceries
               WHERE user_id = ? AND expiry_date < date('now', 'localtime')
               GROUP BY category
               ORDER BY expired_count DESC''', (uid,)
        ).fetchall()
        total_waste = conn.execute(
            "SELECT COUNT(*) as count FROM groceries WHERE user_id = ? AND expiry_date < date('now', 'localtime')", (uid,)
        ).fetchone()['count']
        items_saved = conn.execute(
            '''SELECT COUNT(*) as count FROM groceries
               WHERE user_id = ? AND (expiry_date >= date('now', 'localtime') OR expiry_date IS NULL)''', (uid,)
        ).fetchone()['count']
        avg_shelf_life = conn.execute(
            '''SELECT AVG(JULIANDAY(expiry_date) - JULIANDAY(purchase_date)) as avg_days
               FROM groceries
               WHERE user_id = ? AND expiry_date IS NOT NULL AND purchase_date IS NOT NULL''', (uid,)
        ).fetchone()['avg_days']
        conn.close()

        total_items = total_waste + items_saved
        waste_reduction = (items_saved / total_items * 100) if total_items > 0 else 0
        return render_template('statistics.html',
                               category_stats=category_stats,
                               monthly_trends=monthly_trends,
                               waste_stats=waste_stats,
                               total_waste=total_waste,
                               items_saved=items_saved,
                               waste_reduction=waste_reduction,
                               avg_shelf_life=avg_shelf_life)

    except Exception as e:
        logger.error(f"Error loading statistics: {e}")
        flash('An error occurred while loading statistics', 'error')
        return redirect(url_for('index'))


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Notification preferences and data management."""
    if request.method == 'POST':
        session['notifications_enabled'] = request.form.get('notifications_enabled') == 'on'
        session['notification_time'] = request.form.get('notification_time', '09:00')
        try:
            warning_days = int(request.form.get('expiry_warning_days', 7))
        except ValueError:
            warning_days = 7
        session['expiry_warning_days'] = min(max(warning_days, 1), 30)
        flash('Settings saved successfully!', 'success')
        return redirect(url_for('settings'))

    return render_template('settings.html',
                           notifications_enabled=session.get('notifications_enabled', True),
                           notification_time=session.get('notification_time', '09:00'),
                           expiry_warning_days=session.get('expiry_warning_days', app.config['EXPIRY_WARNING_DAYS']))


@app.route('/barcode')
@login_required
def barcode():
    """Barcode scanner page for quick product addition."""
    return render_template('barcode.html', categories=CATEGORIES,
                           sample_codes=barcode_catalog.sample_codes(),
                           online_lookup=app.config['BARCODE_ONLINE_LOOKUP'])


@app.route('/api/export')
@login_required
def export_data():
    """Export the account's inventory as CSV."""
    try:
        conn = get_db_connection()
        groceries = conn.execute('SELECT * FROM groceries WHERE user_id = ? ORDER BY purchase_date DESC',
                                 (current_user_id(),)).fetchall()
        conn.close()
        si = StringIO()
        writer = csv.writer(si)
        writer.writerow(['ID', 'Name', 'Quantity', 'Category', 'Purchase Date', 'Expiry Date', 'Notes'])
        for item in groceries:
            writer.writerow([item['id'], item['name'], item['quantity'], item['category'], item['purchase_date'],
                             item['expiry_date'] or '', item['notes'] or ''])
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=grocery_inventory.csv"
        output.headers["Content-type"] = "text/csv"
        return output

    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        return {'error': 'Internal server error'}, 500


@app.route('/api/clear-expired', methods=['POST'])
@login_required
def clear_expired():
    """Remove the account's expired items."""
    try:
        conn = get_db_connection()
        result = conn.execute("DELETE FROM groceries WHERE user_id = ? AND expiry_date < date('now', 'localtime')",
                              (current_user_id(),))
        count = result.rowcount
        conn.commit()
        conn.close()
        logger.info(f"Cleared {count} expired items")
        return {'success': True, 'count': count}

    except Exception as e:
        logger.error(f"Error clearing expired items: {e}")
        return {'error': 'Internal server error'}, 500


@app.route('/api/reset', methods=['POST'])
@login_required
def reset_data():
    """Delete all of the account's items (other households are untouched)."""
    try:
        conn = get_db_connection()
        conn.execute('DELETE FROM groceries WHERE user_id = ?', (current_user_id(),))
        conn.commit()
        conn.close()
        logger.warning(f"All data reset for account {current_user_id()}")
        return {'success': True}

    except Exception as e:
        logger.error(f"Error resetting data: {e}")
        return {'error': 'Internal server error'}, 500


@app.route('/api/share/<int:item_id>')
@login_required
def share_item(item_id):
    """Item details for the share button."""
    try:
        conn = get_db_connection()
        item = get_item(conn, item_id)
        conn.close()
        if not item:
            return {'error': 'Item not found'}, 404
        return {
            'id': item['id'],
            'name': item['name'],
            'quantity': item['quantity'],
            'category': item['category'],
            'expiry_date': item['expiry_date'],
        }

    except Exception as e:
        logger.error(f"Error sharing item: {e}")
        return {'error': 'Internal server error'}, 500


@app.route('/api/barcode/<barcode_number>')
@login_required
def barcode_lookup(barcode_number):
    """
    Look up a barcode. The bundled offline catalog (barcode_catalog.py) is
    checked first. When BARCODE_ONLINE_LOOKUP is on, unknown codes are also
    looked up on Open Food Facts; if that is off, slow, or unreachable, the
    user simply enters the details by hand.
    """
    code = barcode_number.strip()
    if not barcode_catalog.is_valid_gtin(code):
        return {
            'barcode': code,
            'found': False,
            'error': 'Enter an 8, 12, 13, or 14 digit barcode with a valid check digit.',
        }, 400

    product = barcode_catalog.lookup(code)
    source = barcode_catalog.SOURCE
    online = app.config['BARCODE_ONLINE_LOOKUP']
    if product is None and online:
        product = barcode_catalog.lookup_online(code, timeout=app.config['BARCODE_LOOKUP_TIMEOUT'])
        source = barcode_catalog.ONLINE_SOURCE
    if product is None:
        message = ('Not found in the local catalog or on Open Food Facts. Enter the product details manually.'
                   if online else 'Not in the local catalog. Enter the product details manually.')
        return {'barcode': code, 'found': False, 'online': online, 'message': message}, 404

    return {
        'barcode': code,
        'found': True,
        'name': product['name'],
        'category': product['category'],
        'source': source,
    }


if __name__ == '__main__':
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )
