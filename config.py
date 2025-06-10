from enum import Enum
from pathlib import Path
from datetime import datetime, timedelta
import os

class Environment(Enum):
    DEV = "dev"
    PRODUCTION = "production"

class RotationPeriod(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

class Config:
    def __init__(self, env: Environment = Environment.DEV, rotation_period: RotationPeriod = None):
        self.env = env
        self.base_dir = Path(__file__).parent
        
        # 환경별 기본 로테이션 설정
        if rotation_period is None:
            self.rotation_period = RotationPeriod.WEEKLY if env == Environment.DEV else RotationPeriod.DAILY
        else:
            self.rotation_period = rotation_period
        
        # 디렉토리 설정
        self.LOG_DIR = self.base_dir / "logs"
        self.RESPONSE_DIR = self.base_dir / "responses"
        
        # 보관 정책
        self.KEEP_LOG_DAYS = 30 if env == Environment.DEV else 7
        self.KEEP_RESPONSE_DAYS = 30 if env == Environment.DEV else 7
        
        # 로깅 설정
        self.LOG_LEVEL = "DEBUG" if env == Environment.DEV else "INFO"
        self.LOG_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        
        # 디렉토리 생성
        self.LOG_DIR.mkdir(exist_ok=True)
        self.RESPONSE_DIR.mkdir(exist_ok=True)
        (self.LOG_DIR / "archive").mkdir(exist_ok=True)
        (self.RESPONSE_DIR / "archive").mkdir(exist_ok=True)

# Singleton pattern for configuration
_config = None

def get_config() -> Config:
    global _config
    if _config is None:
        env_str = os.getenv("ENVIRONMENT", "dev")
        env = Environment.DEV if env_str == "dev" else Environment.PRODUCTION
        _config = Config(env=env)
    return _config

def set_config(env: str = None, rotation: str = None) -> Config:
    global _config
    env_enum = Environment(env) if env else Environment.DEV
    rotation_enum = RotationPeriod(rotation) if rotation else None
    _config = Config(env=env_enum, rotation_period=rotation_enum)
    return _config