from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from mistralai import Mistral
import base64
import os
import re
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Business Card OCR API - Regex Version")

mistral_client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

class BusinessCardInfo(BaseModel):
    company: Optional[str] = None
    position: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

@app.post("/ocr/business-card", response_model=BusinessCardInfo)
async def extract_business_card(file: UploadFile = File(...)):
    """
    Extract business card information using Mistral OCR with regex parsing
    """
    import tempfile
    import uuid
    
    try:
        # Check file type
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Only image files are supported")
        
        # Read file content
        content = await file.read()
        
        # Save temporarily and upload to a file hosting service or use local file
        # For this example, we'll use the Mistral Pixtral model which supports image inputs
        base64_image = base64.b64encode(content).decode('utf-8')
        
        # Use Mistral's chat API with vision capability for OCR
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
                        "image_url": f"data:{file.content_type};base64,{base64_image}"
                    }
                ]
            }
        ]
        
        # Call Mistral's vision model
        chat_response = mistral_client.chat.complete(
            model="pixtral-12b-2024-09-04",  # Vision-capable model
            messages=messages
        )
        
        # Extract text from response
        extracted_text = chat_response.choices[0].message.content
        
        # Parse business card information using regex
        business_card_info = extract_info_from_text(extracted_text)
        
        return business_card_info
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

def extract_info_from_text(text: str) -> BusinessCardInfo:
    """
    Extract structured information from OCR text using regex
    """
    info = BusinessCardInfo()
    
    # Convert text to lines for easier processing
    lines = text.split('\n')
    
    # Email pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    # Phone pattern (Korean and international formats)
    phone_patterns = [
        r'(?:010|011|016|017|018|019)[-.\s]?\d{3,4}[-.\s]?\d{4}',  # Korean mobile
        r'0\d{1,2}[-.\s]?\d{3,4}[-.\s]?\d{4}',  # Korean landline
        r'\+82[-.\s]?\d{1,2}[-.\s]?\d{3,4}[-.\s]?\d{4}',  # International Korean
        r'\d{3}[-.\s]?\d{3,4}[-.\s]?\d{4}',  # General format
        r'\(\d{2,3}\)[-.\s]?\d{3,4}[-.\s]?\d{4}',  # With area code
        r'\+1[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'  # US format
    ]
    
    # Common position keywords
    position_keywords = [
        '대표', '이사', '부장', '차장', '과장', '대리', '사원', '주임',
        'CEO', 'CTO', 'CFO', 'COO', 'CMO', 'Director', 'Manager', 
        'Engineer', 'Developer', 'Designer', 'Consultant', 'Representative',
        '팀장', '실장', '본부장', '센터장', '소장', '원장', '회장', '사장',
        'Senior', 'Junior', 'Lead', 'Principal', 'Staff', 'Head'
    ]
    
    # Company keywords (often followed by company name)
    company_indicators = ['(주)', '주식회사', '㈜', 'Inc.', 'Corp.', 'Co.', 'Ltd.', 'LLC', 'Company']
    
    # Extract email
    for line in lines:
        email_match = re.search(email_pattern, line)
        if email_match:
            info.email = email_match.group()
            break
    
    # Extract phone
    for line in lines:
        for pattern in phone_patterns:
            phone_match = re.search(pattern, line)
            if phone_match:
                info.phone = phone_match.group()
                break
        if info.phone:
            break
    
    # Extract position
    for line in lines:
        for keyword in position_keywords:
            if keyword.lower() in line.lower():
                info.position = line.strip()
                break
        if info.position:
            break
    
    # Extract company
    for line in lines:
        for indicator in company_indicators:
            if indicator in line:
                info.company = line.strip()
                break
        if info.company:
            break
    
    # Extract name (heuristic: often the largest text or first non-company line)
    # This is simplified - in production, you might use more sophisticated logic
    for line in lines:
        line = line.strip()
        if line and not info.email and not info.phone:
            # Skip if it's likely company or position
            if not any(indicator in line for indicator in company_indicators):
                if not any(keyword in line.lower() for keyword in position_keywords):
                    if not re.search(email_pattern, line) and not any(re.search(p, line) for p in phone_patterns):
                        # Check if it might be a name
                        if (2 <= len(line) <= 10) or (len(line.split()) >= 2 and len(line.split()) <= 4):
                            info.name = line
                            break
    
    return info

@app.get("/")
async def root():
    return {"message": "Business Card OCR API - Regex Version", "endpoint": "/ocr/business-card"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)