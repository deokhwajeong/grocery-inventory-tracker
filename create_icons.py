#!/usr/bin/env python3
"""
App Icon Generation Script
Generates icons in various sizes for PWA and app stores.
"""

from PIL import Image, ImageDraw, ImageFont
import os

# Icon save directory
ICON_DIR = "/workspaces/grocery-inventory-tracker/static/icons"
os.makedirs(ICON_DIR, exist_ok=True)

# Required icon sizes
ICON_SIZES = [72, 96, 128, 144, 152, 192, 384, 512, 1024]

def create_icon(size):
    """
    Create icon with specified size
    
    Args:
        size: Icon size (pixels)
    """
    # Background color (monotone beige)
    bg_color = (245, 245, 240)
    # Main color (monotone brown)
    main_color = (139, 115, 85)
    # Accent color (dark brown)
    accent_color = (101, 84, 63)
    
    # Create image
    img = Image.new('RGB', (size, size), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Circular background (main color)
    padding = size * 0.1
    circle_bbox = [padding, padding, size - padding, size - padding]
    draw.ellipse(circle_bbox, fill=main_color)
    
    # Draw shopping cart icon
    # Cart body
    cart_width = size * 0.3
    cart_height = size * 0.25
    cart_x = size * 0.35
    cart_y = size * 0.3
    
    # Cart basket
    draw.rectangle(
        [cart_x, cart_y, cart_x + cart_width, cart_y + cart_height],
        fill=None,
        outline=bg_color,
        width=max(2, int(size * 0.04))
    )
    
    # Handle
    handle_start = (cart_x + cart_width, cart_y)
    handle_end = (cart_x + cart_width + size * 0.08, cart_y - size * 0.08)
    draw.line([handle_start, handle_end], fill=bg_color, width=max(2, int(size * 0.04)))
    
    # Wheels
    wheel_radius = size * 0.04
    wheel_y = cart_y + cart_height + wheel_radius * 1.5
    
    # Left wheel
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
    
    # Right wheel
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
    
    # Checkmark (smart tracking indicator)
    check_size = size * 0.15
    check_x = cart_x + cart_width * 0.5 - check_size * 0.3
    check_y = cart_y + cart_height * 0.3
    
    # Checkmark line
    check_points = [
        (check_x, check_y + check_size * 0.5),
        (check_x + check_size * 0.3, check_y + check_size * 0.8),
        (check_x + check_size * 0.8, check_y)
    ]
    draw.line(check_points, fill=accent_color, width=max(2, int(size * 0.03)), joint="curve")
    
    # Save file
    filepath = os.path.join(ICON_DIR, f"icon-{size}x{size}.png")
    img.save(filepath, "PNG")
    print(f"✅ Created {filepath}")
    
    return filepath

def create_apple_touch_icon():
    """Generate Apple Touch Icon for iOS (180x180)"""
    size = 180
    img = Image.new('RGB', (size, size), (245, 245, 240))
    draw = ImageDraw.Draw(img)
    
    # Circular background
    padding = size * 0.1
    draw.ellipse([padding, padding, size - padding, size - padding], fill=(139, 115, 85))
    
    # Simple shopping cart
    cart_width = size * 0.3
    cart_height = size * 0.25
    cart_x = size * 0.35
    cart_y = size * 0.3
    
    draw.rectangle(
        [cart_x, cart_y, cart_x + cart_width, cart_y + cart_height],
        outline=(245, 245, 240),
        width=3
    )
    
    # Handle
    draw.line(
        [(cart_x + cart_width, cart_y), (cart_x + cart_width + 15, cart_y - 15)],
        fill=(245, 245, 240),
        width=3
    )
    
    # Wheels
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
    print(f"✅ Created {filepath}")

def main():
    """Main function"""
    print("🎨 Creating app icons...")
    
    # Create icons in various sizes
    for size in ICON_SIZES:
        create_icon(size)
    
    # Apple Touch icon
    create_apple_touch_icon()
    
    # Favicon (32x32)
    create_icon(32)
    
    print("\n✨ All icons created successfully!")
    print(f"📁 Save location: {ICON_DIR}")

if __name__ == "__main__":
    main()
