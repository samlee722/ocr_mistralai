import requests
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import os

# API endpoint
BASE_URL = "http://localhost:8000"
UPLOAD_ENDPOINT = f"{BASE_URL}/ocr/business-card"

def create_sample_business_card():
    """Create a sample business card image for testing"""
    
    # Create a white background
    width, height = 600, 350
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a better font, fallback to default if not available
    try:
        font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
        font_medium = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
        font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Draw business card information
    y_offset = 40
    
    # Company name
    draw.text((50, y_offset), "TechCorp Inc.", fill='black', font=font_large)
    y_offset += 60
    
    # Name
    draw.text((50, y_offset), "John Smith", fill='black', font=font_medium)
    y_offset += 40
    
    # Position
    draw.text((50, y_offset), "Senior Software Engineer", fill='gray', font=font_small)
    y_offset += 40
    
    # Email
    draw.text((50, y_offset), "john.smith@techcorp.com", fill='black', font=font_small)
    y_offset += 30
    
    # Phone
    draw.text((50, y_offset), "+1 (555) 123-4567", fill='black', font=font_small)
    
    # Add a simple border
    draw.rectangle([10, 10, width-10, height-10], outline='gray', width=2)
    
    # Save the image
    img.save("example.png")
    print("✅ Created sample business card: example.png")
    
    return img

def test_with_generated_card():
    """Test OCR with a generated business card"""
    
    # Create sample card if it doesn't exist
    if not os.path.exists("example.png"):
        print("📝 Creating sample business card...")
        create_sample_business_card()
    
    # Test the API
    with open("example.png", "rb") as f:
        files = {"file": ("example.png", f, "image/png")}
        
        try:
            print(f"\n🚀 Sending request to {UPLOAD_ENDPOINT}...")
            response = requests.post(UPLOAD_ENDPOINT, files=files)
            
            if response.status_code == 200:
                print("\n✅ Success! Extracted information:")
                print("-" * 50)
                
                data = response.json()
                expected = {
                    "company": "TechCorp Inc.",
                    "position": "Senior Software Engineer",
                    "name": "John Smith",
                    "phone": "+1 (555) 123-4567",
                    "email": "john.smith@techcorp.com"
                }
                
                for field, expected_value in expected.items():
                    actual_value = data.get(field)
                    status = "✅" if actual_value else "❌"
                    print(f"{status} {field.capitalize()}: {actual_value or 'Not found'}")
                    if expected_value and actual_value:
                        print(f"   Expected: {expected_value}")
                
                print("-" * 50)
                return data
            else:
                print(f"\n❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("\n❌ Connection Error: Server is not running!")
            print("Please run: uvicorn main:app --reload")
        except Exception as e:
            print(f"\n❌ Unexpected error: {str(e)}")

if __name__ == "__main__":
    print("🧪 Business Card OCR API Test")
    print("=" * 50)
    
    # Check if server is running
    try:
        health = requests.get(f"{BASE_URL}/health")
        if health.status_code == 200:
            print("✅ Server is running")
            test_with_generated_card()
        else:
            print("❌ Server health check failed")
    except:
        print("❌ Server is not running!")
        print("\nTo start the server:")
        print("1. Create .env file with MISTRAL_API_KEY")
        print("2. Run: uvicorn main:app --reload")