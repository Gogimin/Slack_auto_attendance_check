"""
메인 프로그램
슬랙 출석체크 자동화 - 슬랙 댓글 수집 및 구글 시트 업데이트
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.slack_handler import SlackHandler
from src.sheets_handler import SheetsHandler, AttendanceStatus
from src.parser import AttendanceParser
from src.utils import (
    print_header,
    print_section,
    parse_slack_thread_link,
    column_letter_to_index,
    column_index_to_letter
)
from config.settings import (
    SLACK_BOT_TOKEN,
    SLACK_CHANNEL_ID,
    GOOGLE_SHEETS_CREDENTIALS_PATH,
    SPREADSHEET_ID,
    SHEET_NAME,
    NAME_COLUMN,
    START_ROW,
    BASE_DIR
)


def main():
    """메인 실행 함수"""
    print_header("슬랙 출석체크 자동화")

    # ========================================
    # 1. 환경 설정 확인
    # ========================================
    print_section("1. 환경 설정 확인")

    if not SLACK_BOT_TOKEN:
        print("✗ SLACK_BOT_TOKEN이 설정되지 않았습니다.")
        print("  .env 파일에 슬랙 봇 토큰을 입력하세요.")
        return

    print(f"✓ Slack Bot Token: {'*' * 20}{SLACK_BOT_TOKEN[-10:]}")

    if not SLACK_CHANNEL_ID:
        print("✗ SLACK_CHANNEL_ID가 설정되지 않았습니다.")
        print("  .env 파일에 채널 ID를 입력하세요.")
        return

    print(f"✓ Channel ID: {SLACK_CHANNEL_ID}")

    cred_path = BASE_DIR / GOOGLE_SHEETS_CREDENTIALS_PATH

    if not cred_path.exists():
        print(f"✗ credentials.json 파일을 찾을 수 없습니다.")
        print(f"  경로: {cred_path}")
        return

    print(f"✓ Credentials: {cred_path.name}")

    if not SPREADSHEET_ID:
        print("✗ SPREADSHEET_ID가 설정되지 않았습니다.")
        print("  .env 파일에 스프레드시트 ID를 입력하세요.")
        return

    print(f"✓ Spreadsheet ID: {SPREADSHEET_ID}")

    # ========================================
    # 2. 슬랙 연결
    # ========================================
    print_section("2. 슬랙 API 연결")

    slack_handler = SlackHandler(SLACK_BOT_TOKEN)

    if not slack_handler.test_connection():
        print("\n✗ 슬랙 연결에 실패했습니다.")
        return

    # ========================================
    # 3. 출석체크 스레드 선택
    # ========================================
    print_section("3. 출석체크 스레드 선택")
    print("1. 자동 감지 (최신 '출석 스레드' 메시지 찾기)")
    print("2. 수동 입력 (링크 또는 Thread TS 직접 입력)")
    print()

    choice = input("선택 (1/2): ").strip()

    thread_ts = None
    thread_message = None  # 스레드 메시지 정보 저장

    if choice == '1':
        # 자동 감지
        print("\n[자동 감지 모드]")
        thread_message = slack_handler.find_latest_attendance_thread(SLACK_CHANNEL_ID)

        if not thread_message:
            print("\n최신 출석체크 스레드를 찾을 수 없습니다.")
            print("수동으로 입력하시겠습니까? (y/N): ", end="")
            manual = input().strip().lower()

            if manual != 'y':
                return

            choice = '2'  # 수동 입력으로 전환

        else:
            thread_ts = thread_message['ts']
            print(f"\n이 스레드를 사용하시겠습니까? (Y/n): ", end="")
            confirm = input().strip().lower()

            if confirm == 'n':
                print("\n수동 입력 모드로 전환합니다.")
                choice = '2'
            else:
                print(f"✓ Thread TS: {thread_ts}")

    if choice == '2' or (choice == '1' and not thread_ts):
        # 수동 입력
        print("\n[수동 입력 모드]")
        print("출석체크 스레드 링크 또는 Thread TS를 입력하세요.")
        print("예시:")
        print("  - 링크: https://workspace.slack.com/archives/C1234567890/p1760337471753399")
        print("  - TS: 1760337471.753399")
        print()

        thread_input = input("입력: ").strip()

        if not thread_input:
            print("\n✗ 입력이 없습니다. 프로그램을 종료합니다.")
            return

        # 링크 파싱
        thread_ts = parse_slack_thread_link(thread_input)

        if not thread_ts:
            print(f"\n✗ 올바른 형식이 아닙니다: {thread_input}")
            return

        print(f"✓ Thread TS: {thread_ts}")

    if not thread_ts:
        print("\n✗ Thread TS를 확인할 수 없습니다.")
        return

    # ========================================
    # 4. 슬랙 댓글 수집 및 출석 파싱
    # ========================================
    print_section("4. 슬랙 출석 댓글 수집")

    replies = slack_handler.get_replies_with_user_info(SLACK_CHANNEL_ID, thread_ts)

    if not replies:
        print("\n✗ 댓글을 가져올 수 없습니다.")
        print("  - 스레드 링크/TS가 올바른지 확인하세요.")
        print("  - 봇이 채널에 초대되어 있는지 확인하세요.")
        return

    print(f"\n✓ 댓글 수집 완료: {len(replies)}개")

    # 출석 파싱
    parser = AttendanceParser()
    attendance_list = parser.parse_attendance_replies(replies)

    if not attendance_list:
        print("\n✗ 출석한 학생이 없습니다.")
        print("  댓글 형식을 확인하세요 (예: 이름/출석했습니다)")
        return

    summary = parser.get_attendance_summary(attendance_list)
    print(f"\n✓ 출석 파싱 완료: {summary['total_count']}명")
    print("\n출석자 명단:")
    for name in summary['names']:
        print(f"  ✓ {name}")

    # ========================================
    # 5. 출석체크할 열 입력
    # ========================================
    print_section("5. 출석체크할 열 선택")
    print("오늘 출석체크할 열을 입력하세요 (예: H, K, L)")
    print()

    column_input = input("열 입력: ").strip().upper()

    if not column_input:
        print("\n✗ 입력이 없습니다. 프로그램을 종료합니다.")
        return

    column_index = column_letter_to_index(column_input)

    if column_index is None:
        print(f"\n✗ 올바른 열 형식이 아닙니다: {column_input}")
        print("  A-Z 사이의 문자를 입력하세요.")
        return

    print(f"✓ {column_input}열 선택 (인덱스: {column_index})")

    # ========================================
    # 6. 구글 스프레드시트 연결
    # ========================================
    print_section("6. 구글 스프레드시트 연결")

    sheets_handler = SheetsHandler(
        credentials_path=str(cred_path),
        spreadsheet_id=SPREADSHEET_ID,
        sheet_name=SHEET_NAME
    )

    if not sheets_handler.connect():
        print("\n✗ 구글 시트 연결에 실패했습니다.")
        return

    if not sheets_handler.test_connection():
        print("\n✗ 스프레드시트 접근에 실패했습니다.")
        return

    # ========================================
    # 7. 학생 명단 읽기
    # ========================================
    print_section("7. 학생 명단 읽기")

    students = sheets_handler.get_student_list(NAME_COLUMN, START_ROW)

    if not students:
        print("\n✗ 학생 명단을 읽을 수 없습니다.")
        return

    print(f"✓ 학생 명단: {len(students)}명")

    # ========================================
    # 8. 출석 매칭 및 업데이트
    # ========================================
    print_section("8. 출석 체크 매칭")

    # 출석한 학생과 명단 매칭
    updates = []
    matched_names = []
    unmatched_names = []

    for attendance in attendance_list:
        name = attendance['name']
        if name in students:
            row = students[name]
            updates.append({
                'name': name,
                'row': row,
                'column': column_index,
                'status': AttendanceStatus.PRESENT
            })
            matched_names.append(name)
        else:
            unmatched_names.append(name)

    if unmatched_names:
        print(f"\n⚠ 명단에 없는 이름 ({len(unmatched_names)}명):")
        for name in unmatched_names:
            print(f"  - {name}")

    # 미출석자 찾기
    absent_names = [name for name in students.keys() if name not in matched_names]

    print(f"\n출석 현황:")
    print(f"  ✓ 출석: {len(matched_names)}명")
    print(f"  ✗ 미출석: {len(absent_names)}명")

    # 미출석자 X 표시 여부 확인
    print(f"\n미출석자에게 'X'를 표시하시겠습니까? (y/N): ", end="")
    mark_absent = input().strip().lower()

    if mark_absent == 'y':
        print(f"\n미출석자 ({len(absent_names)}명):")
        for name in absent_names[:10]:  # 최대 10명만 표시
            print(f"  - {name}")
        if len(absent_names) > 10:
            print(f"  ... 외 {len(absent_names) - 10}명")

        # 미출석자 업데이트 정보 추가
        for name in absent_names:
            row = students[name]
            updates.append({
                'name': name,
                'row': row,
                'column': column_index,
                'status': AttendanceStatus.ABSENT
            })

    if not updates:
        print("\n✗ 업데이트할 출석 정보가 없습니다.")
        return

    print(f"\n총 업데이트 대상: {len(updates)}명")
    print(f"  - O (출석): {len(matched_names)}명")
    print(f"  - X (미출석): {len(updates) - len(matched_names)}명")
    print(f"대상 열: {column_input}")

    # 최종 확인
    confirm = input("\n출석 체크를 진행하시겠습니까? (y/N): ").strip().lower()

    if confirm != 'y':
        print("출석 체크를 취소했습니다.")
        return

    # ========================================
    # 9. 배치 업데이트
    # ========================================
    print_section("9. 출석 체크 업데이트")

    # 배치 업데이트
    success_count = sheets_handler.batch_update_attendance(updates)

    # ========================================
    # 10. 알림 전송
    # ========================================
    print_section("10. 알림 전송")

    # 10-1. 스레드에 완료 댓글 작성
    print("\n출석체크 스레드에 완료 댓글을 작성하시겠습니까? (Y/n): ", end="")
    send_thread_reply = input().strip().lower()

    if send_thread_reply != 'n':
        simple_message = "출석 체크를 완료했습니다."
        if slack_handler.post_thread_reply(SLACK_CHANNEL_ID, thread_ts, simple_message):
            print("✓ 스레드 댓글 작성 완료")

    # 10-2. 작성자에게 DM 전송
    if choice == '1' and thread_message:
        # 자동 감지 모드에서만 작성자 정보 사용 가능
        thread_author = thread_message.get('user')

        if thread_author:
            print(f"\n출석체크 스레드 작성자에게 DM을 전송하시겠습니까? (Y/n): ", end="")
            send_dm_choice = input().strip().lower()

            if send_dm_choice != 'n':
                # DM 메시지 작성
                dm_message = f"""[출석체크 완료 알림]

📅 열: {column_input}열
📊 총 인원: {len(students)}명
✅ 출석: {len(matched_names)}명 ({len(matched_names)/len(students)*100:.1f}%)
❌ 미출석: {len(absent_names)}명 ({len(absent_names)/len(students)*100:.1f}%)

📋 출석자: {', '.join(matched_names)}

⚠️ 미출석자 ({len(absent_names)}명):
"""
                # 미출석자 명단 추가 (최대 50명)
                for i, name in enumerate(absent_names[:50], 1):
                    dm_message += f"{i}. {name}\n"

                if len(absent_names) > 50:
                    dm_message += f"... 외 {len(absent_names) - 50}명"

                if slack_handler.send_dm(thread_author, dm_message):
                    print("✓ DM 전송 완료")

    # ========================================
    # 11. 완료
    # ========================================
    print_section("완료")
    print(f"✓ 출석 체크가 완료되었습니다!")
    print(f"  - 성공: {success_count}명")
    print(f"  - 실패: {len(updates) - success_count}명")
    print(f"  - 출석(O): {len(matched_names)}명")
    print(f"  - 미출석(X): {len(updates) - len(matched_names)}명")
    print(f"  - 열: {column_input}")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n프로그램이 중단되었습니다.")
    except Exception as e:
        print(f"\n✗ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
