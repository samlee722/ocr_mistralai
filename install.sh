#!/bin/bash
# OCR Test Tools Installation Script

echo "🔧 Installing OCR Test Tools..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required"
    exit 1
fi

# Make scripts executable
chmod +x test_ocr_url.py
chmod +x ocr
chmod +x ocr_advanced.py

echo "✅ Scripts are now executable"

# Optional: Install globally
read -p "Install globally to /usr/local/bin? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo cp test_ocr_url.py /usr/local/bin/ocr-test
    sudo cp ocr /usr/local/bin/ocr
    sudo cp ocr_advanced.py /usr/local/bin/ocr-adv
    echo "✅ Installed globally. You can now use:"
    echo "   ocr <url_or_file>"
    echo "   ocr-test <url_or_file>"
    echo "   ocr-adv <url_or_file> [options]"
else
    echo "✅ Local installation complete. Use:"
    echo "   ./test_ocr_url.py <url_or_file>"
    echo "   ./ocr <url_or_file>"
    echo "   ./ocr_advanced.py <url_or_file> [options]"
fi

echo ""
echo "📝 Quick Start:"
echo "   1. Start server: uvicorn main:app --reload"
echo "   2. Test with URL: ocr https://drive.google.com/file/d/YOUR_ID/view"
echo ""
echo "✨ Done!"