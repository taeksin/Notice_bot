"""
로깅 유틸리티 모듈

프로젝트 전반에서 사용하는 공통 로거 설정
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

try:
    # Python 3.9+
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None

def now_kst() -> datetime:
    """KST 기준 현재 시간(datetime) 반환. 외부 util 모듈에 의존하지 않음."""
    if ZoneInfo is not None:
        return datetime.now(ZoneInfo("Asia/Seoul"))
    # zoneinfo 가 없으면 로컬 시간을 그대로 사용 (최소 동작 보장)
    return datetime.now()

# UTF-8 출력 설정
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


# ✅ SUCCESS 로그 레벨 정의
SUCCESS_LEVEL_NUM = 25  # INFO(20)와 WARNING(30) 사이
logging.addLevelName(SUCCESS_LEVEL_NUM, "SUCCESS")


class ColoredFormatter(logging.Formatter):
    """컬러 출력과 줄바꿈을 지원하는 로그 포맷터"""

    COLORS = {
        'DEBUG': '\033[36m',    # 파랑
        'INFO': '\033[32m',     # 초록
        'SUCCESS': '\033[32m',  # 초록
        'WARNING': '\033[33m',  # 노랑
        'ERROR': '\033[31m',    # 빨강
        'CRITICAL': '\033[35m', # 보라
        'RESET': '\033[0m',
    }

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        # 로그는 항상 KST 기준으로 표시
        ts = now_kst().strftime('%Y-%m-%d %H:%M:%S')
        return f"{ts} {color}[{record.levelname}]{reset} - {record.getMessage()}"


class Logger:
    """공통 로거 클래스 (Singleton)"""

    _instance = None
    _logger = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._logger is None:
            self._setup_logger()

    def _setup_logger(self):
        self._logger = logging.getLogger('project_logger')
        self._logger.setLevel(logging.INFO)

        # 중복 핸들러 제거
        for h in self._logger.handlers[:]:
            self._logger.removeHandler(h)

        # 콘솔 핸들러
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(ColoredFormatter())
        console_handler.setLevel(logging.DEBUG)
        self._logger.addHandler(console_handler)

        # 파일 핸들러
        self._setup_file_handler()

    def _setup_file_handler(self):
        try:
            log_dir = Path('logs')
            log_dir.mkdir(exist_ok=True)
            # 단일 로그 파일 사용 (일자별 파일 분리 X)
            log_file = log_dir / "app.log"
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            file_handler.setLevel(logging.DEBUG)
            self._logger.addHandler(file_handler)
        except Exception:
            pass

    # ✅ SUCCESS 레벨 메서드
    def success(self, message, *args, **kwargs):
        if self._logger.isEnabledFor(SUCCESS_LEVEL_NUM):
            self._logger._log(SUCCESS_LEVEL_NUM, f"✅ {message}", args, **kwargs)

    # 기본 로깅 메서드들
    def debug(self, msg): self._logger.debug(msg)
    def info(self, msg): self._logger.info(msg)
    def warning(self, msg): self._logger.warning(msg)
    def error(self, msg, exc_info=False): self._logger.error(msg, exc_info=exc_info)
    def critical(self, msg, exc_info=False): self._logger.critical(msg, exc_info=exc_info)

    def progress(self, msg): self._logger.info(f"▶ {msg}")

    # ✅ 구분선 출력 (줄바꿈 없음)
    def newline(self):
        self._logger.info("=" * 50)

    # ✅ 빈 줄 출력 (줄바꿈만)
    def blankline(self):
        # print() 사용 금지: 로거로 빈 줄을 남긴다
        self._logger.info("")

    def set_level(self, level):
        """레벨 문자열로 로깅 수준 변경"""
        levels = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'SUCCESS': SUCCESS_LEVEL_NUM,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL,
        }
        lvl = levels.get(level.upper())
        if lvl:
            self._logger.setLevel(lvl)
            for h in self._logger.handlers:
                h.setLevel(lvl)


# ✅ 싱글톤 인스턴스 생성
logger = Logger()

# 간편 접근용 함수들
def get_logger(): return logger
def set_log_level(level): logger.set_level(level)
def log_debug(msg): logger.debug(msg)
def log_info(msg): logger.info(msg)
def log_success(msg): logger.success(msg)
def log_warning(msg): logger.warning(msg)
def log_error(msg, exc_info=False): logger.error(msg, exc_info=exc_info)
def log_critical(msg, exc_info=False): logger.critical(msg, exc_info=exc_info)
def log_blankline(): logger.blankline()


if __name__ == "__main__":
    test_log = get_logger()
    test_log.debug("디버그 메시지")
    test_log.info("일반 정보 메시지")
    test_log.success("성공 메시지 (초록색으로 표시됨)")
    test_log.warning("경고 메시지")
    test_log.blankline()
    test_log.error("에러 메시지")
    test_log.critical("치명적 오류 발생!")
    test_log.newline()


