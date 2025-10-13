# 슬랙 출석체크 자동화 프로그램

슬랙 API와 구글 스프레드시트 API를 활용하여 출석체크를 자동화하는 Python 프로그램입니다.

## 주요 기능

✅ **슬랙 API 연동**
- 출석체크 스레드 자동 감지 또는 수동 입력
- "이름/출석했습니다" 패턴 자동 인식 및 파싱
- 슬랙 링크 자동 파싱 (URL → Thread TS)

✅ **구글 스프레드시트 연동**
- 학생 명단 자동 읽기
- O/X/△ 문자로 출석 상태 표시
- 출석자/미출석자 자동 업데이트

✅ **알림 기능**
- 출석체크 스레드에 완료 댓글 작성
- 스레드 작성자에게 상세 DM 전송 (출석 현황 + 미출석자 명단)

## 프로젝트 구조

```
Slack_auto_attendance_check/
├── config/                      # 설정 파일
│   ├── __init__.py
│   ├── credentials.json        # 구글 서비스 계정 키 (직접 추가 필요)
│   └── settings.py             # 설정 관리
├── src/                        # 소스 코드
│   ├── __init__.py
│   ├── main.py                 # 메인 실행 파일
│   ├── slack_handler.py        # 슬랙 API 처리
│   ├── sheets_handler.py       # 구글 시트 처리
│   ├── parser.py               # 출석 댓글 파싱
│   └── utils.py                # 유틸리티 함수
├── tests/                      # 테스트 코드
│   └── __init__.py
├── logs/                       # 로그 파일
├── .env                        # 환경변수 (직접 생성 필요)
├── .env.example                # 환경변수 예제
├── .gitignore
├── requirements.txt            # Python 패키지 의존성
├── CLAUDE.md                   # 프로젝트 계획서
└── README.md                   # 이 파일
```

## 설치 방법

### 1. 필수 요구사항

- Python 3.11 이상
- Conda 환경 (auto)
- 슬랙 워크스페이스 관리자 권한
- 구글 클라우드 프로젝트

### 2. 패키지 설치

conda 환경을 활성화하고 필요한 패키지를 설치합니다:

```bash
conda activate auto
pip install -r requirements.txt
```

### 3. 슬랙 앱 설정

1. [Slack API 페이지](https://api.slack.com/apps)에서 새 앱 생성
2. **OAuth & Permissions**에서 다음 Bot Token Scopes 추가:
   - `channels:history` - 채널 메시지 읽기
   - `channels:read` - 채널 정보 읽기
   - `users:read` - 사용자 정보 읽기
   - `chat:write` - 메시지 작성
   - `im:write` - DM 전송
3. 워크스페이스에 앱 설치
4. **Bot User OAuth Token** 복사 (xoxb-로 시작)
5. 출석체크 채널에 봇 초대 (`@봇이름` 멘션)

### 4. 구글 스프레드시트 API 설정

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 새 프로젝트 생성
3. **API 및 서비스** → **라이브러리**에서 "Google Sheets API" 활성화
4. **사용자 인증 정보** → **서비스 계정 만들기**
5. 서비스 계정 생성 후 **키 추가** → **JSON** 선택
6. 다운로드한 JSON 파일을 `config/credentials.json`으로 저장
7. 스프레드시트를 서비스 계정 이메일과 공유 (편집자 권한)

### 5. 환경변수 설정

`.env.example` 파일을 복사하여 `.env` 파일을 생성하고 실제 값으로 수정:

```bash
cp .env.example .env
```

`.env` 파일 내용:

```
# Slack API 설정
SLACK_BOT_TOKEN=xoxb-your-actual-token
SLACK_CHANNEL_ID=C1234567890              # 출석체크 채널 ID

# Google Sheets API 설정
GOOGLE_SHEETS_CREDENTIALS_PATH=config/credentials.json
SPREADSHEET_ID=your-spreadsheet-id        # 스프레드시트 ID (URL에서 확인)
SHEET_NAME=출석현황

# 열 설정
NAME_COLUMN=1      # 이름 열 (B열 = 1)

# 시작 행
START_ROW=4        # 데이터 시작 행 (5번째 행 = 4)
```

**주의:** SLACK_THREAD_TS는 제거되었습니다. 프로그램 실행 시 자동 감지 또는 수동 입력으로 선택합니다.

#### 슬랙 채널 ID 찾기
1. 슬랙 웹/앱에서 채널 열기
2. 채널 이름 클릭 → 하단의 채널 ID 복사

#### 스프레드시트 ID 찾기
스프레드시트 URL에서 추출:
```
https://docs.google.com/spreadsheets/d/[이_부분이_SPREADSHEET_ID]/edit
```

#### 스프레드시트 열 구조
프로그램은 다음 구조를 가정합니다:
- **B열 (NAME_COLUMN=1)**: 학생 이름
- **출석 체크 열**: 프로그램 실행 시 선택 (예: H열, K열, L열 등)

## 사용 방법

### 기본 실행

```bash
conda activate auto
python run.py
```

### 실행 프로세스

프로그램은 대화형으로 다음 단계를 진행합니다:

1. **환경 설정 확인** - 슬랙/구글 시트 연결 확인
2. **슬랙 API 연결** - 워크스페이스 접속
3. **스레드 선택**
   - 옵션 1: 자동 감지 (최신 "출석 스레드" 메시지 찾기)
   - 옵션 2: 수동 입력 (링크 붙여넣기)
4. **출석 댓글 수집** - 스레드 댓글 가져오기
5. **출석 파싱** - "이름/출석" 패턴 인식
6. **열 선택** - 출석 체크할 열 입력 (예: K)
7. **학생 명단 읽기** - 스프레드시트에서 명단 가져오기
8. **출석 매칭** - 출석자/미출석자 확인
9. **미출석자 표시** - X 표시 여부 확인
10. **업데이트** - 스프레드시트에 O/X 표시
11. **알림 전송**
    - 스레드에 완료 댓글 작성
    - 작성자에게 DM 전송 (출석 현황 + 미출석자 명단)

### 실행 예시

```
==================================================
  슬랙 출석체크 자동화
==================================================

[3. 출석체크 스레드 선택]
1. 자동 감지 (최신 '출석 스레드' 메시지 찾기)
2. 수동 입력 (링크 또는 Thread TS 직접 입력)

선택 (1/2): 1

✓ 출석체크 스레드 발견!
✓ 댓글 수집 완료: 25개
✓ 출석 파싱 완료: 3명

[5. 출석체크할 열 선택]
열 입력: K

출석 현황:
  ✓ 출석: 3명
  ✗ 미출석: 21명

미출석자에게 'X'를 표시하시겠습니까? (y/N): y

출석 체크를 진행하시겠습니까? (y/N): y

✓ 출석 체크 완료: 24/24명
```

## 개발 로드맵

현재 진행 상황은 [CLAUDE.md](CLAUDE.md)를 참조하세요.

- [x] Phase 1: 환경 설정 및 프로젝트 구조 생성
- [ ] Phase 2: 슬랙 API 구현
- [ ] Phase 3: 구글 스프레드시트 연동
- [ ] Phase 4: 메인 로직 통합
- [ ] Phase 5: 자동화 및 개선
- [ ] Phase 6: 테스트 및 배포

## 문제 해결

### 슬랙 API 권한 오류
- Bot Token Scopes가 올바르게 설정되었는지 확인
- 앱을 워크스페이스에 재설치

### 구글 시트 접근 오류
- `credentials.json` 파일이 올바른 위치에 있는지 확인
- 서비스 계정 이메일과 스프레드시트를 공유했는지 확인

### 환경변수 오류
- `.env` 파일이 프로젝트 루트에 있는지 확인
- 모든 필수 값이 입력되었는지 확인

## 라이선스

이 프로젝트는 교육용으로 제작되었습니다.

## 기여

버그 리포트나 기능 제안은 이슈로 등록해주세요.
