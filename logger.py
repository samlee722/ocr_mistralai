import json
import uuid
from datetime import datetime
from pathlib import Path
from loguru import logger
from config import get_config

class ApplicationLogger:
    def __init__(self):
        self.config = get_config()
        self._setup_loggers()
    
    def _setup_loggers(self):
        """로그 타입별 파일 분리"""
        logger.remove()  # 기본 로거 제거
        
        # 콘솔 로거
        logger.add(
            sink=lambda msg: print(msg),
            format=self.config.LOG_FORMAT,
            level=self.config.LOG_LEVEL
        )
        
        # 파일별 로거 설정
        self._add_file_logger("api_requests.log", "api_request")
        self._add_file_logger("app_responses.log", "app_response")
        self._add_file_logger("errors.log", "error")
    
    def _add_file_logger(self, filename: str, log_type: str):
        """특정 로그 타입을 위한 파일 로거 추가"""
        period_dir = self._get_period_directory()
        log_path = period_dir / filename
        
        logger.add(
            sink=log_path,
            format=self.config.LOG_FORMAT,
            level=self.config.LOG_LEVEL,
            filter=lambda record: record.get("extra", {}).get("log_type") == log_type,
            rotation=None,  # 우리가 직접 로테이션 관리
            retention=None  # 우리가 직접 보관 관리
        )
    
    def _get_period_directory(self) -> Path:
        """현재 로테이션 주기에 맞는 디렉토리 반환"""
        now = datetime.now()
        
        if self.config.rotation_period.value == "daily":
            period_name = now.strftime("%Y-%m-%d")
        elif self.config.rotation_period.value == "weekly":
            period_name = now.strftime("%Y-W%U")
        else:  # monthly
            period_name = now.strftime("%Y-%m")
        
        period_dir = self.config.LOG_DIR / period_name
        period_dir.mkdir(exist_ok=True)
        return period_dir
    
    def generate_request_id(self) -> str:
        """고유한 요청 ID 생성"""
        return str(uuid.uuid4())
    
    def log_api_request(self, request_id: str, endpoint: str, **kwargs):
        """API 요청 로깅"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id,
            "endpoint": endpoint,
            **kwargs
        }
        logger.bind(log_type="api_request").info(json.dumps(log_data, ensure_ascii=False))
    
    def log_app_response(self, request_id: str, response_status: str, **kwargs):
        """애플리케이션 응답 로깅"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id,
            "response_status": response_status,
            **kwargs
        }
        logger.bind(log_type="app_response").info(json.dumps(log_data, ensure_ascii=False))
    
    def log_error(self, request_id: str, error_type: str, error_message: str, **kwargs):
        """에러 로깅"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id,
            "error_type": error_type,
            "error_message": error_message,
            **kwargs
        }
        logger.bind(log_type="error").error(json.dumps(log_data, ensure_ascii=False))
    
    def save_response_file(self, request_id: str, content: dict) -> Path:
        """응답 데이터를 파일로 저장"""
        period_dir = self._get_response_directory()
        filename = f"response_{request_id}.json"
        filepath = period_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(content, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    def _get_response_directory(self) -> Path:
        """현재 로테이션 주기에 맞는 응답 디렉토리 반환"""
        now = datetime.now()
        
        if self.config.rotation_period.value == "daily":
            period_name = now.strftime("%Y-%m-%d")
        elif self.config.rotation_period.value == "weekly":
            period_name = now.strftime("%Y-W%U")
        else:  # monthly
            period_name = now.strftime("%Y-%m")
        
        period_dir = self.config.RESPONSE_DIR / period_name
        period_dir.mkdir(exist_ok=True)
        return period_dir

# Singleton pattern for logger
_logger = None

def get_logger() -> ApplicationLogger:
    global _logger
    if _logger is None:
        _logger = ApplicationLogger()
    return _logger