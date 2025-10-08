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
- Store data in a persistent **SQLite database**.
- View your fridge inventory in a clear **web-based dashboard**.
- Highlight items with their **purchase date** so you know when they were stocked.
- Planned extension: **OCR receipt scanning** for automatic data entry.
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
1. **User Input:**  
   From the web interface, you can enter grocery name, quantity, and purchase date.
2. **Database Storage:**  
   Data is stored in `groceries.db` using SQLite.
3. **Dashboard:**  
   The index page displays a table of current inventory, including purchase dates.
4. **Future OCR Integration:**  
   Receipts can be scanned with OCR tools (like Tesseract or Google Vision API), parsed, and automatically added to the database.

---

## Technologies
- **Python (Flask):** Backend web framework.
- **SQLite:** Lightweight relational database.
- **HTML/CSS (Jinja2 templates):** Frontend interface.
- **Bootstrap:** For simple styling and responsive design.
- **(Future)** Tesseract OCR or Google Vision API for receipt scanning.

---

## Project Structure

project/  
├── app.py # Main Flask application  
├── groceries.db # SQLite database  
├── templates/ # HTML templates  
│   ├── layout.html # Base layout  
│   ├── index.html # Inventory dashboard  
│   └── add.html # Form for adding groceries  
├── static/ # CSS/JS files  
│   └── styles.css  
├── README.md # Project documentation  

---

## Setup & Installation
1. Clone the repository:
   git clone https://github.com/deokhwajeong/grocery-inventory-tracker.git  
   cd grocery-inventory-tracker  

2. Install dependencies:
   pip install -r requirements.txt  

3. Initialize the database:
   sqlite3 groceries.db < schema.sql  

4. Run the Flask app:
   flask run  

5. Open in your browser at:  
   http://127.0.0.1:5000  

---

## Files
- **app.py** – Contains all Flask routes (/, /add, etc.), handles database operations.  
- **groceries.db** – SQLite database file that persists grocery data.  
- **templates/index.html** – Displays the current grocery inventory in a table.  
- **templates/add.html** – Simple form for adding grocery items.  
- **templates/layout.html** – Base template for consistent styling.  
- **static/styles.css** – Custom CSS for table styling and layout.  
- **README.md** – Documentation of the project.  

---

## Design Decisions
- I chose Flask over Django to keep the project lightweight and easy to set up for local use.  
- SQLite was chosen instead of MySQL/Postgres because it requires no external server and fits the small scale of this app.  
- The manual entry version was prioritized for submission to guarantee functionality within the project deadline.  
- OCR integration was considered, but postponed to avoid scope creep. Instead, I documented it as a future enhancement.  

---

## Challenges
- Parsing OCR results can be messy, since receipts vary by store format.  
- Designing the database schema was straightforward, but I had to think about scalability (e.g., what if we also want to track expiration dates or categories in the future?).  
- Balancing between “just enough for CS50 Final Project” vs. “something actually useful at home” was an interesting tension.  

---

## Future Work
- **OCR integration:** Automate data entry by scanning receipts.  
- **Expiration tracking:** Automatically calculate expiry dates and highlight soon-to-expire items.  
- **Notifications:** Email or push alerts when items are running low or near expiry.  
- **User accounts:** Multi-user support so each family member can log in.  

---

## Acknowledgements
- Inspired by daily life in my kitchen 😊  
- Some coding assistance provided with the help of AI tools (ChatGPT), cited here as per course guidelines.  
