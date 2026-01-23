#!/usr/bin/env python3
"""
Cross-platform OCR Verification Script
Tests OCR functionality and dependencies across different environments
"""

import sys
import os
import subprocess
from pathlib import Path

def print_header(text):
    """Print formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def check_command(cmd, name):
    """Check if a command is available"""
    try:
        result = subprocess.run([cmd, '--version'], capture_output=True, text=True, timeout=5)
        print(f"✅ {name}: INSTALLED")
        print(f"   Version: {result.stdout.split()[0] if result.stdout else 'Unknown'}")
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print(f"❌ {name}: NOT FOUND")
        return False
    except Exception as e:
        print(f"⚠️  {name}: ERROR - {e}")
        return False

def check_python_package(package_name):
    """Check if a Python package is installed"""
    try:
        __import__(package_name)
        print(f"✅ {package_name}: INSTALLED")
        return True
    except ImportError:
        print(f"❌ {package_name}: NOT INSTALLED")
        return False

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if Path(filepath).exists():
        print(f"✅ {description}: FOUND")
        return True
    else:
        print(f"❌ {description}: MISSING")
        return False

def test_ocr_import():
    """Test importing OCR modules"""
    try:
        from ocr_processor import preprocess_image, extract_text_from_image
        print("✅ OCR processor modules imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import OCR modules: {e}")
        return False

def test_image_processing():
    """Test basic image processing"""
    try:
        import cv2
        import numpy as np
        from PIL import Image
        
        # Create a simple test image
        test_img = np.zeros((100, 100, 3), dtype=np.uint8)
        test_img[25:75, 25:75] = [255, 255, 255]
        
        # Test OpenCV
        gray = cv2.cvtColor(test_img, cv2.COLOR_BGR2GRAY)
        
        # Test PIL
        pil_img = Image.fromarray(test_img)
        
        print("✅ Image processing libraries working correctly")
        return True
    except Exception as e:
        print(f"❌ Image processing test failed: {e}")
        return False

def check_platform_info():
    """Display platform information"""
    import platform
    print(f"Operating System: {platform.system()} {platform.release()}")
    print(f"Platform: {platform.platform()}")
    print(f"Processor: {platform.processor()}")
    print(f"Python Version: {platform.python_version()}")
    print(f"Python Implementation: {platform.python_implementation()}")

def test_capacitor_setup():
    """Check Capacitor setup for mobile platforms"""
    issues = []
    
    # Check package.json
    if not Path('package.json').exists():
        issues.append("package.json not found")
    
    # Check capacitor.config.json
    if not Path('capacitor.config.json').exists():
        issues.append("capacitor.config.json not found")
    
    # Check node_modules
    if not Path('node_modules/@capacitor/core').exists():
        issues.append("@capacitor/core not installed (run: npm install)")
    
    # Check camera handler
    if not Path('static/camera-handler.js').exists():
        issues.append("camera-handler.js not found")
    
    if issues:
        print("⚠️  Capacitor setup issues:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    else:
        print("✅ Capacitor setup looks good")
        return True

def main():
    """Main verification function"""
    print_header("OCR Cross-Platform Verification")
    
    # Platform Info
    print_header("Platform Information")
    check_platform_info()
    
    # System Dependencies
    print_header("System Dependencies")
    tesseract_ok = check_command('tesseract', 'Tesseract OCR')
    
    if not tesseract_ok:
        print("\n⚠️  INSTALLATION INSTRUCTIONS:")
        print("   Ubuntu/Debian: sudo apt-get install tesseract-ocr")
        print("   macOS: brew install tesseract")
        print("   Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
    
    # Python Dependencies
    print_header("Python Dependencies")
    packages = [
        'flask',
        'pytesseract',
        'PIL',  # Pillow
        'cv2',  # opencv-python
        'numpy'
    ]
    
    python_ok = all(check_python_package(pkg) for pkg in packages)
    
    if not python_ok:
        print("\n⚠️  INSTALLATION INSTRUCTIONS:")
        print("   pip install -r requirements.txt")
    
    # OCR Module Tests
    print_header("OCR Module Tests")
    ocr_import_ok = test_ocr_import()
    image_proc_ok = test_image_processing()
    
    # File Checks
    print_header("Required Files")
    files_ok = all([
        check_file_exists('ocr_processor.py', 'OCR Processor'),
        check_file_exists('templates/ocr.html', 'OCR Template'),
        check_file_exists('static/camera-handler.js', 'Camera Handler'),
        check_file_exists('app.py', 'Flask App')
    ])
    
    # Capacitor Setup
    print_header("Mobile Platform Setup (Capacitor)")
    capacitor_ok = test_capacitor_setup()
    
    # Summary
    print_header("Verification Summary")
    
    all_checks = {
        "Tesseract OCR": tesseract_ok,
        "Python Dependencies": python_ok,
        "OCR Modules": ocr_import_ok,
        "Image Processing": image_proc_ok,
        "Required Files": files_ok,
        "Capacitor Setup": capacitor_ok
    }
    
    passed = sum(all_checks.values())
    total = len(all_checks)
    
    print(f"\nPassed: {passed}/{total} checks\n")
    
    for check, status in all_checks.items():
        emoji = "✅" if status else "❌"
        print(f"{emoji} {check}")
    
    if passed == total:
        print("\n🎉 ALL CHECKS PASSED! OCR is ready for cross-platform deployment.")
        print("\nNext steps:")
        print("  1. Test web version: python app.py")
        print("  2. Test mobile web: Access from phone browser")
        print("  3. Build iOS: npx cap add ios && npx cap open ios")
        print("  4. Build Android: npx cap add android && npx cap open android")
        return 0
    else:
        print(f"\n⚠️  {total - passed} check(s) failed. Please fix the issues above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
