# Business Card OCR API

FastAPI server that extracts business card information using Mistral OCR.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file:
```bash
cp .env.example .env
```

3. Add your Mistral API key to `.env`

4. Run the server:
```bash
uvicorn main:app --reload
```

## API Endpoints

- `POST /ocr/business-card`: Upload business card image to extract information
- `GET /`: API info
- `GET /health`: Health check

## Response Format

```json
{
  "company": "Company Name",
  "position": "Job Title",
  "name": "Person Name",
  "phone": "Phone Number",
  "email": "email@example.com"
}
```