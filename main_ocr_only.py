from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from mistralai import Mistral
import base64
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Business Card OCR API - OCR Only")

mistral_client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

class OCRResponse(BaseModel):
    text: str = Field(..., description="Extracted text from OCR")
    confidence: Optional[float] = Field(None, description="OCR confidence score")

def encode_image(image_bytes: bytes) -> str:
    """Encode image bytes to base64."""
    return base64.b64encode(image_bytes).decode('utf-8')

@app.post("/ocr/extract-text", response_model=OCRResponse)
async def extract_text_only(file: UploadFile = File(...)):
    """Extract raw text from business card using OCR API only."""
    try:
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Only image files are supported")
        
        # Read file content
        content = await file.read()
        
        # Encode image to base64
        base64_image = encode_image(content)
        
        # Determine image type from content_type
        image_type = file.content_type.split('/')[-1]  # e.g., 'jpeg', 'png'
        
        # Use OCR API to extract text
        print(f"🔍 Processing image with OCR API...")
        ocr_response = mistral_client.ocr.process(
            model="mistral-ocr-latest",
            document={
                "type": "image_url",
                "image_url": f"data:image/{image_type};base64,{base64_image}"
            },
            include_image_base64=True
        )
        
        # Extract text from response
        ocr_text = ocr_response.content if hasattr(ocr_response, 'content') else str(ocr_response)
        
        # Get confidence if available
        confidence = None
        if hasattr(ocr_response, 'confidence'):
            confidence = ocr_response.confidence
        
        print(f"✅ OCR extraction complete")
        print(f"📝 Extracted text length: {len(ocr_text)} characters")
        
        return OCRResponse(
            text=ocr_text,
            confidence=confidence
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.get("/")
async def root():
    return {
        "message": "Business Card OCR API - OCR Only Version",
        "endpoint": "/ocr/extract-text",
        "description": "Returns raw OCR text without any parsing"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)