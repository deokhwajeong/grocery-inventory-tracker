# Changelog

## Version 2.1.0 - OCR Enhancement Release (January 16, 2026)

### 🚀 Major OCR Enhancements

#### Advanced Image Processing
- **Multi-Stage Preprocessing**: Enhanced image quality for better OCR
  - Automatic rotation correction (deskewing)
  - Contrast enhancement using CLAHE
  - Image sharpening for blurry receipts
  - Advanced noise reduction
  - Multiple preprocessing variants tested simultaneously

#### AI-Powered Text Recognition
- **Intelligent Product Name Normalization** (`ocr_advanced.py`)
  - Automatic OCR error correction (O→0, l→1, etc.)
  - Fuzzy matching for similar product names
  - Common product database with 50+ items
  - Noise word removal (개, 봉, 팩, etc.)
  - Korean/English mixed text support

#### Smart Item Processing
- **Confidence Scoring**: Each item gets 0-100% confidence score
  - Based on name quality, quantity, date validity
  - Visual badges in review screen (green/blue/yellow/red)
  - Low confidence items flagged for review

- **Duplicate Detection**: Intelligent item merging
  - Fuzzy matching algorithm (SequenceMatcher + fuzzywuzzy)
  - Combines quantities of similar items
  - Keeps highest confidence score

- **Auto-Categorization**: AI-based category suggestion
  - Keyword-based classification
  - 9 categories with extensive keyword database
  - Korean and English product recognition

#### Mobile Camera Integration
- **Enhanced Mobile Support**
  - iOS Safari native camera integration
  - Android Chrome camera support
  - `capture="environment"` for rear camera selection
  - Image compression (max 1920px, 85% quality)
  - File type validation (JPEG, PNG, GIF, BMP)
  - Size validation (max 16MB)

#### Receipt Analysis
- **Receipt Type Detection**: Identifies major Korean retailers
  - E-mart, Homeplus, Lotte Mart
  - GS25, CU, 7-Eleven
  - Coupang, Market Kurly
  - Store information extraction

- **Quality Analysis**: Real-time feedback
  - OCR quality score (0-100)
  - Average item confidence
  - Warnings and suggestions
  - Processing metrics

#### UI/UX Improvements
- **Real-time Progress Feedback**
  - Visual progress bar during OCR processing
  - Step-by-step status messages
  - Estimated completion indication

- **Enhanced Review Screen**
  - Confidence badges for each item
  - Auto-populated categories
  - Color-coded quality indicators
  - Improved table layout

### 📦 Dependencies Added
- **python-Levenshtein**: Fast string similarity matching
- **fuzzywuzzy**: Fuzzy string matching for product names

### 📚 Documentation
- **OCR_GUIDE.md**: Comprehensive OCR usage guide
  - Mobile camera tips (iOS/Android)
  - Best practices for photo capture
  - Confidence score interpretation
  - Troubleshooting guide
  - Technical specifications

### 🔧 Technical Improvements
- **Modular Architecture**: Separated advanced OCR features
- **Type Hints**: Added typing annotations throughout
- **Error Handling**: Graceful fallback when advanced features unavailable
- **Logging**: Enhanced debug information for OCR process

---

## Version 2.0.0 - Advanced Feature Release (January 2026)

### 🆕 New Features

#### License
- **MIT License Added**: Project now has official open-source license
  - Allows commercial use, modification, and distribution
  - See LICENSE file for full details

#### Configuration Management
- **config.py**: Centralized configuration system
  - Development and production configurations
  - Environment variable support with `.env` files
  - Secure defaults for all settings
  - Easy customization through `.env.example`

#### Code Quality Improvements
- **Comprehensive Logging**: All operations now logged
  - Info level: User actions and major operations
  - Warning level: Validation failures and potential issues
  - Error level: Exceptions and critical errors
  - Debug level: Detailed execution flow
  
- **Enhanced Error Handling**: Try-catch blocks throughout
  - Graceful error recovery
  - User-friendly error messages
  - Detailed logging for debugging
  
- **Input Validation**: Robust validation for all user inputs
  - Required field checking
  - Data type validation
  - Range validation (quantity, dates, string length)
  - Category validation
  - Cross-field validation (expiry vs purchase date)

#### Documentation
- **Developer Guide**: Comprehensive DEVELOPER_GUIDE.md added
  - Development setup instructions
  - Code structure documentation
  - Feature addition guide
  - Testing checklist
  - Deployment instructions
  - Troubleshooting guide
  
- **Environment Template**: .env.example for easy configuration
- **Enhanced README**: Updated with all improvements

### 🔧 Code Improvements

#### app.py
- Added docstrings to all functions with parameter descriptions
- Implemented `validate_grocery_item()` function for reusable validation
- Enhanced error handling in all routes
- Logging for all major operations
- Better database connection management
- Configurable settings from config.py

#### ocr_processor.py
- Comprehensive docstrings with type hints
- Enhanced image preprocessing error handling
- Improved OCR text extraction with better error messages
- More robust receipt parsing with validation
- Quantity sanity checking (prevents unreasonable values)
- Better date extraction and validation
- Detailed logging for debugging OCR issues

#### config.py (NEW)
- Environment-based configuration
- Development vs Production modes
- All settings configurable via environment variables
- Secure secret key handling
- Customizable expiry warning days
- OCR language configuration
- Logging configuration

### 📦 Dependencies
- **python-dotenv**: Added for .env file support
- All existing dependencies maintained

### 🗂️ New Files
- `LICENSE` - MIT License
- `config.py` - Configuration management
- `.env.example` - Environment configuration template
- `DEVELOPER_GUIDE.md` - Developer documentation
- `CHANGELOG.md` - This file

### 🔒 Security Enhancements
- Environment-based SECRET_KEY (no hardcoded secrets)
- Production configuration requires explicit SECRET_KEY
- Enhanced input sanitization
- Better SQL injection prevention through validation
- Secure file upload handling with size limits

### 📊 Performance
- Database queries optimized with proper indexes
- Efficient error handling without performance degradation
- Configurable logging levels (reduce I/O in production)

### 🐛 Bug Fixes
- Fixed potential database connection leaks
- Better handling of missing/invalid dates
- Improved error recovery in OCR processing
- Fixed edge cases in quantity validation

### 📝 Documentation Updates
- README.md updated with:
  - License information
  - Configuration instructions
  - Enhanced setup guide
  - Improved project structure
  - Better technology descriptions
  - Developer guide link
  
- New DEVELOPER_GUIDE.md with:
  - Development workflow
  - Testing procedures
  - Deployment guide
  - Troubleshooting section

---

## Version 1.0.0 - Initial Release

### Features
- Full CRUD operations for grocery items
- OCR receipt scanning with Tesseract
- Image preprocessing with OpenCV
- Expiry date tracking with warnings
- Category system (9 categories)
- Search and filter functionality
- Sort by multiple criteria
- OCR review page
- Statistics dashboard
- Monotone design with premium typography
- Mobile camera integration
- Responsive UI with Bootstrap 5
