#!/usr/bin/env python3
"""
OCR 방식 비교 테스트
- OCR API 전용
- Vision Model 전용
"""

import requests
import sys
import time
from pathlib import Path
import json

def test_ocr_api(image_path: str, port: int = 8002):
    """OCR API 전용 테스트"""
    print("\n" + "="*50)
    print("🔍 Testing OCR API Only")
    print("="*50)
    
    url = f"http://localhost:{port}/ocr/extract-text"
    
    try:
        with open(image_path, 'rb') as f:
            files = {"file": (Path(image_path).name, f, "image/jpeg")}
            
            start_time = time.time()
            response = requests.post(url, files=files)
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success! (Time: {elapsed_time:.2f}s)")
                print(f"\n📝 OCR Extracted Text:")
                print("-" * 50)
                print(data['text'])
                print("-" * 50)
                
                if data.get('confidence'):
                    print(f"\n📊 Confidence: {data['confidence']}")
                
                # Save to file
                with open("ocr_api_result.txt", "w", encoding="utf-8") as f:
                    f.write(data['text'])
                print(f"\n💾 Saved to: ocr_api_result.txt")
                
                return data
            else:
                print(f"❌ Error: {response.status_code}")
                print(response.text)
                
    except requests.exceptions.ConnectionError:
        print("❌ Server not running on port", port)
        print("Run: uvicorn main_ocr_only:app --reload --port", port)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    return None

def test_vision_model(image_path: str, port: int = 8003):
    """Vision Model 전용 테스트"""
    print("\n" + "="*50)
    print("👁️ Testing Vision Model Only")
    print("="*50)
    
    url = f"http://localhost:{port}/ocr/vision-extract"
    
    try:
        with open(image_path, 'rb') as f:
            files = {"file": (Path(image_path).name, f, "image/jpeg")}
            
            start_time = time.time()
            response = requests.post(url, files=files)
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success! (Time: {elapsed_time:.2f}s)")
                print(f"🤖 Model Used: {data['model_used']}")
                print(f"\n📝 Vision Model Extracted Text:")
                print("-" * 50)
                print(data['text'])
                print("-" * 50)
                
                # Save to file
                with open("vision_model_result.txt", "w", encoding="utf-8") as f:
                    f.write(data['text'])
                print(f"\n💾 Saved to: vision_model_result.txt")
                
                return data
            else:
                print(f"❌ Error: {response.status_code}")
                print(response.text)
                
    except requests.exceptions.ConnectionError:
        print("❌ Server not running on port", port)
        print("Run: uvicorn main_vision_only:app --reload --port", port)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    return None

def compare_results():
    """두 결과 비교"""
    print("\n" + "="*50)
    print("📊 Comparison Summary")
    print("="*50)
    
    try:
        with open("ocr_api_result.txt", "r", encoding="utf-8") as f:
            ocr_text = f.read()
        
        with open("vision_model_result.txt", "r", encoding="utf-8") as f:
            vision_text = f.read()
        
        print(f"OCR API Text Length: {len(ocr_text)} chars")
        print(f"Vision Model Text Length: {len(vision_text)} chars")
        
        # 간단한 유사도 체크 (단어 단위)
        ocr_words = set(ocr_text.lower().split())
        vision_words = set(vision_text.lower().split())
        
        common_words = ocr_words & vision_words
        all_words = ocr_words | vision_words
        
        if all_words:
            similarity = len(common_words) / len(all_words) * 100
            print(f"\n📈 Word Similarity: {similarity:.1f}%")
            print(f"Common words: {len(common_words)}")
            print(f"OCR unique words: {len(ocr_words - vision_words)}")
            print(f"Vision unique words: {len(vision_words - ocr_words)}")
        
    except Exception as e:
        print(f"Could not compare results: {str(e)}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_ocr_comparison.py <image_file>")
        print("\nExample:")
        print("  python test_ocr_comparison.py business_card.jpg")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    if not Path(image_path).exists():
        print(f"❌ File not found: {image_path}")
        sys.exit(1)
    
    print(f"🖼️ Testing with image: {image_path}")
    
    # Test both methods
    ocr_result = test_ocr_api(image_path)
    vision_result = test_vision_model(image_path)
    
    # Compare results if both succeeded
    if ocr_result and vision_result:
        compare_results()
    
    print("\n✨ Testing complete!")
    print("\nTo run individual servers:")
    print("  OCR API: uvicorn main_ocr_only:app --reload --port 8002")
    print("  Vision: uvicorn main_vision_only:app --reload --port 8003")

if __name__ == "__main__":
    main()