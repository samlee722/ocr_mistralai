from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from mistralai import Mistral
import base64
import os
import json
import time
import traceback
import argparse
from typing import Optional
from dotenv import load_dotenv
from contextlib import asynccontextmanager

# 로깅 시스템 임포트
from config import set_config, get_config
from logger import get_logger
from file_rotator import get_file_rotator

load_dotenv()

# 커맨드라인 인자 파싱
parser = argparse.ArgumentParser()
parser.add_argument("--env", choices=["dev", "production"], default="dev")
parser.add_argument("--rotation", choices=["daily", "weekly", "monthly"])
parser.add_argument("--port", type=int, default=8000)

# FastAPI 실행 시 uvicorn이 인자를 추가로 전달할 수 있으므로 처리
args, unknown = parser.parse_known_args()

# 설정 초기화
config = set_config(env=args.env, rotation=args.rotation)
app_logger = get_logger()
file_rotator = get_file_rotator()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시
    file_rotator.start()
    print(f"Started with {config.env.value} environment, {config.rotation_period.value} rotation")
    yield
    # 종료 시
    file_rotator.stop()

app = FastAPI(title="Business Card OCR API", lifespan=lifespan)

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
async def extract_business_card(request: Request, file: UploadFile = File(...)):
    # 요청 ID 생성
    request_id = app_logger.generate_request_id()
    start_time = time.time()
    
    try:
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Only image files are supported")
        
        # Read file content
        content = await file.read()
        file_size_mb = len(content) / (1024 * 1024)
        
        # 요청 로깅
        app_logger.log_api_request(
            request_id=request_id,
            endpoint="/ocr/business-card",
            method="POST",
            client_ip=request.client.host if request.client else "unknown",
            file_name=file.filename,
            file_size_mb=round(file_size_mb, 2),
            content_type=file.content_type
        )
        
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
        
        # 처리 시간 계산
        processing_time = (time.time() - start_time) * 1000  # ms
        
        # 응답 데이터 저장
        response_data = {
            "request_id": request_id,
            "timestamp": time.time(),
            "file_name": file.filename,
            "ocr_text": ocr_text,
            "extracted_data": business_card_info.dict(),
            "processing_time_ms": round(processing_time, 2)
        }
        response_file_path = app_logger.save_response_file(request_id, response_data)
        
        # 응답 로깅
        app_logger.log_app_response(
            request_id=request_id,
            response_status="success",
            response_file=str(response_file_path.name),
            processing_time_ms=round(processing_time, 2),
            extracted_fields=len([v for v in business_card_info.dict().values() if v])
        )
        
        return business_card_info
        
    except json.JSONDecodeError as e:
        app_logger.log_error(
            request_id=request_id,
            error_type="JSONDecodeError",
            error_message=str(e),
            traceback=traceback.format_exc()
        )
        raise HTTPException(status_code=500, detail=f"Failed to parse AI response: {str(e)}")
    except Exception as e:
        app_logger.log_error(
            request_id=request_id,
            error_type=type(e).__name__,
            error_message=str(e),
            traceback=traceback.format_exc()
        )
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Business Card OCR API", "endpoint": "/ocr/business-card"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=args.port)