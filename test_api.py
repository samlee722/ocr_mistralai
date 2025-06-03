import requests
import os
from pathlib import Path

# API endpoint
BASE_URL = "http://localhost:8001"
UPLOAD_ENDPOINT = f"{BASE_URL}/ocr/business-card"

def test_business_card_ocr():
    """Test business card OCR with example image"""
    
    # Check if example file exists
    example_file = Path("1.jpg")
    if not example_file.exists():
        print("Error: example.png not found in current directory")
        print("Please add a business card image named 'example.png' to test")
        return
    
    # Prepare the file for upload
    with open(example_file, "rb") as f:
        files = {"file": ("example.png", f, "image/png")}
        
        try:
            # Send POST request
            print(f"Sending request to {UPLOAD_ENDPOINT}...")
            response = requests.post(UPLOAD_ENDPOINT, files=files)
            
            # Check response
            if response.status_code == 200:
                print("\n✅ Success! Business card information extracted:")
                print("-" * 50)
                
                data = response.json()
                for field, value in data.items():
                    if value:
                        print(f"{field.capitalize()}: {value}")
                
                print("-" * 50)
                return data
            else:
                print(f"\n❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("\n❌ Connection Error: Make sure the server is running!")
            print("Run: uvicorn main:app --reload")
        except Exception as e:
            print(f"\n❌ Unexpected error: {str(e)}")

def test_health_check():
    """Test health check endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print("❌ Health check failed")
    except:
        print("❌ Cannot connect to server")

if __name__ == "__main__":
    print("🔍 Testing Business Card OCR API")
    print("=" * 50)
    
    # Test health check first
    test_health_check()
    print()
    
    # Test OCR
    test_business_card_ocr()