"""
슬랙 출석체크 자동화 - Flask 웹 애플리케이션
더블클릭으로 실행 가능한 독립 실행형 프로그램
"""
import sys
import webbrowser
import threading
from pathlib import Path
from flask import Flask, render_template, jsonify, request

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from src.workspace_manager import WorkspaceManager
from src.slack_handler import SlackHandler
from src.sheets_handler import SheetsHandler, AttendanceStatus
from src.parser import AttendanceParser
from src.utils import parse_slack_thread_link, column_letter_to_index

# Flask 앱 초기화
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # 한글 지원

# 워크스페이스 매니저 초기화
workspace_manager = WorkspaceManager()


@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')


@app.route('/api/workspaces', methods=['GET'])
def get_workspaces():
    """모든 워크스페이스 목록 반환"""
    try:
        workspaces = workspace_manager.get_all_workspaces()

        workspace_list = []
        for ws in workspaces:
            workspace_list.append({
                'name': ws.display_name,
                'folder_name': ws.name,
                'channel_id': ws.slack_channel_id,
                'spreadsheet_id': ws.spreadsheet_id,
                'sheet_name': ws.sheet_name
            })

        return jsonify({
            'success': True,
            'workspaces': workspace_list
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/find-thread', methods=['POST'])
def find_thread():
    """최신 출석 스레드 자동 감지"""
    try:
        data = request.json
        workspace_name = data.get('workspace')

        workspace = workspace_manager.get_workspace(workspace_name)
        if not workspace:
            return jsonify({
                'success': False,
                'error': '워크스페이스를 찾을 수 없습니다.'
            }), 404

        slack_handler = SlackHandler(workspace.slack_bot_token)

        if not slack_handler.test_connection():
            return jsonify({
                'success': False,
                'error': '슬랙 연결에 실패했습니다.'
            }), 500

        thread_message = slack_handler.find_latest_attendance_thread(
            workspace.slack_channel_id
        )

        if not thread_message:
            return jsonify({
                'success': False,
                'error': '최신 출석 스레드를 찾을 수 없습니다.'
            }), 404

        return jsonify({
            'success': True,
            'thread_ts': thread_message['ts'],
            'thread_text': thread_message['text'][:100] + '...',
            'thread_user': thread_message.get('user', 'unknown')
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/run-attendance', methods=['POST'])
def run_attendance():
    """출석체크 실행"""
    try:
        data = request.json
        workspace_name = data.get('workspace')
        thread_input = data.get('thread_ts')
        column_input = data.get('column', 'K').strip().upper()
        mark_absent = data.get('mark_absent', True)
        send_thread_reply = data.get('send_thread_reply', True)
        send_dm = data.get('send_dm', True)
        thread_user = data.get('thread_user')  # 자동 감지 시 사용

        # 1. 워크스페이스 로드
        workspace = workspace_manager.get_workspace(workspace_name)
        if not workspace:
            return jsonify({
                'success': False,
                'error': '워크스페이스를 찾을 수 없습니다.'
            }), 404

        # 2. Thread TS 파싱
        thread_ts = parse_slack_thread_link(thread_input)
        if not thread_ts:
            return jsonify({
                'success': False,
                'error': '올바른 Thread TS 형식이 아닙니다.'
            }), 400

        # 3. 열 변환
        column_index = column_letter_to_index(column_input)
        if column_index is None:
            return jsonify({
                'success': False,
                'error': '올바른 열 형식이 아닙니다.'
            }), 400

        # 4. 슬랙 연결
        slack_handler = SlackHandler(workspace.slack_bot_token)
        if not slack_handler.test_connection():
            return jsonify({
                'success': False,
                'error': '슬랙 연결에 실패했습니다.'
            }), 500

        # 5. 댓글 수집
        replies = slack_handler.get_replies_with_user_info(
            workspace.slack_channel_id,
            thread_ts
        )

        if not replies:
            return jsonify({
                'success': False,
                'error': '댓글을 가져올 수 없습니다.'
            }), 500

        # 6. 출석 파싱
        parser = AttendanceParser()
        attendance_list = parser.parse_attendance_replies(replies)

        if not attendance_list:
            return jsonify({
                'success': False,
                'error': '출석한 학생이 없습니다.'
            }), 400

        summary = parser.get_attendance_summary(attendance_list)

        # 7. 구글 시트 연결
        sheets_handler = SheetsHandler(
            credentials_path=workspace.credentials_path,
            spreadsheet_id=workspace.spreadsheet_id,
            sheet_name=workspace.sheet_name
        )

        if not sheets_handler.connect() or not sheets_handler.test_connection():
            return jsonify({
                'success': False,
                'error': '구글 시트 연결에 실패했습니다.'
            }), 500

        # 8. 학생 명단 읽기
        students = sheets_handler.get_student_list(
            workspace.name_column,
            workspace.start_row
        )

        if not students:
            return jsonify({
                'success': False,
                'error': '학생 명단을 읽을 수 없습니다.'
            }), 500

        # 9. 출석 매칭
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

        # 10. 미출석자 처리
        absent_names = [name for name in students.keys() if name not in matched_names]

        if mark_absent:
            for name in absent_names:
                row = students[name]
                updates.append({
                    'name': name,
                    'row': row,
                    'column': column_index,
                    'status': AttendanceStatus.ABSENT
                })

        # 11. 업데이트
        success_count = sheets_handler.batch_update_attendance(updates)

        # 12. 알림 전송
        notifications = []

        if send_thread_reply:
            if slack_handler.post_thread_reply(
                workspace.slack_channel_id,
                thread_ts,
                "출석 체크를 완료했습니다."
            ):
                notifications.append('스레드 댓글 작성 완료')

        if send_dm and thread_user:
            dm_message = f"""[출석체크 완료 알림]

📅 열: {column_input}열
📊 총 인원: {len(students)}명
✅ 출석: {len(matched_names)}명 ({len(matched_names)/len(students)*100:.1f}%)
❌ 미출석: {len(absent_names)}명 ({len(absent_names)/len(students)*100:.1f}%)

📋 출석자: {', '.join(matched_names)}

⚠️ 미출석자 ({len(absent_names)}명):
"""
            for i, name in enumerate(absent_names[:50], 1):
                dm_message += f"{i}. {name}\n"

            if len(absent_names) > 50:
                dm_message += f"... 외 {len(absent_names) - 50}명"

            if slack_handler.send_dm(thread_user, dm_message):
                notifications.append('DM 전송 완료')

        # 13. 결과 반환
        return jsonify({
            'success': True,
            'result': {
                'total_students': len(students),
                'present': len(matched_names),
                'absent': len(absent_names),
                'matched_names': matched_names,
                'absent_names': absent_names[:20],  # 최대 20명만
                'unmatched_names': unmatched_names,
                'success_count': success_count,
                'column': column_input,
                'notifications': notifications
            }
        })

    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


def open_browser():
    """브라우저 자동 열기"""
    webbrowser.open('http://127.0.0.1:5000')


if __name__ == '__main__':
    try:
        # 경로 확인
        print("=" * 50)
        print("슬랙 출석체크 관리 시스템 v2.0")
        print("=" * 50)
        print(f"현재 작업 디렉토리: {Path.cwd()}")
        print(f"실행 파일 위치: {Path(__file__).parent}")

        # 필수 폴더 확인
        required_folders = ['templates', 'static', 'src', 'workspaces']
        missing_folders = []

        for folder in required_folders:
            folder_path = Path(__file__).parent / folder
            if not folder_path.exists():
                missing_folders.append(folder)
                print(f"⚠️  {folder}/ 폴더를 찾을 수 없습니다: {folder_path}")

        if missing_folders:
            print()
            print("=" * 50)
            print("❌ 오류: 필수 폴더가 없습니다!")
            print("=" * 50)
            print("누락된 폴더:", ", ".join(missing_folders))
            print()
            print("해결 방법:")
            print("1. 개발 모드: 프로젝트 루트에서 실행하세요")
            print("   python app_flask.py")
            print()
            print("2. EXE 모드: dist/슬랙출석체크/ 폴더 전체를 복사하세요")
            print("=" * 50)
            input("\n아무 키나 누르면 종료됩니다...")
            sys.exit(1)

        print()
        print("✓ 모든 폴더 확인 완료")
        print()

        # 워크스페이스 확인
        workspaces = workspace_manager.get_all_workspaces()
        if not workspaces:
            print("⚠️  워크스페이스가 없습니다.")
            print("   workspaces/ 폴더에 워크스페이스를 추가하세요.")
        else:
            print(f"✓ {len(workspaces)}개의 워크스페이스를 찾았습니다")

        print()
        print("=" * 50)
        print("서버 시작 중...")
        print("=" * 50)
        print("URL: http://127.0.0.1:5000")
        print("종료하려면 Ctrl+C를 누르세요.")
        print("=" * 50)
        print()

        # 1초 후 브라우저 자동 열기
        threading.Timer(1.5, open_browser).start()

        # Flask 앱 실행
        app.run(host='127.0.0.1', port=5000, debug=False)

    except KeyboardInterrupt:
        print("\n\n서버가 종료되었습니다.")
        sys.exit(0)
    except Exception as e:
        print()
        print("=" * 50)
        print("❌ 오류 발생!")
        print("=" * 50)
        print(f"오류 내용: {e}")
        print()
        import traceback
        print("상세 오류:")
        traceback.print_exc()
        print("=" * 50)
        input("\n아무 키나 누르면 종료됩니다...")
        sys.exit(1)
