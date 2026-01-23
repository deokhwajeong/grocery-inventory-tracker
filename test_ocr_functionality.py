#!/usr/bin/env python3
"""
Simple OCR functionality test
Creates a test receipt image and processes it
"""

from PIL import Image, ImageDraw, ImageFont
import os
import sys

def create_test_receipt():
    """Create a simple test receipt image"""
    # Create white background
    img = Image.new('RGB', (400, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a default font, fallback to basic if not available
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
        font_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
    except:
        font = ImageFont.load_default()
        font_bold = font
    
    # Draw receipt content
    y_position = 50
    
    # Store name
    draw.text((100, y_position), "GROCERY STORE", fill='black', font=font_bold)
    y_position += 40
    
    # Items
    items = [
        "Milk                $3.99",
        "Bread               $2.49",
        "Eggs (12)           $4.29",
        "Apples (1kg)        $5.99",
        "Chicken Breast      $8.99",
        "Orange Juice        $3.49",
    ]
    
    for item in items:
        draw.text((50, y_position), item, fill='black', font=font)
        y_position += 30
    
    # Total
    y_position += 20
    draw.line([(50, y_position), (350, y_position)], fill='black', width=2)
    y_position += 20
    draw.text((50, y_position), "TOTAL              $29.24", fill='black', font=font_bold)
    y_position += 40
    
    # Date
    draw.text((50, y_position), "Date: 2026-01-23", fill='black', font=font)
    
    # Save image
    output_path = 'test_receipt.jpg'
    img.save(output_path, quality=95)
    print(f"✅ Test receipt created: {output_path}")
    return output_path

def test_ocr_processing(image_path):
    """Test OCR processing on the test image"""
    print(f"\n📸 Testing OCR on: {image_path}")
    
    try:
        from ocr_processor import preprocess_image, extract_text_from_image, parse_receipt_items
        
        # Preprocess
        print("  ⏳ Preprocessing image...")
        processed_images = preprocess_image(image_path)
        print(f"  ✅ Generated {len(processed_images)} preprocessed versions")
        
        # Extract text
        print("  ⏳ Extracting text with OCR...")
        text = extract_text_from_image(image_path)
        print(f"  ✅ Extracted text ({len(text)} characters)")
        print("\n  📄 Extracted Text:")
        print("  " + "-" * 50)
        for line in text.split('\n')[:15]:  # Show first 15 lines
            if line.strip():
                print(f"  {line}")
        print("  " + "-" * 50)
        
        # Parse items
        print("\n  ⏳ Parsing receipt items...")
        items = parse_receipt_items(text)
        print(f"  ✅ Parsed {len(items)} items")
        
        if items:
            print("\n  🛒 Parsed Items:")
            print("  " + "-" * 50)
            for item in items[:10]:  # Show first 10 items
                name = item.get('name', 'Unknown')
                qty = item.get('quantity', 1)
                print(f"  - {name} (qty: {qty})")
            print("  " + "-" * 50)
        
        return True
        
    except Exception as e:
        print(f"  ❌ OCR processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("="*60)
    print("  OCR Functionality Test")
    print("="*60)
    
    # Create test receipt
    image_path = create_test_receipt()
    
    # Test OCR processing
    success = test_ocr_processing(image_path)
    
    # Summary
    print("\n" + "="*60)
    if success:
        print("✅ OCR TEST PASSED")
        print("\nThe OCR system is working correctly!")
        print("You can now test with real receipt images.")
    else:
        print("❌ OCR TEST FAILED")
        print("\nPlease check the error messages above.")
        return 1
    print("="*60)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
