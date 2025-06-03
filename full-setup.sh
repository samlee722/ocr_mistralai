#!/bin/bash
# Complete setup for OCR API and test tools

echo "🚀 OCR API Complete Setup"
echo "========================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required. Please install Python 3.8 or higher."
    exit 1
fi

# Create virtual environment (optional)
read -p "Create virtual environment? (recommended) (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3 -m venv venv
    source venv/bin/activate
    echo "✅ Virtual environment created and activated"
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Check for .env file
if [ ! -f .env ]; then
    echo ""
    echo "⚠️  No .env file found!"
    echo "Creating .env file..."
    
    read -p "Enter your MISTRAL_API_KEY: " api_key
    echo "MISTRAL_API_KEY=$api_key" > .env
    echo "✅ .env file created"
else
    echo "✅ .env file exists"
fi

# Make test scripts executable
chmod +x test_ocr_url.py
echo "✅ Test scripts are executable"

# Create convenience scripts
cat > ocr-start.sh << 'EOF'
#!/bin/bash
# Start OCR server

echo "Starting OCR API server..."
echo "Choose version:"
echo "1) Main (OCR API) - Port 8000"
echo "2) Regex (Vision + Regex) - Port 8001"
read -p "Enter choice (1 or 2): " choice

if [ "$choice" = "1" ]; then
    uvicorn main:app --reload
else
    uvicorn main_regex:app --reload --port 8001
fi
EOF

chmod +x ocr-start.sh

# Create test runner
cat > ocr-run.sh << 'EOF'
#!/bin/bash
# Run OCR test

if [ $# -eq 0 ]; then
    echo "Usage: ./ocr-run.sh <url_or_file>"
    echo "Example: ./ocr-run.sh https://drive.google.com/file/d/123/view"
    exit 1
fi

python test_ocr_url.py "$1"
EOF

chmod +x ocr-run.sh

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Start the server:     ./ocr-start.sh"
echo "2. Test with an image:   ./ocr-run.sh <url_or_file>"
echo ""
echo "📝 Examples:"
echo "   ./ocr-run.sh https://drive.google.com/file/d/YOUR_ID/view"
echo "   ./ocr-run.sh ./business_card.jpg"
echo "   ./ocr-run.sh  # Creates test image"
echo ""
echo "✨ Happy OCR testing!"