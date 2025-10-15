// 전역 변수
let currentWorkspace = null;
let threadTS = null;
let threadUser = null;

// DOM 로드 완료 시
document.addEventListener('DOMContentLoaded', function() {
    loadWorkspaces();
    setupEventListeners();
    loadAllSchedules(); // 예약 현황 로드
});

// 이벤트 리스너 설정
function setupEventListeners() {
    // 워크스페이스 선택
    document.getElementById('workspace-select').addEventListener('change', onWorkspaceChange);

    // 스레드 모드 전환
    document.querySelectorAll('input[name="thread-mode"]').forEach(radio => {
        radio.addEventListener('change', onThreadModeChange);
    });

    // 스레드 찾기 버튼
    document.getElementById('find-thread-btn').addEventListener('click', findThread);

    // 수동 입력
    document.getElementById('thread-input').addEventListener('input', onManualInput);

    // 실행 버튼
    document.getElementById('run-btn').addEventListener('click', runAttendance);

    // 스케줄 활성화 토글
    document.getElementById('auto-schedule-enabled').addEventListener('change', toggleScheduleSettings);

    // 스케줄 저장 버튼
    document.getElementById('save-schedule-btn').addEventListener('click', saveSchedule);

    // 예약 현황 새로고침 버튼
    document.getElementById('refresh-schedule-btn').addEventListener('click', loadAllSchedules);
}

// 워크스페이스 목록 로드
async function loadWorkspaces() {
    try {
        const response = await fetch('/api/workspaces');
        const data = await response.json();

        if (data.success) {
            const select = document.getElementById('workspace-select');
            select.innerHTML = '<option value="">워크스페이스를 선택하세요...</option>';

            data.workspaces.forEach(ws => {
                const option = document.createElement('option');
                option.value = ws.folder_name;
                option.textContent = ws.name;
                option.dataset.channelId = ws.channel_id;
                option.dataset.sheetName = ws.sheet_name;
                select.appendChild(option);
            });

            if (data.workspaces.length === 0) {
                showError('워크스페이스가 없습니다. workspaces/ 폴더에 워크스페이스를 추가하세요.');
            }
        } else {
            showError('워크스페이스 로드 실패: ' + data.error);
        }
    } catch (error) {
        showError('워크스페이스 로드 오류: ' + error.message);
    }
}

// 워크스페이스 변경
function onWorkspaceChange(e) {
    const select = e.target;
    const selectedOption = select.options[select.selectedIndex];

    if (selectedOption.value) {
        currentWorkspace = selectedOption.value;

        // 워크스페이스 정보 표시
        const infoBox = document.getElementById('workspace-info');
        document.getElementById('channel-id').textContent = selectedOption.dataset.channelId;
        document.getElementById('sheet-name').textContent = selectedOption.dataset.sheetName;
        infoBox.style.display = 'block';

        // 스레드 정보 초기화
        resetThreadInfo();

        // 스케줄 폼 초기화 (기존 값 불러오지 않음)
        resetScheduleForm();
    } else {
        currentWorkspace = null;
        document.getElementById('workspace-info').style.display = 'none';
    }
}

// 스레드 모드 전환
function onThreadModeChange(e) {
    const mode = e.target.value;

    if (mode === 'auto') {
        document.getElementById('auto-detect-section').style.display = 'block';
        document.getElementById('manual-input-section').style.display = 'none';
    } else {
        document.getElementById('auto-detect-section').style.display = 'none';
        document.getElementById('manual-input-section').style.display = 'block';
    }

    resetThreadInfo();
}

// 스레드 찾기
async function findThread() {
    if (!currentWorkspace) {
        showError('워크스페이스를 먼저 선택하세요.');
        return;
    }

    const btn = document.getElementById('find-thread-btn');
    btn.disabled = true;
    btn.innerHTML = '<span class="loading"></span> 검색 중...';

    try {
        const response = await fetch('/api/find-thread', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({workspace: currentWorkspace})
        });

        const data = await response.json();

        if (data.success) {
            threadTS = data.thread_ts;
            threadUser = data.thread_user;

            document.getElementById('thread-ts').value = threadTS;
            document.getElementById('thread-user').value = threadUser;
            document.getElementById('thread-text').textContent = data.thread_text;
            document.getElementById('thread-ts-display').textContent = 'Thread TS: ' + threadTS;
            document.getElementById('thread-found').style.display = 'block';

            hideError();
        } else {
            showError('스레드 찾기 실패: ' + data.error);
        }
    } catch (error) {
        showError('스레드 찾기 오류: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '🔍 최신 출석 스레드 찾기';
    }
}

// 수동 입력
function onManualInput(e) {
    const input = e.target.value.trim();
    if (input) {
        threadTS = input;
        document.getElementById('thread-ts').value = input;
        threadUser = null; // 수동 입력 시 DM 불가
        hideError();
    }
}

// 출석체크 실행
async function runAttendance() {
    // 유효성 검사
    if (!currentWorkspace) {
        showError('워크스페이스를 선택하세요.');
        return;
    }

    const threadInput = document.getElementById('thread-ts').value;
    if (!threadInput) {
        showError('스레드를 선택하거나 입력하세요.');
        return;
    }

    const column = document.getElementById('column-input').value.trim().toUpperCase();
    if (!column) {
        showError('열을 입력하세요.');
        return;
    }

    // 진행 상황 표시
    showProgress();
    hideError();
    hideResult();

    // 설정 수집
    const settings = {
        workspace: currentWorkspace,
        thread_ts: threadInput,
        column: column,
        mark_absent: document.getElementById('mark-absent').checked,
        send_thread_reply: document.getElementById('send-thread-reply').checked,
        send_dm: document.getElementById('send-dm').checked,
        thread_user: document.getElementById('thread-user').value
    };

    // 실행 버튼 비활성화
    const runBtn = document.getElementById('run-btn');
    runBtn.disabled = true;

    try {
        // 진행 단계 시뮬레이션
        updateProgress(10, '슬랙 연결 중...');
        await sleep(500);

        updateProgress(25, '댓글 수집 중...');
        const response = await fetch('/api/run-attendance', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(settings)
        });

        updateProgress(50, '출석 파싱 중...');
        await sleep(500);

        updateProgress(70, '구글 시트 업데이트 중...');
        const data = await response.json();

        updateProgress(90, '알림 전송 중...');
        await sleep(500);

        if (data.success) {
            updateProgress(100, '완료!');
            await sleep(300);
            showResult(data.result);
        } else {
            showError('출석체크 실패: ' + data.error);
            if (data.traceback) {
                console.error(data.traceback);
            }
        }
    } catch (error) {
        showError('출석체크 오류: ' + error.message);
    } finally {
        runBtn.disabled = false;
        hideProgress();
    }
}

// 진행 상황 표시
function showProgress() {
    document.getElementById('progress-section').style.display = 'block';
    updateProgress(0, '준비 중...');
}

function updateProgress(percent, text) {
    document.getElementById('progress-fill').style.width = percent + '%';
    document.getElementById('progress-text').textContent = text;
}

function hideProgress() {
    setTimeout(() => {
        document.getElementById('progress-section').style.display = 'none';
    }, 1000);
}

// 결과 표시
function showResult(result) {
    const section = document.getElementById('result-section');

    // 통계
    document.getElementById('stat-total').textContent = result.total_students;
    document.getElementById('stat-present').textContent = result.present;
    document.getElementById('stat-absent').textContent = result.absent;
    document.getElementById('stat-rate').textContent =
        (result.present / result.total_students * 100).toFixed(1) + '%';

    // 출석자 명단
    const presentList = document.getElementById('present-list');
    presentList.innerHTML = result.matched_names.join(', ');

    // 미출석자 명단
    const absentList = document.getElementById('absent-list');
    if (result.absent_names.length > 0) {
        absentList.innerHTML = result.absent_names.join(', ');
        if (result.absent > result.absent_names.length) {
            absentList.innerHTML += ` ... 외 ${result.absent - result.absent_names.length}명`;
        }
    } else {
        absentList.innerHTML = '<em>전원 출석!</em>';
    }

    // 명단에 없는 이름
    if (result.unmatched_names && result.unmatched_names.length > 0) {
        const unmatchedSection = document.getElementById('unmatched-section');
        const unmatchedList = document.getElementById('unmatched-list');
        unmatchedList.innerHTML = result.unmatched_names.join(', ');
        unmatchedSection.style.display = 'block';
    } else {
        document.getElementById('unmatched-section').style.display = 'none';
    }

    // 알림
    if (result.notifications && result.notifications.length > 0) {
        const notificationsSection = document.getElementById('notifications-section');
        const notificationsList = document.getElementById('notifications-list');
        notificationsList.innerHTML = '';
        result.notifications.forEach(notif => {
            const li = document.createElement('li');
            li.textContent = notif;
            notificationsList.appendChild(li);
        });
        notificationsSection.style.display = 'block';
    } else {
        document.getElementById('notifications-section').style.display = 'none';
    }

    section.style.display = 'block';
    section.scrollIntoView({behavior: 'smooth'});
}

function hideResult() {
    document.getElementById('result-section').style.display = 'none';
}

// 오류 표시
function showError(message) {
    const section = document.getElementById('error-section');
    document.getElementById('error-message').textContent = message;
    section.style.display = 'block';
    section.scrollIntoView({behavior: 'smooth'});
}

function hideError() {
    document.getElementById('error-section').style.display = 'none';
}

// 스레드 정보 초기화
function resetThreadInfo() {
    threadTS = null;
    threadUser = null;
    document.getElementById('thread-ts').value = '';
    document.getElementById('thread-user').value = '';
    document.getElementById('thread-found').style.display = 'none';
    document.getElementById('thread-input').value = '';
}

// 스케줄 폼 초기화 (기본값으로 리셋)
function resetScheduleForm() {
    // 자동 실행 비활성화
    document.getElementById('auto-schedule-enabled').checked = false;
    document.getElementById('schedule-settings').style.display = 'none';

    // 출석 스레드 생성 초기화
    document.getElementById('create-thread-day').value = '';
    document.getElementById('create-thread-time').value = '';
    document.getElementById('thread-message').value = '📢 출석 스레드입니다.\n\n"이름/출석했습니다" 형식으로 댓글 달아주세요!';

    // 출석 집계 초기화
    document.getElementById('check-attendance-day').value = '';
    document.getElementById('check-attendance-time').value = '';
    document.getElementById('check-attendance-column').value = 'K';

    // 알림 수신자 초기화
    document.getElementById('notification-user-id').value = '';
}

// 스케줄 활성화 토글
function toggleScheduleSettings(e) {
    const settings = document.getElementById('schedule-settings');
    if (e.target.checked) {
        settings.style.display = 'block';
    } else {
        settings.style.display = 'none';
    }
}

// 스케줄 정보 로드
async function loadSchedule() {
    if (!currentWorkspace) return;

    try {
        const response = await fetch(`/api/schedule/${currentWorkspace}`);
        const data = await response.json();

        if (data.success && data.schedule) {
            const schedule = data.schedule;

            // 활성화 상태
            document.getElementById('auto-schedule-enabled').checked = schedule.enabled || false;
            document.getElementById('schedule-settings').style.display = schedule.enabled ? 'block' : 'none';

            // 출석 스레드 생성
            document.getElementById('create-thread-day').value = schedule.create_thread_day || '';
            document.getElementById('create-thread-time').value = schedule.create_thread_time || '';
            document.getElementById('thread-message').value = schedule.create_thread_message || '';

            // 출석 집계
            document.getElementById('check-attendance-day').value = schedule.check_attendance_day || '';
            document.getElementById('check-attendance-time').value = schedule.check_attendance_time || '';
            document.getElementById('check-attendance-column').value = schedule.check_attendance_column || 'K';

            // 알림 수신자
            document.getElementById('notification-user-id').value = data.notification_user_id || '';
        }
    } catch (error) {
        console.error('스케줄 로드 오류:', error);
    }
}

// 스케줄 저장
async function saveSchedule() {
    if (!currentWorkspace) {
        showError('워크스페이스를 먼저 선택하세요.');
        return;
    }

    const schedule = {
        enabled: document.getElementById('auto-schedule-enabled').checked,
        create_thread_day: document.getElementById('create-thread-day').value,
        create_thread_time: document.getElementById('create-thread-time').value,
        create_thread_message: document.getElementById('thread-message').value,
        check_attendance_day: document.getElementById('check-attendance-day').value,
        check_attendance_time: document.getElementById('check-attendance-time').value,
        check_attendance_column: document.getElementById('check-attendance-column').value
    };

    const notificationUserId = document.getElementById('notification-user-id').value.trim();

    const btn = document.getElementById('save-schedule-btn');
    btn.disabled = true;
    btn.innerHTML = '<span class="loading"></span> 저장 중...';

    try {
        const response = await fetch('/api/schedule', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                workspace: currentWorkspace,
                schedule: schedule,
                notification_user_id: notificationUserId
            })
        });

        const data = await response.json();

        if (data.success) {
            alert('✓ 스케줄이 저장되었습니다!\n\n서버를 재시작하면 자동 실행이 활성화됩니다.');
            hideError();
            // 예약 현황 새로고침
            loadAllSchedules();
        } else {
            showError('스케줄 저장 실패: ' + data.error);
        }
    } catch (error) {
        showError('스케줄 저장 오류: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '💾 스케줄 저장';
    }
}

// 예약 현황 로드
async function loadAllSchedules() {
    try {
        const response = await fetch('/api/schedules/all');
        const data = await response.json();

        const section = document.getElementById('schedule-status-section');
        const content = document.getElementById('schedule-status-content');

        if (data.success && data.schedules && data.schedules.length > 0) {
            // 예약이 있으면 표시
            section.style.display = 'block';

            const dayNames = {
                'mon': '월요일',
                'tue': '화요일',
                'wed': '수요일',
                'thu': '목요일',
                'fri': '금요일',
                'sat': '토요일',
                'sun': '일요일'
            };

            let html = '<table class="schedule-table">';
            html += '<thead><tr>';
            html += '<th>워크스페이스</th>';
            html += '<th>출석 스레드 생성</th>';
            html += '<th>출석 집계</th>';
            html += '<th>출석 열</th>';
            html += '<th>관리</th>';
            html += '</tr></thead>';
            html += '<tbody>';

            data.schedules.forEach(schedule => {
                html += '<tr>';
                html += `<td><strong>${schedule.workspace_name}</strong></td>`;

                // 출석 스레드 생성
                if (schedule.create_thread_day && schedule.create_thread_time) {
                    const day = dayNames[schedule.create_thread_day] || schedule.create_thread_day;
                    html += `<td>매주 ${day} ${schedule.create_thread_time}</td>`;
                } else {
                    html += '<td><span style="color: #999;">미설정</span></td>';
                }

                // 출석 집계
                if (schedule.check_attendance_day && schedule.check_attendance_time) {
                    const day = dayNames[schedule.check_attendance_day] || schedule.check_attendance_day;
                    html += `<td>매주 ${day} ${schedule.check_attendance_time}</td>`;
                } else {
                    html += '<td><span style="color: #999;">미설정</span></td>';
                }

                // 출석 열
                html += `<td><strong>${schedule.check_attendance_column || 'K'}</strong></td>`;

                // 관리 버튼
                html += '<td>';
                html += `<button class="btn-small btn-primary" onclick="editSchedule('${schedule.folder_name}')">✏️ 수정</button> `;
                html += `<button class="btn-small btn-danger" onclick="deleteSchedule('${schedule.folder_name}', '${schedule.workspace_name}')">🗑️ 삭제</button>`;
                html += '</td>';

                html += '</tr>';
            });

            html += '</tbody></table>';
            html += `<p style="margin-top: 15px; color: #666; font-size: 0.9rem;">총 ${data.total}개의 예약된 스케줄</p>`;

            content.innerHTML = html;
        } else {
            // 예약이 없으면 숨김
            section.style.display = 'none';
        }
    } catch (error) {
        console.error('예약 현황 로드 오류:', error);
    }
}

// 스케줄 수정
function editSchedule(workspaceName) {
    // 워크스페이스 선택
    const select = document.getElementById('workspace-select');
    select.value = workspaceName;
    currentWorkspace = workspaceName;

    // 워크스페이스 정보 업데이트 (change 이벤트 트리거하지 않음)
    const selectedOption = select.options[select.selectedIndex];
    const infoBox = document.getElementById('workspace-info');
    document.getElementById('channel-id').textContent = selectedOption.dataset.channelId;
    document.getElementById('sheet-name').textContent = selectedOption.dataset.sheetName;
    infoBox.style.display = 'block';

    // 스레드 정보 초기화
    resetThreadInfo();

    // 저장된 스케줄 불러오기 (수정 모드에서만!)
    loadSchedule();

    // 스케줄 섹션으로 스크롤
    document.getElementById('auto-schedule-enabled').scrollIntoView({ behavior: 'smooth', block: 'center' });

    // 자동 실행 활성화 체크박스 강조
    setTimeout(() => {
        const checkbox = document.getElementById('auto-schedule-enabled');
        checkbox.checked = true;
        checkbox.dispatchEvent(new Event('change'));

        // 깜빡임 효과
        const settings = document.getElementById('schedule-settings');
        settings.style.animation = 'highlight 1s ease';
        setTimeout(() => {
            settings.style.animation = '';
        }, 1000);
    }, 500);
}

// 스케줄 삭제
async function deleteSchedule(workspaceName, displayName) {
    if (!confirm(`"${displayName}" 워크스페이스의 자동 실행 스케줄을 삭제하시겠습니까?\n\n삭제 후 서버를 재시작해야 적용됩니다.`)) {
        return;
    }

    try {
        // 빈 스케줄로 저장 (enabled: false)
        const response = await fetch('/api/schedule', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                workspace: workspaceName,
                schedule: {
                    enabled: false,
                    create_thread_day: '',
                    create_thread_time: '',
                    create_thread_message: '',
                    check_attendance_day: '',
                    check_attendance_time: '',
                    check_attendance_column: ''
                },
                notification_user_id: ''
            })
        });

        const data = await response.json();

        if (data.success) {
            alert('✓ 스케줄이 삭제되었습니다!\n\n서버를 재시작하면 적용됩니다.');
            // 예약 현황 새로고침
            loadAllSchedules();
        } else {
            alert('스케줄 삭제 실패: ' + data.error);
        }
    } catch (error) {
        alert('스케줄 삭제 오류: ' + error.message);
    }
}

// 유틸리티
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
