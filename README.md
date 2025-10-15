# 슬랙 출석체크 자동화 프로그램

슬랙 API와 구글 스프레드시트 API를 활용하여 출석체크를 자동화하는 **Flask 웹 애플리케이션**입니다.

**더블클릭 한 번으로 실행 가능!** 🚀

## 🌟 주요 기능

✅ **다중 워크스페이스 지원**
- 여러 슬랙 워크스페이스를 하나의 프로그램으로 관리
- 드롭다운으로 간편하게 전환
- 워크스페이스별 독립적인 설정 관리

✅ **슬랙 API 연동**
- 출석체크 스레드 자동 감지 또는 수동 입력
- "이름/출석했습니다" 패턴 자동 인식 및 파싱
- 슬랙 링크 자동 파싱 (URL → Thread TS)
- **NEW!** 출석 스레드 자동 생성 (예약 시간 설정)

✅ **구글 스프레드시트 연동**
- 학생 명단 자동 읽기
- O/X/△ 문자로 출석 상태 표시
- 출석자/미출석자 자동 업데이트

✅ **알림 기능**
- 출석체크 스레드에 완료 댓글 작성
- **NEW!** 특정 담당자에게 상세 DM 전송 (출석 현황 + 미출석자 명단)

✅ **자동 실행 스케줄** 🆕
- 매주 특정 요일/시간에 출석 스레드 자동 생성
- 매주 특정 요일/시간에 출석 자동 집계
- **한국 시간대 (KST, UTC+9) 지원**
- 워크스페이스별 독립적인 스케줄 설정
- 웹 UI에서 간편하게 스케줄 관리

✅ **Flask 웹 UI**
- 아름다운 그라데이션 디자인
- 실시간 진행 상황 표시
- 통계 대시보드 제공
- **NEW!** 스케줄 설정 UI

✅ **EXE 빌드 지원**
- Python 설치 없이 실행 가능
- 다른 컴퓨터에 쉽게 배포

## 🚀 빠른 시작

### 1. 패키지 설치 (최초 1회만)

```bash
conda activate auto
pip install -r requirements.txt
```

### 2. 프로그램 실행

**방법 A: Python으로 직접 실행 (개발/테스트)**
```
실행.bat 더블클릭
```

**방법 B: EXE 파일로 빌드 (배포)**
```
빌드.bat 더블클릭
```
→ `dist/슬랙출석체크/슬랙출석체크.exe` 생성
→ EXE 파일 더블클릭으로 실행!

브라우저가 자동으로 열리고 `http://127.0.0.1:5000`에서 앱이 실행됩니다.

## 📁 프로젝트 구조

```
Slack_auto_attendance_check/
├── 실행.bat                    # Flask 앱 실행
├── 빌드.bat                    # EXE 파일 빌드
├── 사용방법.txt                # 간단한 사용 가이드
├── build_exe.py                # 빌드 스크립트
├── app_flask.py                # Flask 메인 앱
├── attendance_app.spec         # PyInstaller 설정
├── requirements.txt            # 패키지 의존성
├── README.md                   # 이 파일
├── FLASK_GUIDE.md              # Flask 사용 가이드
├── CLAUDE.md                   # 프로젝트 계획서
├── .gitignore
│
├── src/                        # 소스 코드
│   ├── __init__.py
│   ├── slack_handler.py        # 슬랙 API 처리
│   ├── sheets_handler.py       # 구글 시트 처리
│   ├── parser.py               # 출석 댓글 파싱
│   ├── utils.py                # 유틸리티 함수
│   └── workspace_manager.py    # 워크스페이스 관리자
│
├── templates/                  # HTML 템플릿
│   └── index.html
│
├── static/                     # 정적 파일
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
│
└── workspaces/                 # 워크스페이스 설정
    ├── README.md               # 워크스페이스 추가 가이드
    └── 테스트/                  # 워크스페이스 예시
        ├── config.json         # 슬랙/구글 시트 설정
        └── credentials.json    # 구글 서비스 계정 키
```

## ⚙️ 설치 방법

### 1. 필수 요구사항

- **Python 3.11 이상**
- **Conda 환경** (또는 venv)
- 슬랙 워크스페이스 관리자 권한
- 구글 클라우드 프로젝트

### 2. 슬랙 앱 설정

1. [Slack API 페이지](https://api.slack.com/apps)에서 새 앱 생성
2. **OAuth & Permissions**에서 다음 Bot Token Scopes 추가:
   - `channels:history` - 채널 메시지 읽기
   - `channels:read` - 채널 정보 읽기
   - `users:read` - 사용자 정보 읽기
   - `users:read.email` - **이메일로 사용자 찾기 (필수!)** 🆕
   - `chat:write` - 메시지 작성
   - `im:write` - DM 전송
3. 워크스페이스에 앱 설치
4. **Bot User OAuth Token** 복사 (xoxb-로 시작)
5. 출석체크 채널에 봇 초대 (`@봇이름` 멘션)

### 3. 구글 스프레드시트 API 설정

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 새 프로젝트 생성
3. **API 및 서비스** → **라이브러리**에서 "Google Sheets API" 활성화
4. **사용자 인증 정보** → **서비스 계정 만들기**
5. 서비스 계정 생성 후 **키 추가** → **JSON** 선택
6. 다운로드한 JSON 파일을 `workspaces/워크스페이스명/credentials.json`으로 저장
7. 스프레드시트를 서비스 계정 이메일과 공유 (편집자 권한)

### 4. 워크스페이스 설정

`workspaces/테스트/` 폴더를 참고하여 새 워크스페이스를 추가하세요.

#### config.json 예시:

```json
{
  "name": "학교A",
  "slack_bot_token": "xoxb-your-slack-bot-token",
  "slack_channel_id": "C1234567890",
  "spreadsheet_id": "1abc123...",
  "sheet_name": "출석현황",
  "name_column": 1,
  "start_row": 4
}
```

상세한 방법은 [workspaces/README.md](workspaces/README.md)를 참조하세요.

## 🎯 사용 방법

### 웹 UI 사용법

1. **워크스페이스 선택** - 드롭다운에서 선택
2. **스레드 선택** - 자동 감지 또는 수동 입력
3. **열 입력** - 출석 체크할 열 (예: K)
4. **옵션 설정** - 미출석자 X 표시, 알림 전송 여부
5. **출석체크 시작** - 버튼 클릭!

자세한 사용법은 [FLASK_GUIDE.md](FLASK_GUIDE.md)를 참조하세요.

## 📦 EXE 빌드

### 빌드 방법

```
빌드.bat 더블클릭
```

또는 터미널에서:
```bash
conda activate auto
python build_exe.py
```

### 빌드 결과

```
dist/슬랙출석체크/
├── 슬랙출석체크.exe        # 메인 실행 파일
├── templates/              # HTML 템플릿
├── static/                 # CSS, JS 파일
├── workspaces/             # 워크스페이스 설정
└── ... (기타 의존성 파일들)
```

### 배포하기

1. `dist/슬랙출석체크/` 폴더 전체를 복사
2. 다른 컴퓨터에 붙여넣기
3. `슬랙출석체크.exe` 더블클릭
4. 완료! (Python 설치 필요 없음)

## 💡 자주 묻는 질문

### Q1: Python이 없어도 실행 가능한가요?
**A:** EXE 파일로 빌드하면 Python 없이도 실행 가능합니다!
1. `빌드.bat` 더블클릭
2. `dist/슬랙출석체크/슬랙출석체크.exe` 실행

### Q2: 여러 학교/워크스페이스를 관리할 수 있나요?
**A:** 네! `workspaces/` 폴더에 여러 워크스페이스를 추가하고 웹에서 드롭다운으로 선택하면 됩니다.

### Q3: 실행.bat이 작동하지 않아요.
**A:** 터미널에서 직접 실행:
```bash
conda activate auto
python app_flask.py
```

### Q4: 브라우저가 자동으로 열리지 않아요.
**A:** 수동으로 브라우저를 열고 다음 주소로 접속:
```
http://127.0.0.1:5000
```


## 🔧 문제 해결

### 슬랙 API 권한 오류
- Bot Token Scopes가 올바르게 설정되었는지 확인
- 앱을 워크스페이스에 재설치

### 구글 시트 접근 오류
- `credentials.json` 파일이 올바른 위치에 있는지 확인
- 서비스 계정 이메일과 스프레드시트를 공유했는지 확인

### EXE 빌드 오류
- PyInstaller 설치: `pip install pyinstaller`
- 모든 패키지 설치: `pip install -r requirements.txt`
- 재시도

### 워크스페이스가 표시되지 않음
- `workspaces/워크스페이스명/config.json` 파일 확인
- `workspaces/워크스페이스명/credentials.json` 파일 확인
- JSON 형식이 올바른지 확인

## 📚 문서

- [사용방법.txt](사용방법.txt) - 간단한 사용 가이드
- [FLASK_GUIDE.md](FLASK_GUIDE.md) - Flask 웹 UI 상세 가이드
- **[자동실행_가이드.md](자동실행_가이드.md) - 자동 실행 스케줄 설정 가이드** 🆕
- [CLAUDE.md](CLAUDE.md) - 프로젝트 계획 및 진행 상황
- [workspaces/README.md](workspaces/README.md) - 워크스페이스 추가 방법

## 🎉 완료된 기능

✅ 다중 워크스페이스 지원
✅ Flask 웹 UI
✅ EXE 빌드 지원
✅ 출석체크 자동화
✅ 알림 기능
✅ 통계 대시보드
✅ **자동 실행 스케줄** 🆕
✅ **특정 담당자 알림** 🆕

## 🚧 향후 개선 사항

- [ ] 아이콘 추가
- [ ] 로깅 시스템
- [ ] 출석률 추이 그래프

## 📊 기술 스택

- **Backend**: Flask 3.0.0
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **APIs**: Slack Web API, Google Sheets API
- **Scheduler**: APScheduler 3.10.4 (한국 시간대 지원) 🆕
- **Build**: PyInstaller 6.3.0

## 📄 라이선스

이 프로젝트는 교육용으로 제작되었습니다.

## 🙏 도움말

문제가 발생하거나 질문이 있으면 이슈를 등록해주세요.

---

**Made with Python & Flask ❤️**

**v2.1** - 자동 실행 스케줄 기능 추가! 🎉
