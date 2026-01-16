# Screenshots Guide

This folder contains screenshots for the project README.

## Required Screenshots

### 1. dashboard.png
- **Description**: Main inventory dashboard
- **What to capture**:
  - Full page showing the item list
  - Search bar and filter dropdowns
  - Category tabs or badges
  - Statistics section (total items, expiring soon)
  - At least 5-7 items visible
- **Recommended size**: 1200x800px
- **Tips**: Show diverse items with different expiry statuses

### 2. ocr-upload.png
- **Description**: OCR receipt upload page
- **What to capture**:
  - Camera/file upload button
  - Instructions text
  - Mobile camera interface (if on mobile)
  - Progress indicator if visible
- **Recommended size**: 600x800px (portrait) or 1200x600px (landscape)
- **Tips**: Show the clean upload interface

### 3. ocr-review.png
- **Description**: OCR review page with extracted items
- **What to capture**:
  - List of extracted items
  - Confidence score badges (green/blue/yellow/red)
  - Edit buttons and category dropdowns
  - Checkbox selections
  - "Add to Inventory" button
- **Recommended size**: 1200x800px
- **Tips**: Show at least 5-6 extracted items with various confidence levels

### 4. mobile-camera.png
- **Description**: Mobile camera interface
- **What to capture**:
  - Phone's native camera view
  - Receipt being photographed
  - Camera button/controls
- **Recommended size**: 375x667px (iPhone) or 360x640px (Android)
- **Device**: Use actual mobile device or browser DevTools mobile emulation

### 5. mobile-preview.png
- **Description**: Image preview before processing
- **What to capture**:
  - Preview of uploaded/captured receipt image
  - "Process Receipt" or similar button
  - Loading state or progress bar
- **Recommended size**: 375x667px
- **Tips**: Show a clear receipt image

### 6. mobile-results.png
- **Description**: OCR results on mobile
- **What to capture**:
  - Mobile view of extracted items
  - Touch-friendly buttons
  - Responsive layout
- **Recommended size**: 375x667px
- **Tips**: Demonstrate mobile-optimized UI

### 7. add-edit.png
- **Description**: Add/Edit item form
- **What to capture**:
  - Form fields (name, quantity, dates, category, notes)
  - Category dropdown expanded (optional)
  - Submit button
  - Clean form styling
- **Recommended size**: 800x1000px
- **Tips**: Fill in sample data to show how it looks

### 8. expiry-warnings.png
- **Description**: Items with expiry warnings
- **What to capture**:
  - Items expiring soon (yellow/orange warning)
  - Expired items (red border)
  - Normal items (no warning)
  - Days until expiry information
- **Recommended size**: 1200x600px
- **Tips**: Ensure at least one expired and one expiring-soon item is visible

### 9. category-stats.png
- **Description**: Category distribution statistics
- **What to capture**:
  - Dashboard statistics section
  - Total items count
  - Expiring soon count
  - Category breakdown/chart
- **Recommended size**: 1200x400px
- **Tips**: Show diverse category distribution

## How to Take Screenshots

### On Desktop
1. Run the application: `python app.py`
2. Open browser to `http://localhost:5000`
3. Navigate to each page
4. Use screenshot tools:
   - **Windows**: Win + Shift + S
   - **macOS**: Cmd + Shift + 4
   - **Linux**: Screenshot app or Shift + PrtScn
5. Save with exact filenames listed above

### On Mobile
1. Deploy app or use port forwarding to access from mobile
2. Navigate to each page
3. Take screenshots using device's native screenshot function
4. Transfer images to computer
5. Rename files to match the required names

### Using Browser DevTools (for mobile views)
1. Open Chrome DevTools (F12)
2. Click "Toggle device toolbar" (Ctrl+Shift+M)
3. Select device (iPhone 12, Pixel 5, etc.)
4. Take screenshots using DevTools or browser extensions

## Image Editing Tips

### Recommended Tools
- **Crop/Resize**: GIMP, Photoshop, or online tools like Photopea
- **Annotation**: Add arrows, highlights, or text if needed
- **Optimization**: Use tools like TinyPNG to reduce file size

### Best Practices
- Use PNG format for better quality
- Optimize images to keep file size under 500KB each
- Ensure text is readable
- Use consistent dimensions for similar types of screenshots
- Add subtle borders or shadows if needed for clarity

## Privacy Note
- **DO NOT** include real personal information in screenshots
- Use sample/dummy data for all fields
- Blur or redact any sensitive information
- Use generic names like "Milk", "Bread", "Apple" etc.

## After Adding Screenshots
1. Verify all images are in this folder
2. Check that filenames match exactly (case-sensitive)
3. Test README by viewing on GitHub
4. Optimize images if total size > 3MB

---

**Quick Checklist:**
- [ ] dashboard.png
- [ ] ocr-upload.png
- [ ] ocr-review.png
- [ ] mobile-camera.png
- [ ] mobile-preview.png
- [ ] mobile-results.png
- [ ] add-edit.png
- [ ] expiry-warnings.png
- [ ] category-stats.png

Once all screenshots are added, the README will look professional and complete! 🎉
