#!/usr/bin/env python3
"""
Automated Screenshot Capture Script
Automatically captures each page of the app and saves as PNG files.
"""

import time
import os
import subprocess
import asyncio
from playwright.async_api import async_playwright

# Screenshot save directory
SCREENSHOTS_DIR = "/workspaces/grocery-inventory-tracker/docs/screenshots"
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# Flask app process
flask_process = None

def start_flask_app():
    """Start Flask app"""
    global flask_process
    print("🚀 Starting Flask app...")
    flask_process = subprocess.Popen(
        ["/workspaces/grocery-inventory-tracker/.venv/bin/python", "app.py"],
        cwd="/workspaces/grocery-inventory-tracker",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(5)  # Wait for app to start
    print("✅ Flask app started")

def stop_flask_app():
    """Stop Flask app"""
    global flask_process
    if flask_process:
        print("🛑 Stopping Flask app...")
        flask_process.terminate()
        flask_process.wait()
        print("✅ Flask app stopped")

async def take_screenshot(page, url, filename, wait_selector=None):
    """
    Take a screenshot of a specific URL.
    
    Args:
        page: Playwright Page object
        url: URL to capture
        filename: Filename to save
        wait_selector: CSS selector to wait for
    """
    print(f"📸 Capturing {filename}...")
    await page.goto(url)
    
    # Wait for page loading
    if wait_selector:
        await page.wait_for_selector(wait_selector, timeout=10000)
    else:
        await page.wait_for_timeout(2000)
    
    # Save screenshot
    filepath = os.path.join(SCREENSHOTS_DIR, filename)
    await page.screenshot(path=filepath, full_page=True)
    print(f"✅ {filename} saved successfully")

async def main():
    """Main function"""
    try:
        # Start Flask app
        start_flask_app()
        
        async with async_playwright() as p:
            # Start browser
            browser = await p.chromium.launch(headless=True)
            
            # Desktop view
            context = await browser.new_context(viewport={"width": 1920, "height": 1080})
            page = await context.new_page()
            base_url = "http://localhost:5000"
            
            # 1. Dashboard screenshot
            await take_screenshot(
                page, 
                f"{base_url}/", 
                "dashboard.png",
                wait_selector="body"
            )
            
            # 2. Add item page
            await take_screenshot(
                page,
                f"{base_url}/add",
                "add-edit.png",
                wait_selector="form"
            )
            
            # 3. OCR upload page
            await take_screenshot(
                page,
                f"{base_url}/ocr",
                "ocr-upload.png",
                wait_selector="body"
            )
            
            # 4. Category statistics (dashboard)
            await take_screenshot(
                page,
                f"{base_url}/",
                "category-stats.png",
                wait_selector="body"
            )
            
            # 5. Expiry warnings
            await take_screenshot(
                page,
                f"{base_url}/",
                "expiry-warnings.png",
                wait_selector="body"
            )
            
            await context.close()
            
            # Mobile view (iPhone 12 size)
            mobile_context = await browser.new_context(
                viewport={"width": 390, "height": 844},
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
            )
            mobile_page = await mobile_context.new_page()
            
            await take_screenshot(
                mobile_page,
                f"{base_url}/ocr",
                "mobile-camera.png",
                wait_selector="body"
            )
            
            await take_screenshot(
                mobile_page,
                f"{base_url}/",
                "mobile-preview.png",
                wait_selector="body"
            )
            
            await take_screenshot(
                mobile_page,
                f"{base_url}/ocr",
                "mobile-results.png",
                wait_selector="body"
            )
            
            # OCR review page (assuming data exists)
            await take_screenshot(
                mobile_page,
                f"{base_url}/",
                "ocr-review.png",
                wait_selector="body"
            )
            
            await mobile_context.close()
            await browser.close()
        
        print("\n✨ All screenshots captured successfully!")
        print(f"📁 Save location: {SCREENSHOTS_DIR}")
        
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Stop Flask app
        stop_flask_app()

if __name__ == "__main__":
    asyncio.run(main())
