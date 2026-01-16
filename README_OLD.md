# Grocery Inventory Tracker
#### Video Demo: <URL https://www.youtube.com/watch?v=gzT7N7sNEq4>
#### Description:
Grocery Inventory Tracker is a simple web application built with Flask and SQLite that helps you keep track of the items in your fridge.  
With this app, you can easily record groceries (name, quantity, and purchase date) and view your fridge inventory in a clean dashboard.  

This project started as my business ideation, with the goal of solving a real-world problem: reducing food waste and making it easier to know what’s inside the fridge at a glance.  
While the initial version uses **manual entry**, it’s designed to be extended with **OCR (Optical Character Recognition)** in the future, so that grocery receipts can be scanned automatically to update the inventory.

---

## Features
- Add grocery items with **name, quantity, and purchase date**.
- **📸 OCR Receipt Scanning**: Upload or take a photo of your receipt and automatically extract items!
- **Mobile-friendly camera access**: Use your phone's camera directly in the browser
- Store data in a persistent **SQLite database**.
- View your fridge inventory in a clear **web-based dashboard**.
- Highlight items with their **purchase date** so you know when they were stocked.
- **English and Korean receipt support** via Tesseract OCR
- Future idea: **Expiration date tracking** with notifications.

---

## Motivation
The inspiration for this project came from my daily routine.  
Like many families, I sometimes lose track of what’s inside the fridge and end up buying duplicate items or letting food go to waste.  
I wanted to build something small but useful that could help keep groceries organized.  

Instead of relying on expensive smart fridge technology, I decided to create a lightweight, web-based application that anyone can run locally.  
The project is also a great opportunity to apply what I learned in CS50: working with Flask for the backend, SQL for data storage, and HTML/CSS for the frontend.

---

## How It Works
1. **Manual Entry:**  
   From the web interface, you can enter grocery name, quantity, and purchase date.
2. **OCR Receipt Scanning:**  
   Upload a receipt photo or use your phone's camera to capture it directly. The app uses Tesseract OCR to extract items, quantities, and dates automatically.
3. **Database Storage:**  
   Data is stored in `groceries.db` using SQLite.
4. **Dashboard:**  
   The index page displays a table of current inventory, including purchase dates.
5. **Smart Parsing:**  
   The OCR system intelligently parses receipt text to identify item names, quantities, and purchase dates in both English and Korean.

---

## Technologies
- **Python (Flask):** Backend web framework.
- **SQLite:** Lightweight relational database.
- **HTML/CSS (Jinja2 templates):** Frontend interface.
- **Bootstrap:** For simple styling and responsive design.
- **Tesseract OCR:** For receipt text extraction (English and Korean support).
- **OpenCV:** For image preprocessing to improve OCR accuracy.
- **Pillow:** For image handling and manipulation.

---

## Project Structure

project/  
├── app.py # Main Flask application  
├── ocr_processor.py # OCR and receipt parsing logic  
├── groceries.db # SQLite database  
├── schema.sql # Database schema  
├── templates/ # HTML templates  
│   ├── layout.html # Base layout  
│   ├── index.html # Inventory dashboard  
│   ├── add.html # Form for adding groceries  
│   └── ocr.html # OCR receipt upload page  
├── static/ # CSS/JS files  
│   └── styles.css  
├── uploads/ # Temporary receipt images (auto-deleted)  
├── requirements.txt # Python dependencies  
├── .gitignore # Git ignore file  
└── README.md # Project documentation  

---

## Setup & Installation
1. Clone the repository:
   git clone https://github.com/deokhwajeong/grocery-inventory-tracker.git  
   cd grocery-inventory-tracker  

2. Install system dependencies (Tesseract OCR):
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install -y tesseract-ocr tesseract-ocr-kor
   
   # macOS
   brew install tesseract tesseract-lang

3. Install Python dependencies:
   pip install -r requirements.txt  

4. Initialize the database:
   sqlite3 groceries.db < schema.sql  

5. Run the Flask app:
   flask run  

6. Open in your browser at:  
   http://127.0.0.1:5000  

7. On mobile devices, navigate to the same URL to use camera features!  

---

## Files
- **app.py** – Contains all Flask routes (/, /add, /ocr, /delete), handles database operations and file uploads.  
- **ocr_processor.py** – OCR processing logic, image preprocessing, and receipt text parsing.
- **groceries.db** – SQLite database file that persists grocery data.  
- **schema.sql** – Database schema definition.
- **templates/index.html** – Displays the current grocery inventory in a table.  
- **templates/add.html** – Simple form for adding grocery items manually.  
- **templates/ocr.html** – Receipt upload page with camera access for mobile devices.
- **templates/layout.html** – Base template for consistent styling.  
- **static/styles.css** – Custom CSS for table styling and layout.  
- **README.md** – Documentation of the project.  

---

## Design Decisions
- I chose Flask over Django to keep the project lightweight and easy to set up for local use.  
- SQLite was chosen instead of MySQL/Postgres because it requires no external server and fits the small scale of this app.  
- **Tesseract OCR** was selected over cloud APIs (Google Vision, AWS Textract) to keep the app completely offline and free.
- **Image preprocessing** with OpenCV improves OCR accuracy by applying grayscale conversion, thresholding, and denoising.
- The OCR system supports both **English and Korean** receipts to accommodate diverse users.
- Receipt images are automatically deleted after processing to save storage space and protect privacy.  

---

## Challenges
- **Receipt format variations:** Different stores use different layouts, fonts, and formats, making universal parsing difficult.
- **OCR accuracy:** Low-quality images, poor lighting, or crumpled receipts can reduce OCR accuracy. Image preprocessing helps but isn't perfect.
- **Smart parsing logic:** Distinguishing between item names, quantities, and prices required careful regex patterns and text analysis.
- **Mobile compatibility:** Ensuring camera access works across different mobile browsers required proper HTML5 attributes.
- Designing the database schema was straightforward, but I had to think about scalability (e.g., what if we also want to track expiration dates or categories in the future?).

---

## Future Work
- **Improved OCR accuracy:** Train custom models for specific store receipt formats.
- **Batch editing:** Allow users to review and edit OCR results before saving.
- **Expiration tracking:** Automatically calculate expiry dates and highlight soon-to-expire items.  
- **Notifications:** Email or push alerts when items are running low or near expiry.  
- **User accounts:** Multi-user support so each family member can log in.
- **Categories and tags:** Organize items by category (dairy, produce, meat, etc.).
- **Shopping list generation:** Automatically create shopping lists based on low inventory.  

---

## Acknowledgements
- Inspired by daily life in my kitchen 😊  
- Some coding assistance provided with the help of AI tools (ChatGPT), cited here as per course guidelines.  
