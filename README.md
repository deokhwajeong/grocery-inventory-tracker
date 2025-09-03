# Grocery Inventory Tracker
#### Video Demo: <URL HERE>
#### Description:
Grocery Inventory Tracker is a simple web application built with Flask and SQLite that helps you keep track of the items in your fridge.  
With this app, you can easily record groceries (name, quantity, and purchase date) and view your fridge inventory in a clean dashboard.  

This project started as my **CS50x Final Project**, with the goal of solving a real-world problem: reducing food waste and making it easier to know what’s inside the fridge at a glance.  
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
