#!/usr/bin/env python3
"""
OCR API Test Script with URL Support

Usage:
    python test_ocr_url.py <image_url>
    python test_ocr_url.py <local_file_path>
    python test_ocr_url.py  # Uses default test image

Examples:
    python test_ocr_url.py https://drive.google.com/file/d/1abc123/view
    python test_ocr_url.py https://example.com/image.jpg
    python test_ocr_url.py ./business_card.jpg
"""

import requests
import sys
import os
import re
from pathlib import Path
import tempfile
from urllib.parse import urlparse, parse_qs
import json
from typing import Optional, Dict, Any

# Configuration
BASE_URL = "http://localhost:8001"  # Change to 8001 for regex version
UPLOAD_ENDPOINT = f"{BASE_URL}/ocr/business-card"

def extract_google_drive_id(url: str) -> Optional[str]:
    """Extract file ID from Google Drive URL."""
    patterns = [
        r'/file/d/([a-zA-Z0-9-_]+)',
        r'id=([a-zA-Z0-9-_]+)',
        r'/open\?id=([a-zA-Z0-9-_]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_google_drive_download_url(file_id: str) -> str:
    """Convert Google Drive file ID to direct download URL."""
    return f"https://drive.google.com/uc?export=download&id={file_id}"

def download_file(url: str, timeout: int = 30) -> Optional[bytes]:
    """Download file from URL and return bytes."""
    try:
        print(f"📥 Downloading from: {url}")
        
        # Handle Google Drive URLs
        if 'drive.google.com' in url:
            file_id = extract_google_drive_id(url)
            if file_id:
                url = get_google_drive_download_url(file_id)
                print(f"📄 Google Drive file ID: {file_id}")
            else:
                print("❌ Could not extract Google Drive file ID")
                return None
        
        # Download the file
        response = requests.get(url, timeout=timeout, stream=True)
        response.raise_for_status()
        
        # Check if it's an image
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('image/'):
            print(f"⚠️  Warning: Content-Type is '{content_type}', not an image")
        
        content = response.content
        print(f"✅ Downloaded {len(content):,} bytes")
        return content
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Download error: {str(e)}")
        return None

def test_ocr_api(image_data: bytes, filename: str = "image.jpg") -> Optional[Dict[str, Any]]:
    """Test the OCR API with image data."""
    try:
        # Determine content type from filename
        ext = Path(filename).suffix.lower()
        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.webp': 'image/webp'
        }
        content_type = content_types.get(ext, 'image/jpeg')
        
        # Prepare the file for upload
        files = {
            "file": (filename, image_data, content_type)
        }
        
        print(f"\n🚀 Sending request to {UPLOAD_ENDPOINT}...")
        print(f"📎 File: {filename} ({content_type})")
        
        response = requests.post(UPLOAD_ENDPOINT, files=files)
        
        if response.status_code == 200:
            print("\n✅ Success! Business card information extracted:")
            print("-" * 50)
            
            data = response.json()
            
            # Pretty print the results
            for field, value in data.items():
                if value:
                    print(f"📌 {field.capitalize()}: {value}")
                else:
                    print(f"❌ {field.capitalize()}: Not found")
            
            print("-" * 50)
            
            # Save results to file
            output_file = f"ocr_result_{Path(filename).stem}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"\n💾 Results saved to: {output_file}")
            
            return data
            
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection Error: Make sure the server is running!")
        print("Run: uvicorn main:app --reload")
        return None
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        return None

def test_with_local_file(filepath: str) -> Optional[Dict[str, Any]]:
    """Test with a local file."""
    path = Path(filepath)
    
    if not path.exists():
        print(f"❌ File not found: {filepath}")
        return None
    
    print(f"📂 Reading local file: {filepath}")
    
    try:
        with open(path, 'rb') as f:
            image_data = f.read()
        
        print(f"✅ Read {len(image_data):,} bytes")
        return test_ocr_api(image_data, path.name)
        
    except Exception as e:
        print(f"❌ Error reading file: {str(e)}")
        return None

def create_test_image() -> bytes:
    """Create a simple test business card image."""
    from PIL import Image, ImageDraw, ImageFont
    import io
    
    print("🎨 Creating test business card image...")
    
    width, height = 600, 350
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use system font
    try:
        font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
        font_medium = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
        font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Draw business card content
    y_offset = 40
    
    draw.text((50, y_offset), "TechCorp Inc.", fill='black', font=font_large)
    y_offset += 60
    
    draw.text((50, y_offset), "John Smith", fill='black', font=font_medium)
    y_offset += 40
    
    draw.text((50, y_offset), "Senior Software Engineer", fill='gray', font=font_small)
    y_offset += 40
    
    draw.text((50, y_offset), "john.smith@techcorp.com", fill='black', font=font_small)
    y_offset += 30
    
    draw.text((50, y_offset), "+1 (555) 123-4567", fill='black', font=font_small)
    
    # Add border
    draw.rectangle([10, 10, width-10, height-10], outline='gray', width=2)
    
    # Convert to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    
    return img_bytes.getvalue()

def check_server_health() -> bool:
    """Check if the server is running."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def main():
    """Main function."""
    print("🔍 Business Card OCR API Test Tool")
    print("=" * 50)
    
    # Check server health
    if not check_server_health():
        print("❌ Server is not running!")
        print("\nTo start the server:")
        print("1. Create .env file with MISTRAL_API_KEY")
        print("2. Run: uvicorn main:app --reload")
        print("\nOr for regex version:")
        print("   uvicorn main_regex:app --reload --port 8001")
        return
    
    print("✅ Server is running")
    
    # Determine input source
    if len(sys.argv) > 1:
        input_source = sys.argv[1]
        
        # Check if it's a URL
        if input_source.startswith(('http://', 'https://')):
            # Download from URL
            image_data = download_file(input_source)
            if image_data:
                # Extract filename from URL or use default
                parsed_url = urlparse(input_source)
                filename = os.path.basename(parsed_url.path) or "downloaded_image.jpg"
                test_ocr_api(image_data, filename)
            else:
                print("❌ Failed to download image")
        else:
            # Local file
            test_with_local_file(input_source)
    else:
        # No argument provided, create test image
        print("\n📝 No input provided. Creating test image...")
        print("Usage: python test_ocr_url.py <url_or_file>")
        
        try:
            test_data = create_test_image()
            test_ocr_api(test_data, "test_business_card.png")
        except ImportError:
            print("\n❌ Pillow not installed. To create test images:")
            print("   pip install pillow")
            print("\nPlease provide an image URL or file path:")
            print("   python test_ocr_url.py <url_or_file>")

if __name__ == "__main__":
    main()