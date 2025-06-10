from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import zipfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from config import get_config
from loguru import logger

class FileRotator:
    def __init__(self):
        self.config = get_config()
        self.scheduler = BackgroundScheduler()
        self._setup_rotation_schedule()
    
    def _setup_rotation_schedule(self):
        """로테이션 스케줄 설정"""
        if self.config.rotation_period.value == "daily":
            trigger = CronTrigger(hour=0, minute=0)  # 매일 자정
        elif self.config.rotation_period.value == "weekly":
            trigger = CronTrigger(day_of_week=0, hour=0, minute=0)  # 매주 월요일 자정
        else:  # monthly
            trigger = CronTrigger(day=1, hour=0, minute=0)  # 매월 1일 자정
        
        self.scheduler.add_job(
            func=self.rotate_all,
            trigger=trigger,
            id="file_rotation"
        )
    
    def start(self):
        """스케줄러 시작"""
        self.scheduler.start()
        logger.info(f"File rotation scheduler started with {self.config.rotation_period.value} rotation")
    
    def stop(self):
        """스케줄러 종료"""
        self.scheduler.shutdown()
        logger.info("File rotation scheduler stopped")
    
    def rotate_all(self):
        """모든 파일 로테이션 실행"""
        logger.info("Starting file rotation...")
        self._rotate_directory(self.config.LOG_DIR, self.config.KEEP_LOG_DAYS)
        self._rotate_directory(self.config.RESPONSE_DIR, self.config.KEEP_RESPONSE_DAYS)
        logger.info("File rotation completed")
    
    def _rotate_directory(self, base_dir: Path, keep_days: int):
        """디렉토리 로테이션 처리"""
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        archive_dir = base_dir / "archive"
        
        for item in base_dir.iterdir():
            if item.is_dir() and item.name != "archive":
                # 디렉토리 생성 시간 확인
                if self._is_directory_old(item, cutoff_date):
                    self._archive_directory(item, archive_dir)
    
    def _is_directory_old(self, directory: Path, cutoff_date: datetime) -> bool:
        """디렉토리가 보관 기한을 넘었는지 확인"""
        # 디렉토리 이름에서 날짜 파싱
        dir_name = directory.name
        
        try:
            if "-W" in dir_name:  # Weekly format (YYYY-WXX)
                year, week = dir_name.split("-W")
                dir_date = datetime.strptime(f"{year}-W{week}-1", "%Y-W%U-%w")
            elif len(dir_name.split("-")) == 3:  # Daily format (YYYY-MM-DD)
                dir_date = datetime.strptime(dir_name, "%Y-%m-%d")
            elif len(dir_name.split("-")) == 2:  # Monthly format (YYYY-MM)
                dir_date = datetime.strptime(dir_name, "%Y-%m")
            else:
                return False
            
            return dir_date < cutoff_date
        except ValueError:
            # 날짜 파싱 실패 시 수정 시간으로 확인
            stat = directory.stat()
            mtime = datetime.fromtimestamp(stat.st_mtime)
            return mtime < cutoff_date
    
    def _archive_directory(self, source_dir: Path, archive_dir: Path):
        """디렉토리를 ZIP으로 아카이브"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"{source_dir.name}_{timestamp}.zip"
        zip_path = archive_dir / zip_filename
        
        logger.info(f"Archiving {source_dir} to {zip_path}")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in source_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(source_dir.parent)
                    zipf.write(file_path, arcname)
        
        # 원본 디렉토리 삭제
        shutil.rmtree(source_dir)
        logger.info(f"Archived and removed {source_dir}")
    
    def manual_cleanup(self, force: bool = False):
        """수동으로 정리 실행"""
        if force:
            logger.warning("Force cleanup initiated - archiving all directories")
            # 강제 정리: 모든 디렉토리 아카이브
            self._rotate_directory(self.config.LOG_DIR, 0)
            self._rotate_directory(self.config.RESPONSE_DIR, 0)
        else:
            # 일반 정리: 정책에 따른 정리
            self.rotate_all()

# Singleton pattern for file rotator
_file_rotator = None

def get_file_rotator() -> FileRotator:
    global _file_rotator
    if _file_rotator is None:
        _file_rotator = FileRotator()
    return _file_rotator