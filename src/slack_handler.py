"""
Slack API 처리 모듈
출석체크 스레드의 댓글을 수집하고 사용자 정보를 가져옵니다.
"""
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from typing import List, Dict, Optional
import time


class SlackHandler:
    """Slack API를 처리하는 클래스"""

    def __init__(self, token: str):
        """
        SlackHandler 초기화

        Args:
            token (str): Slack Bot Token (xoxb-로 시작)
        """
        self.client = WebClient(token=token)
        self.user_cache = {}  # 사용자 정보 캐시

    def test_connection(self) -> bool:
        """
        Slack API 연결 테스트

        Returns:
            bool: 연결 성공 여부
        """
        try:
            response = self.client.auth_test()
            print(f"✓ Slack 연결 성공!")
            print(f"  - Bot 이름: {response['user']}")
            print(f"  - 팀: {response['team']}")
            return True
        except SlackApiError as e:
            print(f"✗ Slack 연결 실패: {e.response['error']}")
            return False

    def get_thread_replies(self, channel_id: str, thread_ts: str) -> List[Dict]:
        """
        특정 스레드의 모든 댓글 가져오기

        Args:
            channel_id (str): 채널 ID
            thread_ts (str): 스레드 타임스탬프

        Returns:
            List[Dict]: 댓글 리스트 (원본 메시지 제외)
        """
        try:
            print(f"\n[Slack] 스레드 댓글 수집 중...")
            print(f"  - Channel: {channel_id}")
            print(f"  - Thread TS: {thread_ts}")

            response = self.client.conversations_replies(
                channel=channel_id,
                ts=thread_ts,
                limit=1000  # 최대 1000개
            )

            if not response['ok']:
                raise SlackApiError("API 호출 실패", response)

            messages = response['messages']

            # 첫 번째 메시지는 원본 메시지이므로 제외
            replies = messages[1:] if len(messages) > 1 else []

            print(f"✓ 댓글 수집 완료: {len(replies)}개")

            return replies

        except SlackApiError as e:
            print(f"✗ 댓글 가져오기 실패: {e.response['error']}")
            return []

    def get_user_info(self, user_id: str) -> Optional[Dict]:
        """
        사용자 ID로 사용자 정보 가져오기 (캐시 사용)

        Args:
            user_id (str): Slack User ID

        Returns:
            Optional[Dict]: 사용자 정보 (이름, 실명 등)
        """
        # 캐시에 있으면 반환
        if user_id in self.user_cache:
            return self.user_cache[user_id]

        try:
            response = self.client.users_info(user=user_id)

            if not response['ok']:
                return None

            user = response['user']
            user_info = {
                'id': user_id,
                'name': user.get('name', ''),
                'real_name': user.get('real_name', ''),
                'display_name': user.get('profile', {}).get('display_name', ''),
            }

            # 캐시에 저장
            self.user_cache[user_id] = user_info

            # API Rate Limiting 방지
            time.sleep(0.1)

            return user_info

        except SlackApiError as e:
            print(f"✗ 사용자 정보 가져오기 실패 ({user_id}): {e.response['error']}")
            return None

    def get_replies_with_user_info(self, channel_id: str, thread_ts: str) -> List[Dict]:
        """
        스레드 댓글과 사용자 정보를 함께 가져오기

        Args:
            channel_id (str): 채널 ID
            thread_ts (str): 스레드 타임스탬프

        Returns:
            List[Dict]: 댓글 + 사용자 정보 리스트
        """
        replies = self.get_thread_replies(channel_id, thread_ts)

        if not replies:
            return []

        print(f"\n[Slack] 사용자 정보 수집 중...")

        enriched_replies = []

        for reply in replies:
            user_id = reply.get('user')
            text = reply.get('text', '')
            ts = reply.get('ts', '')

            # Bot 메시지 제외
            if reply.get('bot_id'):
                continue

            user_info = None
            if user_id:
                user_info = self.get_user_info(user_id)

            enriched_replies.append({
                'user_id': user_id,
                'user_info': user_info,
                'text': text,
                'timestamp': ts,
            })

        print(f"✓ 사용자 정보 수집 완료: {len(enriched_replies)}개")

        return enriched_replies


# 테스트 코드
if __name__ == '__main__':
    from config.settings import SLACK_BOT_TOKEN, SLACK_CHANNEL_ID, SLACK_THREAD_TS

    if not SLACK_BOT_TOKEN:
        print("✗ SLACK_BOT_TOKEN이 설정되지 않았습니다.")
        print("  .env 파일을 생성하고 토큰을 입력하세요.")
    else:
        handler = SlackHandler(SLACK_BOT_TOKEN)

        # 연결 테스트
        if handler.test_connection():
            print("\n슬랙 API 연결이 정상적으로 작동합니다!")

            # 스레드 댓글 가져오기 테스트 (SLACK_THREAD_TS가 설정된 경우)
            if SLACK_CHANNEL_ID and SLACK_THREAD_TS:
                replies = handler.get_replies_with_user_info(SLACK_CHANNEL_ID, SLACK_THREAD_TS)
                print(f"\n가져온 댓글 샘플 (최대 3개):")
                for i, reply in enumerate(replies[:3], 1):
                    user_info = reply['user_info']
                    name = user_info.get('real_name', '알 수 없음') if user_info else '알 수 없음'
                    print(f"  {i}. {name}: {reply['text'][:50]}...")
