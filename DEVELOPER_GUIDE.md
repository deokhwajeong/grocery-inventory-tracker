# Developer Guide

## Table of Contents
- [Development Setup](#development-setup)
- [Code Structure](#code-structure)
- [Adding New Features](#adding-new-features)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

## Development Setup

### Prerequisites
- Python 3.8+
- Tesseract OCR
- Git
- Code editor (VS Code recommended)

### Getting Started
1. Clone and setup:
   ```bash
   git clone https://github.com/deokhwajeong/grocery-inventory-tracker.git
   cd grocery-inventory-tracker
   pip install -r requirements.txt
   ```

2. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. Initialize database:
   ```bash
   sqlite3 groceries.db < schema.sql
   ```

4. Run in development mode:
   ```bash
   export FLASK_ENV=development
   python app.py
   ```

## Code Structure

### Application Flow
```
User Request → Flask Route → Validation → Database/OCR → Template → Response
```

### Key Components

#### `app.py` - Main Application
- **Route Handlers**: Handle HTTP requests and responses
- **Validation Functions**: `validate_grocery_item()` validates user input
- **Database Helpers**: `get_db_connection()`, `init_db()`
- **Error Handling**: Try-catch blocks with logging

#### `ocr_processor.py` - OCR Module
- **Image Preprocessing**: `preprocess_image()` enhances image quality
- **Text Extraction**: `extract_text_from_image()` uses Tesseract
- **Parsing Logic**: `parse_receipt_text()` extracts structured data
- **Main Interface**: `process_receipt_image()` orchestrates the workflow

#### `config.py` - Configuration
- **Config Classes**: Base, Development, Production configs
- **Environment Variables**: All customizable settings
- **Defaults**: Sensible defaults for all options

### Database Schema
```sql
CREATE TABLE groceries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    purchase_date TEXT NOT NULL,
    expiry_date TEXT,
    category TEXT DEFAULT 'Other',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_category ON groceries(category);
CREATE INDEX idx_expiry_date ON groceries(expiry_date);
```

## Adding New Features

### Adding a New Route
1. Define the route in `app.py`:
   ```python
   @app.route('/new-feature', methods=['GET', 'POST'])
   def new_feature():
       """Brief description of what this route does"""
       try:
           # Your logic here
           logger.info("Feature accessed")
           return render_template('new_feature.html')
       except Exception as e:
           logger.error(f"Error in new feature: {e}")
           flash('An error occurred', 'error')
           return redirect(url_for('index'))
   ```

2. Create a template in `templates/new_feature.html`:
   ```html
   {% extends "layout.html" %}
   {% block content %}
   <!-- Your content -->
   {% endblock %}
   ```

3. Add navigation link in `templates/layout.html`

### Adding a New Category
Edit `config.py`:
```python
CATEGORIES = [
    'Dairy', 'Meat', 'Produce', 'Bakery',
    'Frozen', 'Pantry', 'Beverages', 'Snacks',
    'Your New Category', 'Other'
]
```

### Adding Database Fields
1. Modify `schema.sql`:
   ```sql
   ALTER TABLE groceries ADD COLUMN new_field TEXT;
   ```

2. Update forms in templates (add.html, edit.html)

3. Update route handlers in app.py

4. Consider adding migration script for existing databases

## Testing

### Manual Testing Checklist
- [ ] Add item with all fields
- [ ] Add item with only required fields
- [ ] Edit existing item
- [ ] Delete item
- [ ] Search functionality
- [ ] Filter by category
- [ ] Sort by different fields
- [ ] Upload receipt
- [ ] Review OCR results
- [ ] Select/deselect items in OCR review
- [ ] Test with expired items
- [ ] Test with expiring soon items
- [ ] Mobile camera functionality
- [ ] Error handling (invalid inputs)

### Testing OCR
Test with different receipt types:
- English receipts
- Korean receipts
- Mixed language receipts
- Poor quality images
- Different lighting conditions

### Performance Testing
```bash
# Check database query performance
sqlite3 groceries.db
.timer on
SELECT * FROM groceries WHERE category = 'Dairy';
SELECT * FROM groceries WHERE expiry_date <= date('now', '+7 days');
```

## Deployment

### Production Checklist
- [ ] Set secure `SECRET_KEY` environment variable
- [ ] Set `FLASK_ENV=production`
- [ ] Disable debug mode (`FLASK_DEBUG=False`)
- [ ] Configure proper logging
- [ ] Set up database backups
- [ ] Configure firewall rules
- [ ] Use HTTPS
- [ ] Set up monitoring

### Environment Variables for Production
```bash
export FLASK_ENV=production
export FLASK_DEBUG=False
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
export DATABASE_PATH=/var/app/data/groceries.db
export LOG_LEVEL=WARNING
export LOG_FILE=/var/log/grocery-tracker/app.log
```

### Using a Production Server
Instead of the Flask development server, use gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

Or with nginx as reverse proxy (recommended).

### Docker Deployment (Future)
```dockerfile
FROM python:3.9-slim
# Install tesseract
RUN apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-kor
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

## Troubleshooting

### Common Issues

#### "Tesseract not found"
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-kor

# macOS
brew install tesseract tesseract-lang
```

#### Database locked error
- Close all connections to the database
- Check if another process is using it
- Ensure proper connection closing in code

#### OCR returns no items
- Check image quality (try preprocessing)
- Verify Tesseract languages installed
- Check logs for errors
- Try with different receipt

#### Import errors
```bash
pip install -r requirements.txt --upgrade
```

#### Port already in use
```bash
# Find process using port 5000
lsof -i :5000
# Kill the process
kill -9 <PID>
```

### Debugging

#### Enable detailed logging
```python
# In config.py or .env
LOG_LEVEL=DEBUG
```

#### Check logs
```bash
tail -f app.log
```

#### Database inspection
```bash
sqlite3 groceries.db
.tables
.schema groceries
SELECT * FROM groceries LIMIT 5;
```

## Best Practices

### Code Style
- Follow PEP 8 for Python code
- Use meaningful variable names
- Add docstrings to all functions
- Keep functions focused (single responsibility)
- Use logging instead of print statements

### Security
- Never commit `.env` file
- Validate all user inputs
- Use parameterized SQL queries
- Sanitize file uploads
- Keep dependencies updated

### Performance
- Use database indexes for frequently queried fields
- Limit query results when appropriate
- Clean up temporary files
- Use connection pooling for concurrent users
- Cache expensive computations

### Git Workflow
```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes and commit
git add .
git commit -m "Add: new feature description"

# Push and create pull request
git push origin feature/new-feature
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Tesseract OCR Documentation](https://tesseract-ocr.github.io/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [OpenCV Python Tutorials](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html)
