"""
Slack API 테스트 스크립트
슬랙 연결 및 스레드 댓글 읽기 테스트
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from src.slack_handler import SlackHandler
from src.parser import AttendanceParser
from src.utils import print_header, print_section, parse_slack_thread_link
from config.settings import SLACK_BOT_TOKEN, SLACK_CHANNEL_ID


def main():
    print_header("슬랙 API 테스트")

    # 1. 설정 확인
    print_section("1. 환경 설정 확인")
    if not SLACK_BOT_TOKEN:
        print("✗ SLACK_BOT_TOKEN이 설정되지 않았습니다.")
        print("  .env 파일에 슬랙 봇 토큰을 입력하세요.")
        return

    print(f"✓ Slack Bot Token: {'*' * 20}{SLACK_BOT_TOKEN[-10:]}")

    if SLACK_CHANNEL_ID:
        print(f"✓ Channel ID: {SLACK_CHANNEL_ID}")
    else:
        print("⚠ Channel ID가 설정되지 않았습니다.")

    # 2. Slack 연결 테스트
    print_section("2. Slack API 연결 테스트")
    handler = SlackHandler(SLACK_BOT_TOKEN)

    if not handler.test_connection():
        print("\n✗ Slack 연결에 실패했습니다. 토큰을 확인하세요.")
        return

    # 3. 출석체크 스레드 링크 입력받기
    print_section("3. 출석체크 스레드 입력")
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
        print("  슬랙 링크 또는 Thread TS 형식을 확인하세요.")
        return

    print(f"\n✓ Thread TS 파싱 완료: {thread_ts}")

    # 4. 스레드 댓글 가져오기
    if SLACK_CHANNEL_ID and thread_ts:
        print_section("4. 스레드 댓글 가져오기")
        replies = handler.get_replies_with_user_info(SLACK_CHANNEL_ID, thread_ts)

        if replies:
            print(f"\n✓ 댓글 {len(replies)}개를 가져왔습니다.")

            # 5. 출석 파싱 테스트
            print_section("5. 출석 파싱 테스트")
            parser = AttendanceParser()
            attendance_list = parser.parse_attendance_replies(replies)

            # 6. 결과 출력
            print_section("6. 출석 결과")
            if attendance_list:
                summary = parser.get_attendance_summary(attendance_list)
                print(f"\n총 출석: {summary['total_count']}명\n")

                print("출석자 명단:")
                for name in summary['names']:
                    print(f"  ✓ {name}")

                print(f"\n추출 방법:")
                print(f"  - 텍스트 패턴: {summary['by_source']['text_pattern']}명")
                print(f"  - 슬랙 이름: {summary['by_source']['slack_name']}명")
            else:
                print("출석자가 없습니다.")

            print_section("테스트 완료")
            print("✓ 슬랙 API가 정상적으로 작동합니다!")
            print("✓ 다음 단계: Phase 3 (구글 스프레드시트 연동)")
        else:
            print("\n⚠ 댓글을 가져올 수 없습니다.")
            print("  - 채널 ID와 스레드 TS를 확인하세요.")
            print("  - 봇이 해당 채널에 초대되어 있는지 확인하세요.")
    else:
        print("\n✗ 채널 ID가 설정되지 않았습니다.")
        print("  .env 파일에 SLACK_CHANNEL_ID를 입력하세요.")


if __name__ == '__main__':
    main()
