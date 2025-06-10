from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from mistralai import Mistral
import base64
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Business Card OCR API - Vision Model Only")

mistral_client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

class VisionResponse(BaseModel):
    text: str = Field(..., description="Extracted text from Vision model")
    model_used: str = Field(..., description="Vision model used")

def encode_image(image_bytes: bytes) -> str:
    """Encode image bytes to base64."""
    return base64.b64encode(image_bytes).decode('utf-8')

@app.post("/ocr/vision-extract", response_model=VisionResponse)
async def extract_with_vision(file: UploadFile = File(...)):
    """Extract text from business card using Vision model only."""
    try:
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Only image files are supported")
        
        # Read file content
        content = await file.read()
        
        # Encode image to base64
        base64_image = encode_image(content)
        
        # Determine image type from content_type
        image_type = file.content_type.split('/')[-1]  # e.g., 'jpeg', 'png'
        
        # Use Vision model to extract text
        print(f"🔍 Processing image with Vision model...")
        
        # Prepare messages for Vision model
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Please extract all text from this business card image. Return only the text content, preserving the layout as much as possible."
                    },
                    {
                        "type": "image_url",
                        "image_url": f"data:image/{image_type};base64,{base64_image}"
                    }
                ]
            }
        ]
        
        # Try different vision models
        vision_models = [
            "pixtral-large-latest",
            "mistral-large-latest",
            "pixtral-12b-latest",
            "pixtral-12b"
        ]
        
        model_used = None
        extracted_text = None
        
        for model in vision_models:
            try:
                print(f"🔄 Trying model: {model}")
                chat_response = mistral_client.chat.complete(
                    model=model,
                    messages=messages
                )
                
                # Extract text from response
                extracted_text = chat_response.choices[0].message.content
                model_used = model
                print(f"✅ Success with model: {model}")
                break
                
            except Exception as e:
                print(f"❌ Failed with {model}: {str(e)}")
                continue
        
        if not extracted_text:
            raise HTTPException(
                status_code=500, 
                detail="Failed to extract text with any available vision model"
            )
        
        print(f"📝 Extracted text length: {len(extracted_text)} characters")
        
        return VisionResponse(
            text=extracted_text,
            model_used=model_used
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.get("/")
async def root():
    return {
        "message": "Business Card OCR API - Vision Model Only Version",
        "endpoint": "/ocr/vision-extract",
        "description": "Returns raw text extracted by Vision model without any parsing"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)