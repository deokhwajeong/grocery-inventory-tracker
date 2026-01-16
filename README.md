# Grocery Inventory Tracker

Grocery Inventory Tracker is a sophisticated web application built with Flask and SQLite designed to revolutionize how you manage your fridge inventory. This application combines modern OCR technology, smart categorization, and an elegant monotone UI to help reduce food waste and keep your groceries organized.

Born from the frustration of discovering expired items and duplicate purchases, this project evolved from a simple inventory tracker into a comprehensive grocery management system with advanced features like expiry tracking, smart filtering, and mobile-first OCR scanning.

---

## Features

### Core Functionality
- Full CRUD Operations: Add, view, edit, and delete grocery items with comprehensive details
- Smart Dashboard: Real-time statistics showing total items, expiring items, and category distribution
- Advanced Search & Filter: Search by name, filter by category, and sort by multiple criteria
- Responsive Design: Beautiful monotone UI that works seamlessly on desktop and mobile

### Expiry Management
- Expiry Date Tracking: Set and monitor expiration dates for all items
- Smart Alerts: Visual warnings for items expiring within 7 days
- Color-Coded Status: Expired (dark border), expiring soon (warning), or fresh items
- Expiry Statistics: Dashboard widget showing count of soon-to-expire items

### OCR Technology
- Receipt Scanning: Upload photos or use your phone's camera to scan receipts
- AI-Powered Recognition: Advanced OCR with multi-stage image preprocessing
- Multi-language Support: English and Korean receipt recognition
- High Accuracy: Confidence scoring for each extracted item (0-100%)
- Smart Normalization: Automatic product name correction and standardization
- Duplicate Detection: Intelligent merging of similar items
- Auto-categorization: AI-based category suggestion for each item
- Quality Analysis: Real-time feedback on OCR extraction quality
- Batch Editing: Review and modify all scanned items before import
- Selective Import: Choose which scanned items to add to inventory
- Mobile-First: Native camera integration for iOS and Android
- Real-time Progress: Visual feedback during OCR processing

### Organization
- Category System: 9 predefined categories (Dairy, Meat, Produce, Bakery, Frozen, Pantry, Beverages, Snacks, Other)
- Notes Field: Add custom notes or details for any item
- Category Analytics: View item distribution across categories
- Smart Badges: Visual category indicators throughout the interface

### Design & UX
- Minimalist Monotone Design: Sophisticated beige and gray color palette
- Premium Typography: Playfair Display for headings, Inter for body text
- Clean Layout: Generous spacing, subtle shadows, and refined borders
- Smooth Interactions: Subtle hover effects and transitions
- Mobile Optimized: Touch-friendly interface with camera integration

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

## Technologies

### Backend
- **Python (Flask):** Lightweight web framework for routing and logic
- **SQLite:** Zero-configuration relational database with indexes
- **Tesseract OCR:** Open-source OCR engine for text extraction
- **OpenCV:** Image preprocessing for improved OCR accuracy
- **Pillow (PIL):** Image handling and manipulation
- **Logging:** Comprehensive application logging for debugging and monitoring

### Frontend
- **HTML/CSS (Jinja2 templates):** Dynamic templating
- **Bootstrap 5:** Responsive grid and components
- **Custom CSS:** Monotone design system with CSS variables
- **Google Fonts:** Inter and Playfair Display typography
- **Vanilla JavaScript:** Interactive features and form handling

### Features & Libraries
- **Configuration Management:** Environment-based config with development/production modes
- **Session Management:** Flask sessions for OCR workflow
- **Flash Messages:** User feedback system
- **File Uploads:** Secure receipt image handling with validation
- **Form Validation:** Comprehensive server-side input validation
- **Error Handling:** Try-catch blocks with proper logging throughout
- **Security:** Environment-based SECRET_KEY, input sanitization, CSRF protection

---

## Project Structure

```
grocery-inventory-tracker/  
├── app.py                    # Main Flask application with routes, validation, error handling
├── ocr_processor.py          # OCR processing with logging and robust error handling
├── config.py                 # Configuration management (development/production)
├── groceries.db              # SQLite database
├── schema.sql                # Database schema with indexes
├── requirements.txt          # Python dependencies
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
│   └── ocr_review.html       # OCR results review/edit page
├── static/                   # Static assets
│   └── styles.css            # Custom CSS with monotone design
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
   sudo apt-get install -y tesseract-ocr tesseract-ocr-kor
   
   # macOS
   brew install tesseract tesseract-lang
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

## Future Enhancements

### Planned Features
- **Email Notifications**: Alerts for expiring items
- **Analytics Dashboard**: Consumption patterns, waste tracking, spending insights
- **Shopping List Generation**: Auto-generate lists based on low stock
- **Multi-user Support**: Family accounts with role-based access
- **Progressive Web App**: Installable mobile app experience
- **Dark Mode**: Eye-friendly theme for night use
- **Export/Import**: CSV and JSON data portability
- **Browser Notifications**: Push alerts for expiry warnings
- **Store Integration**: Barcode scanning for product info
- **ML Improvements**: Custom receipt format training

### Technical Improvements
- **Redis Caching**: Faster dashboard statistics
- **PostgreSQL Migration**: Better concurrent access
- **Docker Deployment**: Containerized setup
- **API Endpoints**: RESTful API for mobile apps
- **Automated Testing**: Unit and integration tests
- **CI/CD Pipeline**: Automated deployment

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
