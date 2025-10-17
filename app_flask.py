"""
슬랙 출석체크 자동화 - Flask 웹 애플리케이션
더블클릭으로 실행 가능한 독립 실행형 프로그램
"""
import sys
import webbrowser
import threading
from pathlib import Path
from flask import Flask, render_template, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import pytz

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from src.workspace_manager import WorkspaceManager
from src.slack_handler import SlackHandler
from src.sheets_handler import SheetsHandler, AttendanceStatus
from src.parser import AttendanceParser
from src.utils import parse_slack_thread_link, column_letter_to_index, get_next_column, column_index_to_letter

# Flask 앱 초기화
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # 한글 지원

# 워크스페이스 매니저 초기화
workspace_manager = WorkspaceManager()

# 스케줄러 초기화 (한국 시간대)
scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Seoul'))
KST = pytz.timezone('Asia/Seoul')


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


@app.route('/api/workspaces/add', methods=['POST'])
def add_workspace():
    """새 워크스페이스 추가"""
    import os
    import json

    try:
        data = request.json

        # 필수 필드 확인
        required_fields = ['workspace_name', 'display_name', 'slack_bot_token',
                          'slack_channel_id', 'spreadsheet_id', 'credentials_json']

        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'{field} 필드가 필요합니다.'
                }), 400

        workspace_name = data['workspace_name'].strip()
        display_name = data['display_name'].strip()
        slack_bot_token = data['slack_bot_token'].strip()
        slack_channel_id = data['slack_channel_id'].strip()
        spreadsheet_id = data['spreadsheet_id'].strip()
        sheet_name = data.get('sheet_name', 'Sheet1').strip()
        name_column = data.get('name_column', 'B').strip()
        start_row = int(data.get('start_row', 2))
        credentials_json = data['credentials_json']

        # 워크스페이스 폴더 경로
        workspace_folder = Path(__file__).parent / 'workspaces' / workspace_name

        # 폴더가 이미 존재하는지 확인
        if workspace_folder.exists():
            return jsonify({
                'success': False,
                'error': f'{workspace_name} 워크스페이스가 이미 존재합니다.'
            }), 400

        # 폴더 생성
        workspace_folder.mkdir(parents=True, exist_ok=True)

        # config.json 생성
        config = {
            "name": display_name,
            "slack_bot_token": slack_bot_token,
            "slack_channel_id": slack_channel_id,
            "spreadsheet_id": spreadsheet_id,
            "sheet_name": sheet_name,
            "name_column": name_column if name_column.isalpha() else 1,
            "start_row": start_row,
            "notification_user_id": "",
            "auto_schedule": {
                "enabled": False,
                "create_thread_day": "",
                "create_thread_time": "",
                "create_thread_message": "",
                "check_attendance_day": "",
                "check_attendance_time": "",
                "check_attendance_column": "K",
                "auto_column_enabled": False,
                "start_column": "H",
                "end_column": "O"
            }
        }

        config_path = workspace_folder / 'config.json'
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        # credentials.json 생성
        credentials_path = workspace_folder / 'credentials.json'

        # credentials_json이 문자열이면 JSON 파싱, 딕셔너리면 그대로 사용
        if isinstance(credentials_json, str):
            credentials_data = json.loads(credentials_json)
        else:
            credentials_data = credentials_json

        with open(credentials_path, 'w', encoding='utf-8') as f:
            json.dump(credentials_data, f, ensure_ascii=False, indent=2)

        # 워크스페이스 매니저 리로드
        workspace_manager.reload()

        return jsonify({
            'success': True,
            'message': f'{display_name} 워크스페이스가 추가되었습니다.',
            'workspace_name': workspace_name
        })

    except json.JSONDecodeError as e:
        return jsonify({
            'success': False,
            'error': f'JSON 형식이 올바르지 않습니다: {str(e)}'
        }), 400
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
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


@app.route('/api/schedule/<workspace_name>', methods=['GET'])
def get_schedule(workspace_name):
    """워크스페이스 스케줄 조회"""
    try:
        workspace = workspace_manager.get_workspace(workspace_name)
        if not workspace:
            return jsonify({
                'success': False,
                'error': '워크스페이스를 찾을 수 없습니다.'
            }), 404

        return jsonify({
            'success': True,
            'schedule': workspace.auto_schedule or {},
            'notification_user_id': workspace.notification_user_id or ''
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/schedules/all', methods=['GET'])
def get_all_schedules():
    """모든 워크스페이스의 예약 현황 조회"""
    try:
        workspaces = workspace_manager.get_all_workspaces()
        schedules = []

        for workspace in workspaces:
            schedule = workspace.auto_schedule

            if schedule and schedule.get('enabled'):
                schedules.append({
                    'workspace_name': workspace.display_name,
                    'folder_name': workspace.name,
                    'create_thread_day': schedule.get('create_thread_day', ''),
                    'create_thread_time': schedule.get('create_thread_time', ''),
                    'check_attendance_day': schedule.get('check_attendance_day', ''),
                    'check_attendance_time': schedule.get('check_attendance_time', ''),
                    'check_attendance_column': schedule.get('check_attendance_column', ''),
                    'notification_user_id': workspace.notification_user_id or ''
                })

        return jsonify({
            'success': True,
            'schedules': schedules,
            'total': len(schedules)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/schedule', methods=['POST'])
def save_schedule():
    """스케줄 저장"""
    try:
        data = request.json
        workspace_name = data.get('workspace')
        schedule = data.get('schedule')
        notification_user_id = data.get('notification_user_id', '')

        workspace = workspace_manager.get_workspace(workspace_name)
        if not workspace:
            return jsonify({
                'success': False,
                'error': '워크스페이스를 찾을 수 없습니다.'
            }), 404

        # 스케줄 저장
        if not workspace.save_schedule(schedule):
            return jsonify({
                'success': False,
                'error': '스케줄 저장에 실패했습니다.'
            }), 500

        # notification_user_id 저장
        workspace._config['notification_user_id'] = notification_user_id
        import json
        with open(workspace.config_file, 'w', encoding='utf-8') as f:
            json.dump(workspace._config, f, ensure_ascii=False, indent=2)

        # 스케줄러 재시작
        restart_scheduler()

        return jsonify({
            'success': True,
            'message': '스케줄이 저장되었습니다.'
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


# === 스케줄러 관련 함수 ===

def create_attendance_thread_job(workspace):
    """출석 스레드 자동 생성 작업"""
    try:
        print(f"\n[자동실행] 출석 스레드 생성 시작 - {workspace.display_name}")
        print(f"시간: {datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')}")

        schedule = workspace.auto_schedule
        if not schedule or not schedule.get('enabled'):
            return

        slack_handler = SlackHandler(workspace.slack_bot_token)
        message = schedule.get('create_thread_message', '📢 출석 스레드\n\n오늘 출석 체크합니다!')

        # 메시지 전송
        result = slack_handler.post_message(workspace.slack_channel_id, message)

        if result:
            print(f"✓ 출석 스레드 생성 완료: {result['ts']}")
        else:
            print(f"✗ 출석 스레드 생성 실패")

    except Exception as e:
        print(f"✗ 출석 스레드 생성 오류: {e}")
        import traceback
        traceback.print_exc()


def check_attendance_job(workspace):
    """출석 집계 자동 실행 작업"""
    try:
        print(f"\n[자동실행] 출석 집계 시작 - {workspace.display_name}")
        print(f"시간: {datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')}")

        schedule = workspace.auto_schedule
        if not schedule or not schedule.get('enabled'):
            return

        # 1. 슬랙 연결
        slack_handler = SlackHandler(workspace.slack_bot_token)

        # 2. 최신 출석 스레드 찾기
        thread_message = slack_handler.find_latest_attendance_thread(workspace.slack_channel_id)
        if not thread_message:
            print("✗ 출석 스레드를 찾을 수 없습니다.")
            return

        thread_ts = thread_message['ts']
        thread_user = thread_message.get('user')

        print(f"✓ 출석 스레드 발견: {thread_ts}")

        # 3. 댓글 수집
        replies = slack_handler.get_replies_with_user_info(workspace.slack_channel_id, thread_ts)
        if not replies:
            print("✗ 댓글을 가져올 수 없습니다.")
            return

        # 4. 출석 파싱
        parser = AttendanceParser()
        attendance_list = parser.parse_attendance_replies(replies)

        if not attendance_list:
            print("✗ 출석한 학생이 없습니다.")
            return

        print(f"✓ 출석자 수: {len(attendance_list)}명")

        # 5. 구글 시트 연결
        sheets_handler = SheetsHandler(
            credentials_path=workspace.credentials_path,
            spreadsheet_id=workspace.spreadsheet_id,
            sheet_name=workspace.sheet_name
        )

        if not sheets_handler.connect() or not sheets_handler.test_connection():
            print("✗ 구글 시트 연결 실패")
            return

        # 6. 학생 명단 읽기
        students = sheets_handler.get_student_list(workspace.name_column, workspace.start_row)
        if not students:
            print("✗ 학생 명단을 읽을 수 없습니다.")
            return

        # 7. 출석 매칭
        # 자동 열 증가 모드 확인
        auto_column_enabled = schedule.get('auto_column_enabled', False)
        start_column = schedule.get('start_column', 'H')
        end_column = schedule.get('end_column', 'O')
        current_column = schedule.get('check_attendance_column', 'K')

        # 자동 열 증가가 활성화되어 있으면 다음 열로 이동
        if auto_column_enabled and start_column and end_column:
            # 현재 열 사용
            column_input = current_column
            column_index = column_letter_to_index(column_input)

            print(f"📍 자동 열 증가 모드: {start_column} ~ {end_column}")
            print(f"   현재 열: {current_column}")

            # 끝 열에 도달했는지 확인
            if current_column == end_column:
                print(f"🎯 끝 열({end_column})에 도달했습니다. 스케줄을 비활성화합니다.")

                # 스케줄 비활성화
                schedule['enabled'] = False
                workspace.save_schedule(schedule)

                # 스케줄러에서 제거
                try:
                    scheduler.remove_job(f'create_thread_{workspace.name}')
                    scheduler.remove_job(f'check_attendance_{workspace.name}')
                    print(f"✓ 스케줄러에서 작업 제거 완료")
                except Exception as e:
                    print(f"⚠️ 스케줄러 작업 제거 중 오류 (무시 가능): {e}")

                # 관리자에게 완료 알림 전송
                notification_user = workspace.notification_user_id or thread_user
                if notification_user:
                    completion_message = f"""🎉 [출석체크 완료 알림]

📊 **전체 출석체크가 완료되었습니다!**

✅ 시작 열: {start_column}
✅ 끝 열: {end_column}
✅ 마지막 실행 열: {current_column}

자동 스케줄이 비활성화되었습니다.
다시 시작하려면 웹 UI에서 스케줄을 재설정해주세요.

워크스페이스: {workspace.display_name}
"""
                    slack_handler.send_dm(notification_user, completion_message)
                    print(f"✓ 완료 알림 DM 전송 완료")

                column_index = column_letter_to_index(column_input)
            else:
                # 다음 실행을 위해 열 증가
                next_column = get_next_column(current_column, start_column, end_column)
                print(f"   다음 열: {next_column}")

                # config 업데이트
                schedule['check_attendance_column'] = next_column
                workspace.save_schedule(schedule)
                column_index = column_letter_to_index(column_input)
        else:
            # 수동 모드: 지정된 열 사용
            column_input = current_column
            column_index = column_letter_to_index(column_input)

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

        # 8. 미출석자 처리
        absent_names = [name for name in students.keys() if name not in matched_names]

        for name in absent_names:
            row = students[name]
            updates.append({
                'name': name,
                'row': row,
                'column': column_index,
                'status': AttendanceStatus.ABSENT
            })

        # 9. 업데이트
        success_count = sheets_handler.batch_update_attendance(updates)
        print(f"✓ 구글 시트 업데이트 완료: {success_count}개")

        # 10. 알림 전송
        notification_user = workspace.notification_user_id or thread_user

        # 스레드 댓글
        slack_handler.post_thread_reply(
            workspace.slack_channel_id,
            thread_ts,
            f"[자동] 출석 체크를 완료했습니다.\n출석: {len(matched_names)}명 / 미출석: {len(absent_names)}명"
        )

        # DM 전송
        if notification_user:
            dm_message = f"""[자동 출석체크 완료 알림]

📅 열: {column_input}열
📊 총 인원: {len(students)}명
✅ 출석: {len(matched_names)}명 ({len(matched_names)/len(students)*100:.1f}%)
❌ 미출석: {len(absent_names)}명

📋 출석자: {', '.join(matched_names)}

⚠️ 미출석자 ({len(absent_names)}명):
"""
            for i, name in enumerate(absent_names[:50], 1):
                dm_message += f"{i}. {name}\n"

            if len(absent_names) > 50:
                dm_message += f"... 외 {len(absent_names) - 50}명"

            slack_handler.send_dm(notification_user, dm_message)

        print(f"✓ 출석 집계 완료!")

    except Exception as e:
        print(f"✗ 출석 집계 오류: {e}")
        import traceback
        traceback.print_exc()


def setup_scheduler():
    """스케줄러 설정"""
    workspaces = workspace_manager.get_all_workspaces()

    for workspace in workspaces:
        schedule = workspace.auto_schedule

        if not schedule or not schedule.get('enabled'):
            continue

        print(f"\n📅 스케줄 등록: {workspace.display_name}")

        # 출석 스레드 생성 스케줄
        create_day = schedule.get('create_thread_day')
        create_time = schedule.get('create_thread_time')

        if create_day and create_time:
            hour, minute = create_time.split(':')
            scheduler.add_job(
                func=lambda ws=workspace: create_attendance_thread_job(ws),
                trigger=CronTrigger(day_of_week=create_day, hour=int(hour), minute=int(minute)),
                id=f'create_thread_{workspace.name}',
                replace_existing=True
            )
            print(f"  ✓ 출석 스레드 생성: 매주 {create_day} {create_time}")

        # 출석 집계 스케줄
        check_day = schedule.get('check_attendance_day')
        check_time = schedule.get('check_attendance_time')

        if check_day and check_time:
            hour, minute = check_time.split(':')
            scheduler.add_job(
                func=lambda ws=workspace: check_attendance_job(ws),
                trigger=CronTrigger(day_of_week=check_day, hour=int(hour), minute=int(minute)),
                id=f'check_attendance_{workspace.name}',
                replace_existing=True
            )
            print(f"  ✓ 출석 집계: 매주 {check_day} {check_time}")


def restart_scheduler():
    """스케줄러 재시작"""
    try:
        scheduler.remove_all_jobs()
        setup_scheduler()
        print("\n✓ 스케줄러가 재시작되었습니다.")
    except Exception as e:
        print(f"✗ 스케줄러 재시작 오류: {e}")


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
        print("스케줄러 초기화 중...")
        print("=" * 50)

        # 스케줄러 시작
        setup_scheduler()
        scheduler.start()
        print("\n✓ 스케줄러 시작 완료 (한국 시간대: Asia/Seoul)")

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
        print("\n\n서버 종료 중...")
        scheduler.shutdown()
        print("✓ 스케줄러 종료 완료")
        print("✓ 서버가 종료되었습니다.")
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
