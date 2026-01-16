#!/usr/bin/env python3
"""
앱 아이콘 생성 스크립트
PWA 및 앱스토어용 다양한 크기의 아이콘을 생성합니다.
"""

from PIL import Image, ImageDraw, ImageFont
import os

# 아이콘 저장 디렉토리
ICON_DIR = "/workspaces/grocery-inventory-tracker/static/icons"
os.makedirs(ICON_DIR, exist_ok=True)

# 필요한 아이콘 크기
ICON_SIZES = [72, 96, 128, 144, 152, 192, 384, 512, 1024]

def create_icon(size):
    """
    지정된 크기의 아이콘 생성
    
    Args:
        size: 아이콘 크기 (픽셀)
    """
    # 배경색 (모노톤 베이지)
    bg_color = (245, 245, 240)
    # 메인 색상 (모노톤 브라운)
    main_color = (139, 115, 85)
    # 강조 색상 (진한 브라운)
    accent_color = (101, 84, 63)
    
    # 이미지 생성
    img = Image.new('RGB', (size, size), bg_color)
    draw = ImageDraw.Draw(img)
    
    # 원형 배경 (메인 색상)
    padding = size * 0.1
    circle_bbox = [padding, padding, size - padding, size - padding]
    draw.ellipse(circle_bbox, fill=main_color)
    
    # 쇼핑 카트 아이콘 그리기
    # 카트 몸통
    cart_width = size * 0.3
    cart_height = size * 0.25
    cart_x = size * 0.35
    cart_y = size * 0.3
    
    # 카트 바구니
    draw.rectangle(
        [cart_x, cart_y, cart_x + cart_width, cart_y + cart_height],
        fill=None,
        outline=bg_color,
        width=max(2, int(size * 0.04))
    )
    
    # 손잡이
    handle_start = (cart_x + cart_width, cart_y)
    handle_end = (cart_x + cart_width + size * 0.08, cart_y - size * 0.08)
    draw.line([handle_start, handle_end], fill=bg_color, width=max(2, int(size * 0.04)))
    
    # 바퀴
    wheel_radius = size * 0.04
    wheel_y = cart_y + cart_height + wheel_radius * 1.5
    
    # 왼쪽 바퀴
    left_wheel_x = cart_x + cart_width * 0.3
    draw.ellipse(
        [
            left_wheel_x - wheel_radius,
            wheel_y - wheel_radius,
            left_wheel_x + wheel_radius,
            wheel_y + wheel_radius
        ],
        fill=bg_color
    )
    
    # 오른쪽 바퀴
    right_wheel_x = cart_x + cart_width * 0.7
    draw.ellipse(
        [
            right_wheel_x - wheel_radius,
            wheel_y - wheel_radius,
            right_wheel_x + wheel_radius,
            wheel_y + wheel_radius
        ],
        fill=bg_color
    )
    
    # 체크마크 (스마트 추적 의미)
    check_size = size * 0.15
    check_x = cart_x + cart_width * 0.5 - check_size * 0.3
    check_y = cart_y + cart_height * 0.3
    
    # 체크마크 선
    check_points = [
        (check_x, check_y + check_size * 0.5),
        (check_x + check_size * 0.3, check_y + check_size * 0.8),
        (check_x + check_size * 0.8, check_y)
    ]
    draw.line(check_points, fill=accent_color, width=max(2, int(size * 0.03)), joint="curve")
    
    # 파일 저장
    filepath = os.path.join(ICON_DIR, f"icon-{size}x{size}.png")
    img.save(filepath, "PNG")
    print(f"✅ {filepath} 생성 완료")
    
    return filepath

def create_apple_touch_icon():
    """iOS용 Apple Touch 아이콘 생성 (180x180)"""
    size = 180
    img = Image.new('RGB', (size, size), (245, 245, 240))
    draw = ImageDraw.Draw(img)
    
    # 원형 배경
    padding = size * 0.1
    draw.ellipse([padding, padding, size - padding, size - padding], fill=(139, 115, 85))
    
    # 간단한 쇼핑 카트
    cart_width = size * 0.3
    cart_height = size * 0.25
    cart_x = size * 0.35
    cart_y = size * 0.3
    
    draw.rectangle(
        [cart_x, cart_y, cart_x + cart_width, cart_y + cart_height],
        outline=(245, 245, 240),
        width=3
    )
    
    # 손잡이
    draw.line(
        [(cart_x + cart_width, cart_y), (cart_x + cart_width + 15, cart_y - 15)],
        fill=(245, 245, 240),
        width=3
    )
    
    # 바퀴
    wheel_radius = 7
    wheel_y = cart_y + cart_height + 10
    for wheel_x in [cart_x + cart_width * 0.3, cart_x + cart_width * 0.7]:
        draw.ellipse(
            [wheel_x - wheel_radius, wheel_y - wheel_radius,
             wheel_x + wheel_radius, wheel_y + wheel_radius],
            fill=(245, 245, 240)
        )
    
    filepath = os.path.join(ICON_DIR, "apple-touch-icon.png")
    img.save(filepath, "PNG")
    print(f"✅ {filepath} 생성 완료")

def main():
    """메인 함수"""
    print("🎨 앱 아이콘 생성 중...")
    
    # 다양한 크기의 아이콘 생성
    for size in ICON_SIZES:
        create_icon(size)
    
    # Apple Touch 아이콘
    create_apple_touch_icon()
    
    # 파비콘 (32x32)
    create_icon(32)
    
    print("\n✨ 모든 아이콘 생성 완료!")
    print(f"📁 저장 위치: {ICON_DIR}")

if __name__ == "__main__":
    main()
