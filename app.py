"""
Grocery Inventory Tracker - Main Application
A Flask-based web application for managing grocery inventory with OCR receipt scanning.
"""
import sqlite3
import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from ocr_processor import process_receipt_image
from config import config

# Initialize Flask app
app = Flask(__name__)

# Load configuration
env = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(config.get(env, config['default']))

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

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
logger.info(f"Upload folder created/verified: {app.config['UPLOAD_FOLDER']}")

def allowed_file(filename):
    """
    Check if uploaded file has an allowed extension.
    
    Args:
        filename (str): Name of the uploaded file
        
    Returns:
        bool: True if file extension is allowed, False otherwise
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Database connection helper
def get_db_connection():
    """
    Create and return a database connection.
    
    Returns:
        sqlite3.Connection: Database connection with Row factory
    """
    try:
        conn = sqlite3.connect(app.config['DATABASE_PATH'])
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        raise

# Initialize database
def init_db():
    """
    Initialize the database using the schema file.
    Creates tables and indexes if they don't exist.
    """
    try:
        conn = get_db_connection()
        with open(app.config['SCHEMA_PATH'], 'r') as f:
            conn.executescript(f.read())
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise

def validate_grocery_item(name, quantity, purchase_date):
    """
    Validate grocery item input data.
    
    Args:
        name (str): Item name
        quantity (str): Item quantity
        purchase_date (str): Purchase date in YYYY-MM-DD format
        
    Returns:
        tuple: (is_valid, error_message, validated_quantity)
    """
    # Check required fields
    if not name or not quantity or not purchase_date:
        return False, 'Name, quantity, and purchase date are required', None
    
    # Validate quantity
    try:
        qty = int(quantity)
        if qty <= 0:
            return False, 'Quantity must be a positive number', None
        if qty > 10000:
            return False, 'Quantity seems unreasonably high', None
    except ValueError:
        return False, 'Quantity must be a valid number', None
    
    # Validate purchase date format
    try:
        datetime.strptime(purchase_date, '%Y-%m-%d')
    except ValueError:
        return False, 'Invalid date format. Use YYYY-MM-DD', None
    
    # Validate name length
    if len(name) > 100:
        return False, 'Item name is too long (max 100 characters)', None
    if len(name) < 2:
        return False, 'Item name is too short (min 2 characters)', None
    
    return True, None, qty


@app.route('/')
def index():
    """
    Display the grocery inventory dashboard with search, filter, and sort capabilities.
    Shows statistics and expiry status for all items.
    """
    try:
        # Get filter parameters
        search = request.args.get('search', '').strip()
        category = request.args.get('category', '')
        sort_by = request.args.get('sort', 'purchase_date')
        
        conn = get_db_connection()
        
        # Build query with parameterized statements for security
        query = 'SELECT * FROM groceries WHERE 1=1'
        params = []
        
        if search:
            query += ' AND name LIKE ?'
            params.append(f'%{search}%')
        
        if category:
            query += ' AND category = ?'
            params.append(category)
        
        # Add sorting with whitelist validation
        valid_sorts = ['name', 'purchase_date', 'expiry_date', 'quantity', 'category']
        if sort_by in valid_sorts:
            query += f' ORDER BY {sort_by} DESC'
        else:
            query += ' ORDER BY purchase_date DESC'
        
        groceries = conn.execute(query, params).fetchall()
        
        # Get statistics
        total_items = conn.execute('SELECT COUNT(*) FROM groceries').fetchone()[0]
        
        expiring_soon = conn.execute(
            f'SELECT COUNT(*) FROM groceries WHERE expiry_date IS NOT NULL AND expiry_date <= date("now", "+{app.config["EXPIRY_WARNING_DAYS"]} days")'
        ).fetchone()[0]
        
        categories_count = conn.execute(
            'SELECT category, COUNT(*) as count FROM groceries GROUP BY category'
        ).fetchall()
        
        conn.close()
        
        # Calculate days until expiry for each item
        today = datetime.now().date()
        items_with_expiry = []
        
        for item in groceries:
            item_dict = dict(item)
            if item['expiry_date']:
                try:
                    expiry = datetime.strptime(item['expiry_date'], '%Y-%m-%d').date()
                    days_left = (expiry - today).days
                    item_dict['days_until_expiry'] = days_left
                    
                    # Determine expiry status
                    if days_left < 0:
                        item_dict['expiry_status'] = 'expired'
                    elif days_left <= app.config['EXPIRY_WARNING_DAYS']:
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
        
        logger.info(f"Dashboard loaded: {total_items} items, {expiring_soon} expiring soon")
        
        return render_template('index.html', 
                             groceries=items_with_expiry,
                             categories=CATEGORIES,
                             total_items=total_items,
                             expiring_soon=expiring_soon,
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
                             categories_count=[])


@app.route('/add', methods=['GET', 'POST'])
def add():
    """
    Add a new grocery item to the inventory.
    GET: Display the add item form
    POST: Process form submission and insert into database
    """
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            quantity = request.form.get('quantity', '').strip()
            purchase_date = request.form.get('purchase_date', '').strip()
            expiry_date = request.form.get('expiry_date', '').strip()
            category = request.form.get('category', 'Other')
            notes = request.form.get('notes', '').strip()
            
            # Validate input
            is_valid, error_msg, validated_qty = validate_grocery_item(name, quantity, purchase_date)
            if not is_valid:
                logger.warning(f"Validation failed for add: {error_msg}")
                return render_template('add.html', error=error_msg, categories=CATEGORIES)
            
            # Validate expiry date if provided
            if expiry_date:
                try:
                    expiry_dt = datetime.strptime(expiry_date, '%Y-%m-%d')
                    purchase_dt = datetime.strptime(purchase_date, '%Y-%m-%d')
                    if expiry_dt < purchase_dt:
                        return render_template('add.html', 
                                             error='Expiry date cannot be before purchase date', 
                                             categories=CATEGORIES)
                except ValueError:
                    return render_template('add.html', 
                                         error='Invalid expiry date format', 
                                         categories=CATEGORIES)
            
            # Validate category
            if category not in CATEGORIES:
                category = 'Other'
            
            # Insert into database
            conn = get_db_connection()
            conn.execute(
                'INSERT INTO groceries (name, quantity, purchase_date, expiry_date, category, notes) VALUES (?, ?, ?, ?, ?, ?)',
                (name, validated_qty, purchase_date, expiry_date if expiry_date else None, category, notes)
            )
            conn.commit()
            conn.close()
            
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
def edit(id):
    """
    Edit an existing grocery item.
    
    Args:
        id (int): Database ID of the item to edit
    """
    try:
        conn = get_db_connection()
        
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            quantity = request.form.get('quantity', '').strip()
            purchase_date = request.form.get('purchase_date', '').strip()
            expiry_date = request.form.get('expiry_date', '').strip()
            category = request.form.get('category', 'Other')
            notes = request.form.get('notes', '').strip()
            
            # Validate input
            is_valid, error_msg, validated_qty = validate_grocery_item(name, quantity, purchase_date)
            if not is_valid:
                logger.warning(f"Validation failed for edit item {id}: {error_msg}")
                item = conn.execute('SELECT * FROM groceries WHERE id = ?', (id,)).fetchone()
                return render_template('edit.html', item=item, error=error_msg, categories=CATEGORIES)
            
            # Validate expiry date if provided
            if expiry_date:
                try:
                    expiry_dt = datetime.strptime(expiry_date, '%Y-%m-%d')
                    purchase_dt = datetime.strptime(purchase_date, '%Y-%m-%d')
                    if expiry_dt < purchase_dt:
                        item = conn.execute('SELECT * FROM groceries WHERE id = ?', (id,)).fetchone()
                        return render_template('edit.html', item=item,
                                             error='Expiry date cannot be before purchase date',
                                             categories=CATEGORIES)
                except ValueError:
                    item = conn.execute('SELECT * FROM groceries WHERE id = ?', (id,)).fetchone()
                    return render_template('edit.html', item=item,
                                         error='Invalid expiry date format',
                                         categories=CATEGORIES)
            
            # Validate category
            if category not in CATEGORIES:
                category = 'Other'
            
            # Update database
            conn.execute(
                'UPDATE groceries SET name = ?, quantity = ?, purchase_date = ?, expiry_date = ?, category = ?, notes = ? WHERE id = ?',
                (name, validated_qty, purchase_date, expiry_date if expiry_date else None, category, notes, id)
            )
            conn.commit()
            conn.close()
            
            logger.info(f"Item {id} updated: {name}")
            flash('Item updated successfully!', 'success')
            return redirect(url_for('index'))
        
        # GET request - fetch item
        item = conn.execute('SELECT * FROM groceries WHERE id = ?', (id,)).fetchone()
        conn.close()
        
        if item is None:
            logger.warning(f"Attempted to edit non-existent item {id}")
            flash('Item not found', 'error')
            return redirect(url_for('index'))
        
        return render_template('edit.html', item=item, categories=CATEGORIES)
    
    except sqlite3.Error as e:
        logger.error(f"Database error while editing item {id}: {e}")
        flash('Database error occurred. Please try again.', 'error')
        return redirect(url_for('index'))
    
    except Exception as e:
        logger.error(f"Unexpected error while editing item {id}: {e}")
        flash('An unexpected error occurred. Please try again.', 'error')
        return redirect(url_for('index'))


@app.route('/delete/<int:id>')
def delete(id):
    """
    Delete a grocery item from the inventory.
    
    Args:
        id (int): Database ID of the item to delete
    """
    try:
        conn = get_db_connection()
        
        # Check if item exists
        item = conn.execute('SELECT name FROM groceries WHERE id = ?', (id,)).fetchone()
        if item is None:
            logger.warning(f"Attempted to delete non-existent item {id}")
            flash('Item not found', 'error')
            conn.close()
            return redirect(url_for('index'))
        
        # Delete the item
        conn.execute('DELETE FROM groceries WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        
        logger.info(f"Item {id} deleted: {item['name']}")
        flash('Item deleted successfully!', 'success')
        
    except sqlite3.Error as e:
        logger.error(f"Database error while deleting item {id}: {e}")
        flash('Database error occurred. Please try again.', 'error')
    
    except Exception as e:
        logger.error(f"Unexpected error while deleting item {id}: {e}")
        flash('An unexpected error occurred. Please try again.', 'error')
    
    return redirect(url_for('index'))


@app.route('/ocr', methods=['GET', 'POST'])
def ocr_upload():
    """
    Upload and process receipt image using OCR.
    Extracts grocery items and stores them in session for review.
    """
    if request.method == 'POST':
        try:
            # Check if file is present
            if 'receipt' not in request.files:
                flash('No file uploaded', 'error')
                return redirect(request.url)
            
            file = request.files['receipt']
            
            # Check if file is selected
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(request.url)
            
            if file and allowed_file(file.filename):
                # Save file with secure filename
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                try:
                    file.save(filepath)
                    logger.info(f"Receipt uploaded: {filename}")
                    
                    # Process with OCR
                    items = process_receipt_image(filepath)
                    
                    if items:
                        # Store items in session for review
                        session['ocr_items'] = items
                        logger.info(f"OCR processed: {len(items)} items found")
                        flash(f'Found {len(items)} items. Please review and edit before saving.', 'info')
                        return redirect(url_for('ocr_review'))
                    else:
                        logger.warning("No items found in receipt")
                        flash('No items found in receipt. Please try again or add manually.', 'warning')
                        return render_template('ocr.html')
                
                except Exception as e:
                    logger.error(f"Error processing receipt: {e}")
                    flash(f'Error processing receipt: {str(e)}', 'error')
                    return redirect(request.url)
                
                finally:
                    # Clean up uploaded file
                    if os.path.exists(filepath):
                        try:
                            os.remove(filepath)
                            logger.debug(f"Cleaned up file: {filename}")
                        except OSError as e:
                            logger.warning(f"Failed to delete uploaded file {filename}: {e}")
            else:
                flash('Invalid file type. Please upload an image file.', 'error')
                return redirect(request.url)
        
        except Exception as e:
            logger.error(f"Unexpected error in OCR upload: {e}")
            flash('An unexpected error occurred. Please try again.', 'error')
            return redirect(request.url)
    
    return render_template('ocr.html')


@app.route('/ocr/review', methods=['GET', 'POST'])
def ocr_review():
    """
    Review and edit OCR-extracted items before adding to inventory.
    Allows users to select which items to import and modify their details.
    """
    if 'ocr_items' not in session:
        logger.warning("OCR review accessed without items in session")
        flash('No OCR items to review', 'warning')
        return redirect(url_for('ocr_upload'))
    
    if request.method == 'POST':
        try:
            # Get selected items
            selected_indices = request.form.getlist('selected')
            items = session.get('ocr_items', [])
            
            if not selected_indices:
                flash('No items selected', 'warning')
                return redirect(url_for('ocr_review'))
            
            conn = get_db_connection()
            added_count = 0
            errors = []
            
            for idx in selected_indices:
                try:
                    i = int(idx)
                    if i >= len(items):
                        continue
                    
                    # Get edited values
                    name = request.form.get(f'name_{i}', items[i]['name']).strip()
                    quantity = request.form.get(f'quantity_{i}', str(items[i]['quantity'])).strip()
                    purchase_date = request.form.get(f'purchase_date_{i}', items[i]['purchase_date']).strip()
                    expiry_date = request.form.get(f'expiry_date_{i}', '').strip()
                    category = request.form.get(f'category_{i}', 'Other')
                    
                    # Validate item
                    is_valid, error_msg, validated_qty = validate_grocery_item(name, quantity, purchase_date)
                    if not is_valid:
                        errors.append(f"{name}: {error_msg}")
                        continue
                    
                    # Validate category
                    if category not in CATEGORIES:
                        category = 'Other'
                    
                    # Insert into database
                    conn.execute(
                        'INSERT INTO groceries (name, quantity, purchase_date, expiry_date, category) VALUES (?, ?, ?, ?, ?)',
                        (name, validated_qty, purchase_date, expiry_date if expiry_date else None, category)
                    )
                    added_count += 1
                    
                except (ValueError, IndexError) as e:
                    logger.warning(f"Error processing OCR item {idx}: {e}")
                    errors.append(f"Item {idx}: Invalid data")
                    continue
            
            conn.commit()
            conn.close()
            
            # Clear session
            session.pop('ocr_items', None)
            
            # Provide feedback
            if added_count > 0:
                logger.info(f"OCR review completed: {added_count} items added")
                flash(f'Successfully added {added_count} items!', 'success')
            
            if errors:
                logger.warning(f"OCR review had {len(errors)} errors")
                flash(f'{len(errors)} items had errors and were not added', 'warning')
            
            return redirect(url_for('index'))
        
        except sqlite3.Error as e:
            logger.error(f"Database error during OCR review: {e}")
            flash('Database error occurred. Please try again.', 'error')
            return redirect(url_for('ocr_review'))
        
        except Exception as e:
            logger.error(f"Unexpected error during OCR review: {e}")
            flash('An unexpected error occurred. Please try again.', 'error')
            return redirect(url_for('ocr_review'))
    
    items = session.get('ocr_items', [])
    return render_template('ocr_review.html', items=items, categories=CATEGORIES)


@app.route('/api/notifications/check', methods=['GET'])
def check_notifications():
    """
    API endpoint to check for items that need notifications.
    Returns items expiring today and tomorrow.
    """
    try:
        conn = get_db_connection()
        
        # Items expiring today
        today_items = conn.execute(
            'SELECT * FROM groceries WHERE expiry_date = date("now") ORDER BY name'
        ).fetchall()
        
        # Items expiring tomorrow
        tomorrow_items = conn.execute(
            'SELECT * FROM groceries WHERE expiry_date = date("now", "+1 day") ORDER BY name'
        ).fetchall()
        
        # Items expiring within 3 days
        soon_items = conn.execute(
            'SELECT * FROM groceries WHERE expiry_date > date("now", "+1 day") AND expiry_date <= date("now", "+3 days") ORDER BY expiry_date, name'
        ).fetchall()
        
        conn.close()
        
        return {
            'today': [dict(item) for item in today_items],
            'tomorrow': [dict(item) for item in tomorrow_items],
            'soon': [dict(item) for item in soon_items]
        }
    except Exception as e:
        logger.error(f"Error checking notifications: {e}")
        return {'error': str(e)}, 500


@app.route('/shopping-list')
def shopping_list():
    """
    Smart shopping list that automatically suggests items based on:
    - Items that are running low (quantity <= 2)
    - Items that expired recently (might need replacement)
    - Frequently purchased items
    """
    try:
        conn = get_db_connection()
        
        # Low stock items
        low_stock = conn.execute(
            'SELECT * FROM groceries WHERE quantity <= 2 AND quantity > 0 ORDER BY quantity ASC'
        ).fetchall()
        
        # Recently expired items (last 7 days)
        expired_recent = conn.execute(
            'SELECT * FROM groceries WHERE expiry_date < date("now") AND expiry_date >= date("now", "-7 days") ORDER BY expiry_date DESC'
        ).fetchall()
        
        # Frequently purchased items (appears more than 3 times in history)
        # This is a simplified version - in production you'd have a purchase history table
        frequently_purchased = conn.execute(
            '''SELECT name, category, COUNT(*) as purchase_count, 
               MAX(purchase_date) as last_purchase
               FROM groceries 
               GROUP BY LOWER(name) 
               HAVING purchase_count >= 2
               ORDER BY purchase_count DESC, last_purchase DESC
               LIMIT 10'''
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
def statistics():
    """
    Advanced statistics and insights dashboard.
    Shows spending patterns, waste tracking, and inventory trends.
    """
    try:
        conn = get_db_connection()
        
        # Category distribution
        category_stats = conn.execute(
            '''SELECT category, COUNT(*) as item_count, SUM(quantity) as total_quantity
               FROM groceries 
               GROUP BY category 
               ORDER BY item_count DESC'''
        ).fetchall()
        
        # Monthly purchase trends (last 6 months)
        monthly_trends = conn.execute(
            '''SELECT strftime('%Y-%m', purchase_date) as month, 
               COUNT(*) as items_added, SUM(quantity) as total_quantity
               FROM groceries 
               WHERE purchase_date >= date('now', '-6 months')
               GROUP BY month 
               ORDER BY month DESC'''
        ).fetchall()
        
        # Waste tracking - expired items
        waste_stats = conn.execute(
            '''SELECT category, COUNT(*) as expired_count, SUM(quantity) as wasted_quantity
               FROM groceries 
               WHERE expiry_date < date('now')
               GROUP BY category 
               ORDER BY expired_count DESC'''
        ).fetchall()
        
        # Total waste count
        total_waste = conn.execute(
            'SELECT COUNT(*) as count FROM groceries WHERE expiry_date < date("now")'
        ).fetchone()['count']
        
        # Items saved from waste (consumed before expiry)
        items_saved = conn.execute(
            '''SELECT COUNT(*) as count FROM groceries 
               WHERE expiry_date >= date('now') OR expiry_date IS NULL'''
        ).fetchone()['count']
        
        # Average shelf life
        avg_shelf_life = conn.execute(
            '''SELECT AVG(JULIANDAY(expiry_date) - JULIANDAY(purchase_date)) as avg_days
               FROM groceries 
               WHERE expiry_date IS NOT NULL AND purchase_date IS NOT NULL'''
        ).fetchone()['avg_days']
        
        conn.close()
        
        # Calculate waste reduction percentage
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
def settings():
    """
    User settings page for notification preferences and app configuration.
    """
    if request.method == 'POST':
        # Save notification preferences to session or database
        session['notifications_enabled'] = request.form.get('notifications_enabled') == 'on'
        session['notification_time'] = request.form.get('notification_time', '09:00')
        session['expiry_warning_days'] = int(request.form.get('expiry_warning_days', 7))
        
        flash('Settings saved successfully!', 'success')
        return redirect(url_for('settings'))
    
    # Load current settings
    notifications_enabled = session.get('notifications_enabled', True)
    notification_time = session.get('notification_time', '09:00')
    expiry_warning_days = session.get('expiry_warning_days', 7)
    
    return render_template('settings.html',
                         notifications_enabled=notifications_enabled,
                         notification_time=notification_time,
                         expiry_warning_days=expiry_warning_days)


@app.route('/barcode')
def barcode():
    """
    Barcode scanner page for quick product addition.
    """
    return render_template('barcode.html', categories=CATEGORIES)


@app.route('/api/export')
def export_data():
    """
    Export inventory data as CSV file.
    """
    import csv
    from io import StringIO
    from flask import make_response
    
    try:
        conn = get_db_connection()
        groceries = conn.execute('SELECT * FROM groceries ORDER BY purchase_date DESC').fetchall()
        conn.close()
        
        # Create CSV
        si = StringIO()
        writer = csv.writer(si)
        writer.writerow(['ID', 'Name', 'Quantity', 'Category', 'Purchase Date', 'Expiry Date', 'Notes'])
        
        for item in groceries:
            writer.writerow([
                item['id'],
                item['name'],
                item['quantity'],
                item['category'],
                item['purchase_date'],
                item['expiry_date'] or '',
                item['notes'] or ''
            ])
        
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=grocery_inventory.csv"
        output.headers["Content-type"] = "text/csv"
        return output
        
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        return {'error': str(e)}, 500


@app.route('/api/clear-expired', methods=['POST'])
def clear_expired():
    """
    Remove all expired items from inventory.
    """
    try:
        conn = get_db_connection()
        result = conn.execute('DELETE FROM groceries WHERE expiry_date < date("now")')
        count = result.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"Cleared {count} expired items")
        return {'success': True, 'count': count}
        
    except Exception as e:
        logger.error(f"Error clearing expired items: {e}")
        return {'error': str(e)}, 500


@app.route('/api/reset', methods=['POST'])
def reset_data():
    """
    Reset all data - DELETE EVERYTHING.
    """
    try:
        conn = get_db_connection()
        conn.execute('DELETE FROM groceries')
        conn.commit()
        conn.close()
        
        logger.warning("All data has been reset!")
        return {'success': True}
        
    except Exception as e:
        logger.error(f"Error resetting data: {e}")
        return {'error': str(e)}, 500


@app.route('/api/share/<int:item_id>')
def share_item(item_id):
    """
    Generate shareable link for an inventory item.
    """
    try:
        conn = get_db_connection()
        item = conn.execute('SELECT * FROM groceries WHERE id = ?', (item_id,)).fetchone()
        conn.close()
        
        if not item:
            return {'error': 'Item not found'}, 404
        
        # In production, you'd generate a secure share token
        # For now, return item details
        return {
            'id': item['id'],
            'name': item['name'],
            'quantity': item['quantity'],
            'category': item['category'],
            'expiry_date': item['expiry_date'],
            'share_url': f"{request.host_url}items/{item_id}"
        }
        
    except Exception as e:
        logger.error(f"Error sharing item: {e}")
        return {'error': str(e)}, 500


@app.route('/api/barcode/<barcode_number>')
def barcode_lookup(barcode_number):
    """
    API endpoint for barcode lookup.
    In production, this would integrate with a product database API.
    """
    # This is a placeholder - in production you'd integrate with:
    # - Open Food Facts API
    # - UPC Database
    # - Barcode Lookup API
    
    return {
        'barcode': barcode_number,
        'name': f'Product {barcode_number}',
        'category': 'Other',
        'message': 'Barcode lookup feature - integrate with product database API'
    }


if __name__ == '__main__':
    # Initialize database if it doesn't exist
    try:
        init_db()
        logger.info("Application starting...")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        
    # Run the application
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )
