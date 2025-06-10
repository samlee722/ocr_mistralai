# 명함 OCR API

Mistral OCR을 사용하여 명함 정보를 추출하는 FastAPI 서버 (프로덕션 레벨 로깅 및 파일 로테이션 시스템 포함)

## command

- python main.py (개발 환경, 주간 로테이션)
- python main.py --env production (운영 환경, 일간 로테이션)
- python main.py --env dev --rotation monthly (월간 로테이션)

## 주요 기능

- Mistral AI를 사용한 명함 OCR
- 회사명, 직책, 이름, 전화번호, 이메일을 포함한 구조화된 JSON 응답
- 자동 로테이션 기능이 있는 프로덕션 레벨 로깅 시스템
- 고유 ID를 통한 요청 추적
- 감사 추적을 위한 응답 파일 저장
- 환경별 설정 (개발/운영)

## 설치 방법

1. 의존성 설치:

```bash
pip install -r requirements.txt
```

2. `.env` 파일 생성:

```bash
cp .env.example .env
```

3. `.env` 파일에 Mistral API 키 추가

4. 서버 실행:

### 개발 환경 (기본값)

```bash
# 기본: 개발 환경, 주간 로테이션
python main.py

# 커스텀 로테이션 주기
python main.py --env dev --rotation monthly
```

### 운영 환경

```bash
# 운영 환경, 일간 로테이션
python main.py --env production

# 커스텀 포트
python main.py --env production --port 8080
```

## API 엔드포인트

### POST /ocr/business-card

명함 이미지를 업로드하여 정보 추출

**요청 형식:**

- Method: `POST`
- Content-Type: `multipart/form-data`
- Body:
  - `file`: 이미지 파일 (지원 형식: JPEG, PNG, GIF, BMP, WEBP)

**요청 예시 (cURL):**

```bash
curl -X POST "http://localhost:8000/ocr/business-card" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@business_card.jpg"
```

**요청 예시 (Python):**

```python
import requests

url = "http://localhost:8000/ocr/business-card"
files = {"file": open("business_card.jpg", "rb")}
response = requests.post(url, files=files)
print(response.json())
```

**응답 형식:**

```json
{
  "company": "주식회사 코리아",
  "position": "대표이사",
  "name": "김철수",
  "phone": "010-1234-5678",
  "email": "kim@korea.com"
}
```

**응답 필드 설명:**

- `company`: 회사명 (없을 경우 null)
- `position`: 직책/직위 (없을 경우 null)
- `name`: 이름 (없을 경우 null)
- `phone`: 전화번호 (없을 경우 null)
- `email`: 이메일 주소 (없을 경우 null)

### GET /

API 기본 정보 확인

**응답:**

```json
{
  "message": "Business Card OCR API",
  "endpoint": "/ocr/business-card"
}
```

### GET /health

서버 상태 확인

**응답:**

```json
{
  "status": "healthy"
}
```

## 로깅 시스템

### 로그 구조

```
logs/
├── 2025-W23/              # 주간 로테이션 (개발 환경 기본값)
│   ├── api_requests.log   # API 요청 로그
│   ├── app_responses.log  # 애플리케이션 응답 로그
│   └── errors.log         # 에러 로그
└── archive/               # 압축된 과거 로그

responses/
├── 2025-W23/              # 응답 데이터 파일
│   └── response_<request_id>.json
└── archive/               # 압축된 과거 응답
```

### 로그 형식

**API 요청 로그:**

```json
{
  "timestamp": "2025-06-05T14:30:00",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "endpoint": "/ocr/business-card",
  "method": "POST",
  "client_ip": "192.168.1.100",
  "file_name": "business_card.jpg",
  "file_size_mb": 2.5,
  "content_type": "image/jpeg"
}
```

**응답 로그:**

```json
{
  "timestamp": "2025-06-05T14:30:05",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "response_status": "success",
  "response_file": "response_550e8400-e29b-41d4-a716-446655440000.json",
  "processing_time_ms": 1234.56,
  "extracted_fields": 5
}
```

### 환경별 설정

| 설정           | 개발 환경          | 운영 환경        |
| -------------- | ------------------ | ---------------- |
| 로테이션 주기  | 주간 (매주 월요일) | 일간 (매일 자정) |
| 로그 보관 기간 | 30일               | 7일              |
| 응답 파일 보관 | 30일               | 7일              |
| 로그 레벨      | DEBUG              | INFO             |

## 에러 처리

**400 Bad Request:**

```json
{
  "detail": "Only image files are supported"
}
```

**500 Internal Server Error:**

```json
{
  "detail": "Error processing image: [에러 메시지]"
}
```
