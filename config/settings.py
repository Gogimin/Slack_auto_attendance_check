"""
환경변수 및 설정 관리 모듈
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트 경로
BASE_DIR = Path(__file__).resolve().parent.parent

# src 모듈을 import할 수 있도록 경로 추가
sys.path.insert(0, str(BASE_DIR))

# .env 파일 로드
load_dotenv(BASE_DIR / '.env')

# utils에서 링크 파싱 함수 import
from src.utils import parse_slack_thread_link

# Slack 설정
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
SLACK_CHANNEL_ID = os.getenv('SLACK_CHANNEL_ID')

# # Thread TS: 링크 또는 TS 형식 모두 지원
# _raw_thread_ts = os.getenv('SLACK_THREAD_TS')
# SLACK_THREAD_TS = parse_slack_thread_link(_raw_thread_ts) if _raw_thread_ts else None

# Google Sheets 설정
GOOGLE_SHEETS_CREDENTIALS_PATH = os.getenv('GOOGLE_SHEETS_CREDENTIALS_PATH', 'config/credentials.json')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
SHEET_NAME = os.getenv('SHEET_NAME', '출석현황')

# 열 설정 (0-based index)
NAME_COLUMN = int(os.getenv('NAME_COLUMN', 1))  # B열
SLACK_COLUMN = int(os.getenv('SLACK_COLUMN', 10))  # K열

# 시작 행 (0-based index)
START_ROW = int(os.getenv('START_ROW', 4))  # 5번째 행

# 로그 설정
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / 'attendance.log'


def validate_settings():
    """필수 환경변수 검증"""
    required = {
        'SLACK_BOT_TOKEN': SLACK_BOT_TOKEN,
        'SLACK_CHANNEL_ID': SLACK_CHANNEL_ID,
        'SLACK_THREAD_TS': SLACK_THREAD_TS,
        'SPREADSHEET_ID': SPREADSHEET_ID,
    }

    missing = [key for key, value in required.items() if not value]

    if missing:
        raise ValueError(f"다음 환경변수가 설정되지 않았습니다: {', '.join(missing)}")

    # credentials 파일 확인
    cred_path = BASE_DIR / GOOGLE_SHEETS_CREDENTIALS_PATH
    if not cred_path.exists():
        raise FileNotFoundError(f"Google 서비스 계정 키 파일을 찾을 수 없습니다: {cred_path}")

    return True


if __name__ == '__main__':
    # 설정 테스트
    try:
        validate_settings()
        print("✓ 모든 설정이 올바르게 구성되었습니다.")
        print(f"\n현재 설정:")
        print(f"  - Slack Channel: {SLACK_CHANNEL_ID}")
        print(f"  - Thread TS (원본): {_raw_thread_ts}")
        print(f"  - Thread TS (파싱됨): {SLACK_THREAD_TS}")
        print(f"  - Spreadsheet ID: {SPREADSHEET_ID}")
        print(f"  - Sheet Name: {SHEET_NAME}")
    except Exception as e:
        print(f"✗ 설정 오류: {e}")
