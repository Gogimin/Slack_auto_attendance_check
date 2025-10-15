// 전역 변수
let currentWorkspace = null;
let threadTS = null;
let threadUser = null;

// DOM 로드 완료 시
document.addEventListener('DOMContentLoaded', function() {
    loadWorkspaces();
    setupEventListeners();
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

// 유틸리티
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
