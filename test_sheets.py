"""
Google Sheets API 테스트 스크립트
스프레드시트 연결 및 학생 명단 읽기 테스트
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from src.sheets_handler import SheetsHandler, AttendanceStatus
from src.utils import print_header, print_section
from config.settings import (
    GOOGLE_SHEETS_CREDENTIALS_PATH,
    SPREADSHEET_ID,
    SHEET_NAME,
    NAME_COLUMN,
    SLACK_COLUMN,
    START_ROW,
    BASE_DIR
)


def main():
    print_header("Google Sheets API 테스트")

    # 1. 설정 확인
    print_section("1. 환경 설정 확인")

    cred_path = BASE_DIR / GOOGLE_SHEETS_CREDENTIALS_PATH

    if not cred_path.exists():
        print(f"✗ credentials.json 파일을 찾을 수 없습니다.")
        print(f"  경로: {cred_path}")
        print("\n필요한 작업:")
        print("  1. Google Cloud Console (https://console.cloud.google.com/) 접속")
        print("  2. 프로젝트 생성 및 Google Sheets API 활성화")
        print("  3. 서비스 계정 생성 및 JSON 키 다운로드")
        print("  4. 다운로드한 파일을 config/credentials.json으로 저장")
        print("  5. 스프레드시트를 서비스 계정 이메일과 공유 (편집자 권한)")
        return

    print(f"✓ Credentials 파일: {cred_path}")

    if not SPREADSHEET_ID:
        print("✗ SPREADSHEET_ID가 설정되지 않았습니다.")
        print("  .env 파일에 스프레드시트 ID를 입력하세요.")
        print("  (URL의 /d/ 뒤 부분)")
        return

    print(f"✓ Spreadsheet ID: {SPREADSHEET_ID}")
    print(f"✓ Sheet Name: {SHEET_NAME}")
    print(f"✓ Name Column: {chr(65 + NAME_COLUMN)}열 (index: {NAME_COLUMN})")
    print(f"✓ Slack Column: {chr(65 + SLACK_COLUMN)}열 (index: {SLACK_COLUMN})")
    print(f"✓ Start Row: {START_ROW + 1}행 (index: {START_ROW})")

    # 2. Google Sheets API 연결
    print_section("2. Google Sheets API 연결")

    handler = SheetsHandler(
        credentials_path=str(cred_path),
        spreadsheet_id=SPREADSHEET_ID,
        sheet_name=SHEET_NAME
    )

    if not handler.connect():
        print("\n✗ Google Sheets API 연결에 실패했습니다.")
        return

    # 3. 스프레드시트 접근 테스트
    print_section("3. 스프레드시트 접근 테스트")

    if not handler.test_connection():
        print("\n✗ 스프레드시트 접근에 실패했습니다.")
        print("  다음 사항을 확인하세요:")
        print("  - 스프레드시트 ID가 올바른지")
        print("  - 서비스 계정과 스프레드시트를 공유했는지")
        print("  - 시트 이름이 올바른지")
        return

    # 4. 학생 명단 읽기
    print_section("4. 학생 명단 읽기")

    students = handler.get_student_list(NAME_COLUMN, START_ROW)

    if not students:
        print("\n✗ 학생 명단을 읽을 수 없습니다.")
        print(f"  {chr(65 + NAME_COLUMN)}{START_ROW + 1} 셀부터 학생 이름이 있는지 확인하세요.")
        return

    print(f"\n학생 명단 (총 {len(students)}명):")
    for i, (name, row) in enumerate(list(students.items())[:10], 1):
        print(f"  {i}. {name} (행: {row + 1})")

    if len(students) > 10:
        print(f"  ... 외 {len(students) - 10}명")

    # 5. 테스트 완료
    print_section("테스트 완료")
    print("✓ Google Sheets API가 정상적으로 작동합니다!")
    print("✓ 다음 단계: Phase 4 (메인 로직 통합)")

    # 6. 업데이트 테스트 여부 확인
    print_section("출석 업데이트 테스트 (선택)")
    print("⚠ 주의: 실제 스프레드시트를 수정합니다!")
    print()
    test_update = input("출석 업데이트 테스트를 진행하시겠습니까? (y/N): ").strip().lower()

    if test_update == 'y':
        print("\n출석 상태 선택:")
        print("  1. O - 출석")
        print("  2. X - 미출석")
        print("  3. △ - 지각")
        status_choice = input("선택 (1/2/3): ").strip()

        status_map = {
            '1': AttendanceStatus.PRESENT,
            '2': AttendanceStatus.ABSENT,
            '3': AttendanceStatus.LATE
        }

        status = status_map.get(status_choice, AttendanceStatus.PRESENT)

        print(f"\n테스트: 첫 번째 학생의 출석 체크 ({status.value})")
        first_student = list(students.items())[0]
        name, row = first_student

        print(f"  학생: {name}")
        print(f"  행: {row + 1}")
        print(f"  열: {chr(65 + SLACK_COLUMN)}")
        print(f"  상태: {status.value}")

        if handler.update_attendance(row, SLACK_COLUMN, status):
            print(f"\n✓ 출석 체크 업데이트 성공!")
            print(f"  {name}의 {chr(65 + SLACK_COLUMN)}{row + 1} 셀이 '{status.value}'로 업데이트되었습니다.")
        else:
            print("\n✗ 출석 체크 업데이트 실패")
    else:
        print("테스트를 건너뜁니다.")


if __name__ == '__main__':
    main()
