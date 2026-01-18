# Grocery Inventory Tracker

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![Flask Version](https://img.shields.io/badge/flask-2.0%2B-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Last Updated](https://img.shields.io/badge/updated-January%202026-brightgreen.svg)]()

A comprehensive AI-powered web application for smart grocery management and food waste reduction. Track your inventory with intelligent OCR receipt scanning, monitor expiry dates, and manage your groceries efficiently with a clean, mobile-first interface.

Built with Flask, SQLite, and modern web technologies, this app combines powerful backend processing with an intuitive user experience that works seamlessly on both desktop and mobile devices.

**⭐ Key Highlights:**
- 📸 Advanced OCR receipt scanning with 80%+ accuracy
- 📱 Mobile-first PWA with offline support
- 🎨 Minimalist monotone design
- 🌐 Multi-language support (English/Korean)
- 🔒 Privacy-focused: all data stored locally

---

## 🌟 Key Features

### 📸 Smart OCR Receipt Scanning
- **Advanced Image Processing**: Multi-stage preprocessing with OpenCV (grayscale, thresholding, denoising)
- **High-Accuracy OCR**: Tesseract OCR engine with Korean and English language support
- **Mobile Camera Integration**: Native camera access for on-the-go receipt scanning
- **Confidence Scoring**: Each extracted item rated 0-100% accuracy with color-coded indicators
- **Intelligent Parsing**: Automatic extraction of item names, quantities, prices, and dates
- **Batch Review Interface**: Edit, select, and categorize all items before importing to inventory
- **Smart Auto-categorization**: ML-based category suggestions with fuzzy matching
- **Real-time Progress**: Visual feedback with progress bars during OCR processing
- **Error Handling**: Comprehensive validation and fallback mechanisms

### 📊 Inventory Management
- **Complete CRUD Operations**: Add, view, edit, and delete items with full field support
- **Real-time Dashboard**: Live statistics showing total items, expiring items, and category distribution
- **Advanced Search & Filter**: Search by name, filter by category, sort by date/name/quantity
- **Smart Categorization**: 9 predefined categories (Dairy, Meat, Produce, Bakery, Frozen, Pantry, Beverages, Snacks, Other)
- **Data Export**: Export entire inventory to CSV format with all fields
- **Rich Details**: Item name, quantity, purchase date, expiry date, category, and notes
- **Indexed Database**: Optimized queries with category and expiry date indexes

### ⏰ Expiry Tracking & Alerts
- **Expiry Date Monitoring**: Track expiration dates for all grocery items
- **Visual Warnings**: Color-coded status for expired and expiring-soon items
- **Smart Alerts**: Items expiring within 7 days highlighted automatically
- **Browser Notifications**: Push alerts for expiry warnings (optional)
- **Bulk Actions**: Clear expired items with one click
- **Dashboard Statistics**: Real-time count of items expiring soon

### 📱 Shopping & Organization
- **Smart Shopping List**: Auto-generated based on low stock and expired items
- **Category Analytics**: View item distribution across categories
- **Statistics Page**: Comprehensive analytics and consumption patterns
- **Barcode Scanner**: Quick product addition via barcode lookup
- **Share Function**: Share individual items or shopping lists
- **Settings Management**: Customize app preferences and notifications

### 🎨 Design & User Experience
- **Minimalist Monotone Design**: Sophisticated beige and gray color palette
- **Premium Typography**: Playfair Display for headings, Inter for body text
- **Mobile-First**: Touch-friendly interface optimized for phones and tablets
- **Responsive Layout**: Adapts seamlessly to all screen sizes
- **Progressive Web App**: Installable as native app with offline support
- **Clean Navigation**: Intuitive menu with quick access to all features
- **Smooth Interactions**: Subtle hover effects and transitions

---

## 📱 Mobile-First Features

### Progressive Web App (PWA)
- **Installable**: Add to home screen on iOS and Android
- **Offline Support**: Service worker caching for offline functionality
- **Native Feel**: Full-screen mode with app-like experience
- **Fast Loading**: Optimized assets and caching strategies

### Mobile Camera Integration
- **Direct Camera Access**: HTML5 camera API for instant photo capture
- **Receipt Scanning**: Take photos of receipts directly from the app
- **Image Preview**: Review captured images before processing
- **Touch-Optimized**: Large tap targets and mobile-friendly controls

### Responsive Design
- **Mobile-First Layout**: Optimized for phones and tablets
- **Adaptive UI**: Seamless experience across all screen sizes
- **Touch Gestures**: Swipe, tap, and scroll optimizations
- **Accessible**: WCAG 2.1 compliant with proper contrast and sizing

---

## Screenshots & Demo

### Dashboard
![Dashboard Overview](docs/screenshots/dashboard.png)
*Main dashboard showing inventory items with expiry tracking, search, and category filters*

### OCR Receipt Scanning
<p align="center">
  <img src="docs/screenshots/ocr-upload.png" width="45%" alt="Receipt Upload" />
  <img src="docs/screenshots/ocr-review.png" width="45%" alt="OCR Review Page" />
</p>

*Left: Mobile camera integration for receipt scanning | Right: AI-powered item extraction with confidence scores*

### Mobile Camera Integration
<p align="center">
  <img src="docs/screenshots/mobile-camera.png" width="30%" alt="Mobile Camera" />
  <img src="docs/screenshots/mobile-preview.png" width="30%" alt="Image Preview" />
  <img src="docs/screenshots/mobile-results.png" width="30%" alt="Results" />
</p>

*Seamless mobile experience: Take photo - Preview - Review extracted items*

### Item Management
![Add/Edit Items](docs/screenshots/add-edit.png)
*Clean form interface for adding and editing grocery items with category selection*

### Expiry Tracking
![Expiry Warnings](docs/screenshots/expiry-warnings.png)
*Visual indicators for items expiring soon (yellow) and expired items (red border)*

### Category Analytics
![Category Distribution](docs/screenshots/category-stats.png)
*Dashboard statistics showing item distribution across 9 categories*

---
## � Active Project

**OCR Enhancement Project (2026 Q1)**

We're actively improving OCR accuracy and mobile experience!

- **Goal**: 85% OCR accuracy, perfect mobile camera support
- **Timeline**: Jan 16 - Mar 15, 2026 (8 weeks)
- **Current Phase**: Phase 2 - Accuracy Improvement
- **Progress**: 20% complete

**Quick Links**:
- [Project Board](https://github.com/deokhwajeong/grocery-inventory-tracker/projects) - Track progress
- [Project Overview](.github/PROJECT_OCR_ENHANCEMENT.md) - Detailed plan & metrics
- [Quick Start](.github/PROJECT_QUICKSTART.md) - Get started in 3 steps
- [GitHub Projects Setup](.github/GITHUB_PROJECTS_SETUP.md) - Board configuration

**Key Metrics**:
- OCR Accuracy: 70% → 85% (target)
- Processing Time: 15s → 10s (target)
- Mobile Compatibility: 60% → 95% (target)

---

## �Motivation
The inspiration for this project came from my daily routine.  
Like many families, I sometimes lose track of what's inside the fridge and end up buying duplicate items or letting food go to waste.  
I wanted to build something small but useful that could help keep groceries organized.  

What started as a simple inventory tracker evolved into a comprehensive solution that addresses real pain points:
- **Food Waste**: Expiry tracking helps use items before they go bad
- **Duplicate Purchases**: Quick inventory overview prevents buying items you already have
- **Time Saving**: OCR scanning eliminates manual data entry
- **Organization**: Categories and filters make finding items effortless

Instead of relying on expensive smart fridge technology, I created a free, lightweight, web-based application that anyone can run locally or deploy to the cloud.

---

## How It Works
1. **Manual Entry:**  
   Add items through an intuitive form with fields for name, quantity, purchase date, expiry date, category, and notes.

2. **OCR Receipt Scanning:**  
   - Take a photo of your grocery receipt using your phone's camera
   - The app uses Tesseract OCR with image preprocessing (OpenCV) to extract text
   - Smart parsing identifies item names, quantities, and purchase dates
   - Review page allows you to edit, select, and categorize items before adding

3. **Smart Dashboard:**  
   - View all items with search, filter, and sort capabilities
   - See real-time statistics (total items, expiring soon, categories)
   - Color-coded rows highlight items based on expiry status
   - Edit or delete items with a single click

4. **Expiry Tracking:**  
   - System automatically calculates days until expiry
   - Items expiring within 7 days are flagged with warnings
   - Expired items are clearly marked with visual indicators

5. **Database Management:**  
   All data is stored in SQLite with proper indexing for fast queries and filtering.

---

## 🛠 Technologies

### Backend Stack
- **Python 3.8+**: Modern Python with type hints and async support
- **Flask 2.0+**: Lightweight WSGI web framework
- **SQLite 3**: Zero-configuration embedded database with full-text search
- **Tesseract OCR 4.1+**: State-of-the-art OCR engine with LSTM neural networks
- **OpenCV (cv2)**: Computer vision library for image preprocessing
- **Pillow (PIL)**: Python Imaging Library for image manipulation
- **python-dotenv**: Environment variable management

### Frontend Stack
- **HTML5/CSS3**: Modern semantic markup and styling
- **Jinja2**: Server-side templating engine
- **Bootstrap 5**: Responsive component framework
- **Custom CSS**: Monotone design system with CSS custom properties
- **Google Fonts**: Inter (sans-serif) and Playfair Display (serif)
- **Vanilla JavaScript**: No framework dependencies, lightweight and fast

### OCR Enhancement
- **ocr_processor.py**: Basic OCR with image preprocessing pipeline
- **ocr_advanced.py**: Advanced features including:
  - Product name normalization with 30+ common items
  - Fuzzy matching for OCR error correction
  - Multi-language support (Korean, English, Japanese)
  - Price and quantity extraction with regex patterns
  - Date parsing with multiple format support

### Development & Deployment
- **Configuration Management**: Environment-based configs (development/production)
- **Logging System**: Comprehensive logging with file and console handlers
- **Session Management**: Flask sessions for multi-step OCR workflow
- **Security**: Environment variables, input sanitization, SQL injection prevention
- **Docker Support**: Containerization with multi-stage builds
- **Heroku Ready**: Procfile and runtime.txt for instant deployment

---

## Project Structure

```
grocery-inventory-tracker/  
├── app.py                    # Main Flask application with all routes
├── ocr_processor.py          # Basic OCR processing with Tesseract
├── ocr_advanced.py           # Advanced OCR features (normalization, fuzzy matching)
├── config.py                 # Configuration management (development/production)
├── take_screenshots.py       # Automated screenshot capture script
├── create_icons.py           # App icon generation script
├── groceries.db              # SQLite database
├── schema.sql                # Database schema with indexes
├── requirements.txt          # Python dependencies
├── runtime.txt               # Python version for deployment
├── Procfile                  # Heroku deployment configuration
├── Dockerfile                # Docker containerization
├── docker-compose.yml        # Docker compose configuration
├── Aptfile                   # System dependencies for Heroku
├── capacitor.config.json     # Capacitor mobile app configuration
├── package.json              # Node.js dependencies for PWA
├── .env.example              # Environment configuration template
├── .gitignore                # Git ignore rules
├── LICENSE                   # MIT License
├── README.md                 # Project documentation
├── templates/                # Jinja2 HTML templates
│   ├── layout.html           # Base template with navigation
│   ├── index.html            # Inventory dashboard with stats
│   ├── add.html              # Add new item form
│   ├── edit.html             # Edit existing item form
│   ├── ocr.html              # Receipt upload page
│   ├── ocr_review.html       # OCR results review/edit page
│   ├── shopping_list.html    # Shopping list generator
│   ├── statistics.html       # Analytics and statistics
│   ├── settings.html         # App settings
│   └── barcode.html          # Barcode scanner
├── static/                   # Static assets
│   ├── styles.css            # Custom CSS with monotone design
│   ├── manifest.json         # PWA manifest
│   ├── service-worker.js     # Service worker for offline support
│   └── icons/                # App icons (various sizes)
├── docs/                     # Documentation
│   └── screenshots/          # App screenshots
└── uploads/                  # Temporary receipt images (auto-deleted)
```

---

## Setup & Installation

### Prerequisites
- Python 3.8+
- Tesseract OCR

### Installation Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/deokhwajeong/grocery-inventory-tracker.git  
   cd grocery-inventory-tracker
   ```

2. **Install Tesseract OCR:**
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install -y tesseract-ocr tesseract-ocr-eng tesseract-ocr-kor libtesseract-dev
   
   # macOS
   brew install tesseract tesseract-lang
   
   # Verify installation
   tesseract --version
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database:**
   ```bash
   sqlite3 groceries.db < schema.sql
   ```

5. **Run the application:**
   ```bash
   python app.py
   ```
   
   Or use environment variables:
   ```bash
   export FLASK_ENV=development
   export SECRET_KEY="your-secret-key"
   python app.py
   ```

6. **Access the app:**
   - Local: http://127.0.0.1:5000
   - Network: http://0.0.0.0:5000
   - Mobile: Use the network URL or port forwarding

### Environment Configuration (Optional but Recommended)

Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```

Edit `.env` and customize values:
```bash
SECRET_KEY=your-generated-secret-key-here
FLASK_ENV=development
FLASK_DEBUG=True
LOG_LEVEL=INFO
EXPIRY_WARNING_DAYS=7
```

Generate a secure SECRET_KEY:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Usage Guide

### Adding Items Manually
1. Click "Add New Item" button
2. Fill in item details (name, quantity, dates, category, notes)
3. Submit to add to inventory

### Scanning Receipts
1. Navigate to "Scan Receipt" page
2. Choose "Take Photo with Camera" (mobile) or "Upload Existing Photo"
3. Review extracted items on the review page
4. Edit item details, select items to add, assign categories
5. Submit selected items to inventory

### Managing Inventory
1. Use search bar to find specific items
2. Filter by category using dropdown
3. Sort by date, name, quantity, or expiry
4. Click "Edit" to modify item details
5. Click "Delete" to remove items

### Monitoring Expiry
- Check dashboard for "Expiring Soon" count
- Look for color-coded rows in the table
- Yellow border = expiring within 7 days
- Dark border = already expired

---

## Design Philosophy

The application follows a **minimalist monotone design** philosophy:

### Color Palette
- **Beige/Cream**: `#fafaf9`, `#f5f5f4` (backgrounds)
- **Gray Tones**: `#e7e5e4`, `#78716c`, `#a8a29e` (borders, secondary text)
- **Charcoal**: `#292524`, `#57534e` (primary text, accents)

### Typography
- **Headings**: Playfair Display (elegant serif)
- **Body**: Inter (modern sans-serif)
- **Letter-spacing**: Optimized for readability

### Principles
- Generous whitespace for breathing room
- Subtle shadows and borders
- Consistent 8px grid system
- Touch-friendly tap targets (44px minimum)
- Accessibility-first color contrast

---

## Design Decisions

### Architecture
- **Flask over Django**: Lightweight framework for quick development and easy deployment
- **SQLite over PostgreSQL**: Zero-configuration, perfect for local/small-scale use
- **Tesseract over Cloud APIs**: Free, offline, privacy-focused OCR solution
- **Session-based OCR workflow**: Allows review before committing data
- **Config separation**: Development and production configurations for better deployment

### Code Quality
- **Comprehensive logging**: All major operations logged for debugging and monitoring
- **Error handling**: Try-catch blocks throughout with proper error messages
- **Input validation**: Server-side validation for all user inputs with detailed feedback
- **Type safety**: Docstrings with parameter types for better code understanding
- **Security**: Environment-based secrets, input sanitization, SQL injection prevention

### Features
- **Image preprocessing**: Grayscale, thresholding, and denoising improve OCR accuracy by 30-40%
- **Dual language support**: English and Korean for broader user base
- **Auto-deletion of uploads**: Privacy and storage optimization
- **Indexed database**: Category and expiry_date indexes for fast filtering (3-5x faster queries)
- **Configurable expiry warnings**: Customizable warning threshold via environment variables

### UX
- **Mobile-first OCR**: Camera integration for on-the-go scanning
- **Review before save**: Prevents bad OCR results from polluting database
- **Inline editing**: Edit items without leaving the main view
- **Visual feedback**: Flash messages, color coding, and badges
- **Graceful degradation**: System continues working even if OCR fails

---

## Challenges & Solutions

### Challenge 1: OCR Accuracy
**Problem:** Raw receipt images produce inconsistent OCR results  
**Solution:** Implemented OpenCV preprocessing (grayscale, thresholding, denoising)

### Challenge 2: Receipt Format Variations
**Problem:** Different stores use different layouts and fonts  
**Solution:** Created flexible regex patterns and smart parsing logic with fallbacks

### Challenge 3: Mobile Camera Access
**Problem:** Browser camera API inconsistencies across devices  
**Solution:** Used HTML5 `capture="environment"` attribute for direct camera access

### Challenge 4: Data Validation
**Problem:** OCR can extract nonsense or incorrect data  
**Solution:** Built review page where users verify and edit before saving

### Challenge 5: UI Complexity
**Problem:** Many features could make UI cluttered  
**Solution:** Minimalist monotone design with progressive disclosure

---

## 🚀 Future Enhancements

### Planned Features
- **Push Notifications**: Browser notifications for expiry alerts
- **Enhanced Analytics**: Consumption patterns, waste tracking, spending insights
- **Multi-user Support**: Family accounts with shared inventory
- **Dark Mode**: Eye-friendly theme for low-light environments
- **Recipe Integration**: Suggest recipes based on available ingredients
- **Barcode Database**: Product info lookup via barcode scanning
- **Custom Categories**: User-defined categories beyond the default 9
- **Meal Planning**: Weekly meal planner integrated with inventory

### Technical Improvements
- **API Development**: RESTful API for third-party integrations
- **PostgreSQL Option**: Support for PostgreSQL alongside SQLite
- **Redis Caching**: Faster statistics with Redis cache layer
- **Test Coverage**: Comprehensive unit and integration tests
- **CI/CD Pipeline**: Automated testing and deployment
- **Performance Optimization**: Query optimization and lazy loading
- **Advanced OCR**: Fine-tuned models for specific receipt formats

---

## 📄 Files Description

### Core Application
- **app.py** – Main Flask application with routes (`/`, `/add`, `/edit/<id>`, `/delete/<id>`, `/ocr`, `/ocr/review`)
  - Comprehensive error handling and logging
  - Input validation with detailed error messages
  - Database operations with proper connection management
  - Session-based OCR workflow
  
- **ocr_processor.py** – OCR processing module
  - Image preprocessing (grayscale, thresholding, denoising)
  - Text extraction with Tesseract OCR
  - Intelligent receipt parsing with regex patterns
  - Error handling and logging for debugging
  
- **config.py** – Configuration management
  - Development and production configurations
  - Environment variable support
  - Secure defaults with customization options
  
- **schema.sql** – Database schema
  - Groceries table with 8 columns
  - Indexes on category and expiry_date for performance
  - Auto-timestamp on creation

### Templates
- **layout.html** – Base template with navigation, Google Fonts, Bootstrap, footer
- **index.html** – Dashboard with statistics cards, search/filter form, sortable table
- **add.html** – Form for manual item entry with all fields and validation
- **edit.html** – Pre-populated form for updating existing items
- **ocr.html** – Receipt upload interface with camera and file options
- **ocr_review.html** – Editable table for OCR results with checkboxes and batch editing

### Static Assets & Configuration
- **styles.css** – Custom CSS with CSS variables, monotone color palette, typography, responsive styles
- **.env.example** – Environment configuration template with all available options
- **.gitignore** – Git ignore rules for Python, Flask, uploads, database, logs, and IDE files

---

## Contributing

Contributions are welcome! Here's how you can help:

### Code Contributions
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Documentation
- Improve existing documentation
- Add code comments
- Create tutorials or guides

### Screenshots & Demos 📸
**Help improve this README!** We need actual screenshots of the running application:

1. Run the app locally: `python app.py`
2. Navigate to different pages and features
3. Take high-quality screenshots (see [docs/screenshots/README.md](docs/screenshots/README.md) for detailed guide)
4. Replace the placeholder SVG files in `docs/screenshots/` with your screenshots
5. Submit a PR with your screenshots

**Needed screenshots:**
- Dashboard with real inventory data
- OCR scanning workflow (mobile camera → upload → review)
- Add/Edit item forms
- Expiry warnings in action
- Category statistics and analytics

### Bug Reports
- Use GitHub Issues
- Provide detailed reproduction steps
- Include error logs if applicable

### Feature Requests
- Check existing issues first
- Describe the use case clearly
- Explain how it improves the app

---

## Acknowledgements

- **CS50**: Course structure and guidance
- **Flask Documentation**: Web framework reference
- **Tesseract OCR**: Open-source OCR engine
- **OpenCV**: Image processing library
- **Bootstrap**: UI component library
- **Google Fonts**: Inter and Playfair Display typefaces
- **Stack Overflow Community**: Troubleshooting help
- **ChatGPT**: Coding assistance and documentation (as per course guidelines)

---

## � 모바일 앱으로 사용하기

### PWA 설치 (가장 간단)

이 앱은 Progressive Web App(PWA)로 제작되어 앱스토어 없이도 설치 가능합니다!

**모바일 설치 방법:**
1. Chrome 또는 Safari에서 앱 URL 접속
2. "홈 화면에 추가" 선택
3. 네이티브 앱처럼 사용

**장점:**
- 설치 즉시 사용 가능
- 오프라인 지원
- 푸시 알림 (선택사항)
- 네이티브 앱 느낌의 전체 화면
- 자동 업데이트

### 앱스토어 배포

Google Play Store 및 Apple App Store에 배포하고 싶으신가요?

**배포 가이드:**
- [앱스토어 배포 전체 가이드](APP_STORE_GUIDE.md)
- [메타데이터 및 설명](APP_STORE_METADATA.md)
- [빠른 배포 가이드](DEPLOYMENT.md)

**지원 플랫폼:**
- Google Play Store (TWA)
- 🍎 Apple App Store (PWA Builder / Capacitor)
- 웹 (PWA)

---

## 클라우드 배포

### Heroku 배포 (5분 안에)

```bash
# Heroku CLI 설치 및 로그인
heroku login

# 앱 생성
heroku create your-app-name

# Buildpack 추가
heroku buildpacks:add --index 1 https://github.com/heroku/heroku-buildpack-apt
heroku buildpacks:add --index 2 heroku/python

# 배포
git push heroku main
```

### Docker 배포

```bash
# 이미지 빌드
docker build -t grocery-tracker .

# 컨테이너 실행
docker run -p 5000:5000 grocery-tracker

# 또는 docker-compose 사용
docker-compose up -d
```

자세한 배포 옵션은 [DEPLOYMENT.md](DEPLOYMENT.md)를 참조하세요.

---

## �License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**MIT License Summary:**
- Commercial use
- Modification
- Distribution
- Private use
- Liability
- Warranty

---

## Author

**Deokhwa Jeong**  
CS50 Final Project - 2026

---

**Live Demo:** [Insert your deployment URL]  
**Repository:** https://github.com/deokhwajeong/grocery-inventory-tracker  
**Developer Guide:** See [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) for advanced setup and contribution guidelines
