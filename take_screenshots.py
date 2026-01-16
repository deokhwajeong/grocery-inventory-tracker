#!/usr/bin/env python3
"""
자동 스크린샷 촬영 스크립트
앱의 각 페이지를 자동으로 캡처하여 PNG 파일로 저장합니다.
"""

import time
import os
import subprocess
import asyncio
from playwright.async_api import async_playwright

# 스크린샷 저장 경로
SCREENSHOTS_DIR = "/workspaces/grocery-inventory-tracker/docs/screenshots"
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# Flask 앱 프로세스
flask_process = None

def start_flask_app():
    """Flask 앱 시작"""
    global flask_process
    print("🚀 Flask 앱 시작 중...")
    flask_process = subprocess.Popen(
        ["/workspaces/grocery-inventory-tracker/.venv/bin/python", "app.py"],
        cwd="/workspaces/grocery-inventory-tracker",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(5)  # 앱이 시작될 때까지 대기
    print("✅ Flask 앱 시작 완료")

def stop_flask_app():
    """Flask 앱 종료"""
    global flask_process
    if flask_process:
        print("🛑 Flask 앱 종료 중...")
        flask_process.terminate()
        flask_process.wait()
        print("✅ Flask 앱 종료 완료")

async def take_screenshot(page, url, filename, wait_selector=None):
    """
    특정 URL의 스크린샷을 촬영합니다.
    
    Args:
        page: Playwright Page 객체
        url: 스크린샷을 촬영할 URL
        filename: 저장할 파일명
        wait_selector: 대기할 CSS 선택자
    """
    print(f"📸 {filename} 촬영 중...")
    await page.goto(url)
    
    # 페이지 로딩 대기
    if wait_selector:
        await page.wait_for_selector(wait_selector, timeout=10000)
    else:
        await page.wait_for_timeout(2000)
    
    # 스크린샷 저장
    filepath = os.path.join(SCREENSHOTS_DIR, filename)
    await page.screenshot(path=filepath, full_page=True)
    print(f"✅ {filename} 저장 완료")

async def main():
    """메인 함수"""
    try:
        # Flask 앱 시작
        start_flask_app()
        
        async with async_playwright() as p:
            # 브라우저 시작
            browser = await p.chromium.launch(headless=True)
            
            # 데스크톱 뷰
            context = await browser.new_context(viewport={"width": 1920, "height": 1080})
            page = await context.new_page()
            base_url = "http://localhost:5000"
            
            # 1. 대시보드 스크린샷
            await take_screenshot(
                page, 
                f"{base_url}/", 
                "dashboard.png",
                wait_selector="body"
            )
            
            # 2. 아이템 추가 페이지
            await take_screenshot(
                page,
                f"{base_url}/add",
                "add-edit.png",
                wait_selector="form"
            )
            
            # 3. OCR 업로드 페이지
            await take_screenshot(
                page,
                f"{base_url}/ocr",
                "ocr-upload.png",
                wait_selector="body"
            )
            
            # 4. 카테고리 통계 (대시보드)
            await take_screenshot(
                page,
                f"{base_url}/",
                "category-stats.png",
                wait_selector="body"
            )
            
            # 5. 만료 경고
            await take_screenshot(
                page,
                f"{base_url}/",
                "expiry-warnings.png",
                wait_selector="body"
            )
            
            await context.close()
            
            # 모바일 뷰 (iPhone 12 크기)
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
            
            # OCR 리뷰 페이지 (데이터가 있다고 가정)
            await take_screenshot(
                mobile_page,
                f"{base_url}/",
                "ocr-review.png",
                wait_selector="body"
            )
            
            await mobile_context.close()
            await browser.close()
        
        print("\n✨ 모든 스크린샷 촬영 완료!")
        print(f"📁 저장 위치: {SCREENSHOTS_DIR}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Flask 앱 종료
        stop_flask_app()

if __name__ == "__main__":
    asyncio.run(main())
