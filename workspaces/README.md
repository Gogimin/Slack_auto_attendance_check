# 워크스페이스 관리

이 폴더에는 각 슬랙 워크스페이스별 설정이 저장됩니다.

## 폴더 구조

```
workspaces/
├── 테스트/                    # 기본 테스트 워크스페이스
│   ├── config.json
│   └── credentials.json
├── 학교A/                     # 추가 워크스페이스 예시
│   ├── config.json
│   └── credentials.json
└── ... (최대 6개 권장)
```

## 새 워크스페이스 추가 방법

### 1. 폴더 생성
```
workspaces/새워크스페이스명/
```

### 2. config.json 생성

아래 템플릿을 복사하여 `config.json` 파일을 만드세요:

```json
{
  "name": "워크스페이스 표시 이름",
  "slack_bot_token": "xoxb-your-slack-bot-token-here",
  "slack_channel_id": "C1234567890",
  "spreadsheet_id": "1abc123def456...",
  "sheet_name": "출석현황",
  "name_column": 1,
  "start_row": 4
}
```

**설정 항목 설명:**
- `name`: Streamlit에서 표시될 이름
- `slack_bot_token`: 슬랙 Bot User OAuth Token (xoxb-로 시작)
- `slack_channel_id`: 출석체크할 슬랙 채널 ID (C로 시작)
- `spreadsheet_id`: 구글 스프레드시트 ID (URL에서 복사)
- `sheet_name`: 시트 이름 (탭 이름)
- `name_column`: 학생 이름이 있는 열 (A=0, B=1, C=2, ...)
- `start_row`: 데이터 시작 행 (0-based, 헤더 제외)

### 3. credentials.json 추가

구글 서비스 계정 JSON 키 파일을 복사하세요.

1. Google Cloud Console에서 서비스 계정 생성
2. JSON 키 다운로드
3. `credentials.json`으로 이름 변경
4. 워크스페이스 폴더에 복사

### 4. 확인

워크스페이스가 제대로 설정되었는지 확인:

```bash
conda activate auto
python src/workspace_manager.py
```

또는 Streamlit 앱에서 드롭다운에 표시되는지 확인하세요.

## 주의사항

⚠️ **보안:**
- `config.json`과 `credentials.json`에는 민감한 정보가 포함됩니다.
- 절대 Git에 커밋하지 마세요. (`.gitignore`에 추가됨)
- 파일 권한을 적절히 설정하세요.

⚠️ **권한:**
- 슬랙 봇이 채널에 초대되어 있어야 합니다.
- 구글 서비스 계정이 스프레드시트에 공유되어 있어야 합니다.

## 템플릿 예시

### 학교용 템플릿
```json
{
  "name": "ABC고등학교",
  "slack_bot_token": "xoxb-...",
  "slack_channel_id": "C...",
  "spreadsheet_id": "1...",
  "sheet_name": "출석현황",
  "name_column": 1,
  "start_row": 4
}
```

### 스터디 그룹용 템플릿
```json
{
  "name": "Python 스터디",
  "slack_bot_token": "xoxb-...",
  "slack_channel_id": "C...",
  "spreadsheet_id": "1...",
  "sheet_name": "참석현황",
  "name_column": 0,
  "start_row": 2
}
```

## 문제 해결

### 워크스페이스가 앱에 표시되지 않음

1. `config.json`의 JSON 형식 확인 (콤마, 중괄호 등)
2. 필수 항목이 모두 있는지 확인
3. `credentials.json`이 있는지 확인

### 설정 값 찾기

**Slack Channel ID:**
- 슬랙 채널에서 우클릭 → "링크 복사"
- URL에서 마지막 부분: `.../archives/C1234567890`

**Spreadsheet ID:**
- 구글 시트 URL: `https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit`
- 중간 부분의 긴 문자열

**열 인덱스:**
- A열 = 0
- B열 = 1
- C열 = 2
- ...

**시작 행:**
- 헤더가 1-4행이면 `start_row: 4` (5행부터 시작)
- 0-based 인덱스 사용
