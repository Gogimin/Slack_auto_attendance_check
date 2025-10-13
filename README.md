# 슬랙 출석체크 자동화 프로그램

슬랙 API와 구글 스프레드시트 API를 활용하여 출석체크를 자동화하는 Python 프로그램입니다.

## 주요 기능

- 슬랙 출석체크 스레드에서 댓글 자동 수집
- "이름/출석했습니다" 패턴 자동 인식 및 파싱
- 출석 완료자 리스트 출력
- 구글 스프레드시트 자동 업데이트

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
3. 워크스페이스에 앱 설치
4. **Bot User OAuth Token** 복사 (xoxb-로 시작)

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
SLACK_THREAD_TS=1234567890.123456         # 출석체크 메시지 timestamp

# Google Sheets API 설정
GOOGLE_SHEETS_CREDENTIALS_PATH=config/credentials.json
SPREADSHEET_ID=your-spreadsheet-id        # 스프레드시트 ID (URL에서 확인)
SHEET_NAME=출석현황

# 열 설정
NAME_COLUMN=1      # 이름 열 (B열 = 1)
SLACK_COLUMN=10    # 슬랙 출석 열 (K열 = 10)

# 시작 행
START_ROW=4        # 데이터 시작 행 (5번째 행 = 4)
```

#### 슬랙 채널 ID 찾기
1. 슬랙 웹/앱에서 채널 열기
2. 채널 이름 클릭 → 하단의 채널 ID 복사

#### 스레드 Timestamp 찾기
출석체크 메시지에서 우클릭 → **링크 복사** → URL의 마지막 부분 (예: `p1234567890123456` → `1234567890.123456`)

#### 스프레드시트 ID 찾기
스프레드시트 URL에서 추출:
```
https://docs.google.com/spreadsheets/d/[이_부분이_SPREADSHEET_ID]/edit
```

## 사용 방법

### 기본 실행

```bash
conda activate auto
python src/main.py
```

### 실행 결과

프로그램 실행 시 다음과 같이 출력됩니다:

```
=== 슬랙 출석체크 자동화 시작 ===

[슬랙] 출석체크 스레드 댓글 수집 중...
찾은 댓글: 15개

[파싱] 출석자 파싱 중...
✓ 김철수 - 출석 확인
✓ 이영희 - 출석 확인
✓ 박민수 - 출석 확인
...

출석 완료: 12명
미출석: 3명

[구글 시트] 출석 데이터 업데이트 중...
✓ 김철수 - 업데이트 완료
✓ 이영희 - 업데이트 완료
...

=== 출석체크 완료 ===
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
