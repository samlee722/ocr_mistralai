from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from mistralai import Mistral
import base64
import os
import json
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Business Card OCR API")

mistral_client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

class BusinessCardInfo(BaseModel):
    company: Optional[str] = Field(None, description="Company or organization name")
    position: Optional[str] = Field(None, description="Job title or position")
    name: Optional[str] = Field(None, description="Person's full name")
    phone: Optional[str] = Field(None, description="Phone number")
    email: Optional[str] = Field(None, description="Email address")

def encode_image(image_bytes: bytes) -> str:
    """Encode image bytes to base64."""
    return base64.b64encode(image_bytes).decode('utf-8')

@app.post("/ocr/business-card", response_model=BusinessCardInfo)
async def extract_business_card(file: UploadFile = File(...)):
    try:
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Only image files are supported")
        
        # Read file content
        content = await file.read()
        
        # Encode image to base64
        base64_image = encode_image(content)
        
        # Determine image type from content_type
        image_type = file.content_type.split('/')[-1]  # e.g., 'jpeg', 'png'
        
        # Use OCR API with base64 encoded image
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
        
        # Create prompt for structured extraction
        prompt = f"""Extract business card information from the following text.
Return a JSON object with these fields:
- company: Company or organization name
- position: Job title or position
- name: Person's full name
- phone: Phone number
- email: Email address

If any field is not found, use null.

Text from business card:
{ocr_text}

Return only valid JSON, no additional text."""
        
        # Use chat API to extract structured information
        chat_response = mistral_client.chat.complete(
            model="mistral-large-latest",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        # Parse the JSON response
        extracted_data = json.loads(chat_response.choices[0].message.content)
        
        # Create and return BusinessCardInfo
        business_card_info = BusinessCardInfo(**extracted_data)
        
        return business_card_info
        
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse AI response: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Business Card OCR API", "endpoint": "/ocr/business-card"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)