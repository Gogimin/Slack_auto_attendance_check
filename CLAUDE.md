# 슬랙 출석체크 자동화 프로젝트

## 프로젝트 개요
슬랙 API를 활용하여 출석체크 스레드의 댓글을 자동으로 수집하고, 구글 스프레드시트에 출석 현황을 자동으로 업데이트하는 시스템

## 프로젝트 목표
1. 슬랙 스레드에서 출석 댓글 자동 수집
2. "이름/출석했습니다" 패턴 인식 및 파싱
3. 출석 완료자 리스트 출력
4. 구글 스프레드시트 "슬랙" 열에 자동 체크

## 기술 스택
- **언어**: Python (추천) 또는 Node.js
- **슬랙 API**: Slack Web API, Slack Events API
- **구글 API**: Google Sheets API
- **라이브러리**:
  - Python: `slack-sdk`, `google-api-python-client`, `google-auth`
  - Node.js: `@slack/web-api`, `googleapis`

## 프로젝트 실행 가능성: ✅ 가능

### 가능한 이유
1. Slack API는 스레드 댓글 읽기 기능 제공 (`conversations.replies`)
2. 정규표현식으로 "이름/출석" 패턴 감지 가능
3. Google Sheets API로 셀 값 자동 업데이트 가능
4. 실시간 모니터링 또는 주기적 체크 모두 구현 가능

## TASK 목록

### Phase 1: 환경 설정 및 API 연동 ✅
- [x] Task 1-1: 프로젝트 기술 스택 선택 (Python)
- [x] Task 1-2: 슬랙 앱 생성 및 Bot Token 발급
  - Slack App 생성 (https://api.slack.com/apps)
  - Bot Token Scopes 설정: `channels:history`, `channels:read`, `users:read`
  - 워크스페이스에 앱 설치
- [x] Task 1-3: 구글 클라우드 프로젝트 생성 및 Sheets API 활성화
  - Google Cloud Console에서 프로젝트 생성
  - Google Sheets API 활성화
  - 서비스 계정 생성 및 JSON 키 다운로드
- [x] Task 1-4: 환경변수 설정 (.env 파일)
  - SLACK_BOT_TOKEN
  - SLACK_CHANNEL_ID
  - GOOGLE_SHEETS_CREDENTIALS_PATH
  - SPREADSHEET_ID
- [x] Task 1-5: 프로젝트 구조 생성
  - 폴더 구조 생성 (config, src, tests, logs)
  - requirements.txt 작성
  - .gitignore, .env.example 생성

### Phase 2: 슬랙 API 구현 ✅
- [x] Task 2-1: 슬랙 API 연결 테스트
  - 워크스페이스 접근 확인
  - test_connection() 구현
- [x] Task 2-2: 특정 메시지의 스레드 댓글 읽기 구현
  - `conversations.replies` API 사용
  - 스레드 타임스탬프 기반 댓글 수집
  - 사용자 정보 포함하여 가져오기
- [x] Task 2-3: 출석 댓글 파싱 로직 구현
  - 정규표현식: `(\w+)\s*[/]?\s*출석`
  - 이름 추출 및 정규화
  - 중복 제거 로직
- [x] Task 2-4: 사용자 정보 매칭
  - Slack User ID를 실명으로 매칭
  - Display Name 또는 Real Name 사용
- [x] Task 2-5: 슬랙 링크 자동 파싱
  - URL에서 Thread TS 자동 추출
  - 대화형 입력 지원

### Phase 3: 구글 스프레드시트 연동 ✅
- [x] Task 3-1: Google Sheets API 연결 테스트
  - 스프레드시트 읽기 테스트
  - 권한 확인 (서비스 계정에 스프레드시트 공유 필요)
- [x] Task 3-2: 학생 명단 읽기
  - "이름" 열에서 학생 리스트 가져오기
  - 행 번호와 이름 매핑 딕셔너리 생성
- [x] Task 3-3: 출석 체크 업데이트 구현
  - 출석한 학생 이름으로 행 찾기
  - O/X/△ 문자로 출석 상태 표시
  - AttendanceStatus Enum 구현 (PRESENT/ABSENT/LATE)
  - 배치 업데이트 기능 구현

### Phase 4: 메인 로직 통합 ✅
- [x] Task 4-1: 전체 플로우 통합
  - 슬랙에서 출석자 수집 → 구글 시트 업데이트
  - main.py 작성 완료
- [x] Task 4-2: 출석 완료자 콘솔 출력
  - 출석한 학생 리스트 출력
  - 명단에 없는 이름 경고
- [x] Task 4-3: 열 선택 기능
  - 사용자가 열(H, K 등) 입력
  - 열 문자 ↔ 인덱스 변환 함수
- [x] Task 4-4: 에러 핸들링
  - API 호출 실패 처리
  - 이름 매칭 실패 시 로그 기록
  - 예외 상황 처리
- [x] Task 4-5: 미출석자 자동 X 표시
  - 출석하지 않은 학생 자동 감지
  - 해당 학생에게 X 표시

### Phase 5: 자동화 및 개선
- [ ] Task 5-1: 스레드 자동 감지 (선택)
  - 특정 키워드("출석체크") 포함 메시지 자동 감지
  - 최신 출석체크 스레드 자동 선택
- [ ] Task 5-2: 스케줄링 (선택)
  - 매주 토요일 특정 시간에 자동 실행
  - Cron job 또는 스케줄러 설정
- [ ] Task 5-3: 로깅 시스템
  - 실행 이력 로그 파일 저장
  - 출석 현황 히스토리 관리
- [ ] Task 5-4: 알림 기능 (선택)
  - 출석 체크 완료 후 슬랙 DM 또는 채널 메시지 전송
  - 미출석자 리스트 관리자에게 전송

### Phase 6: 테스트 및 배포
- [ ] Task 6-1: 단위 테스트 작성
  - 파싱 로직 테스트
  - 이름 매칭 테스트
- [ ] Task 6-2: 통합 테스트
  - 실제 슬랙 스레드로 테스트
  - 실제 구글 시트로 테스트 (테스트용 시트 사용)
- [ ] Task 6-3: 문서화
  - README.md 작성 (설치 및 사용 방법)
  - 환경 설정 가이드
- [ ] Task 6-4: 프로덕션 배포
  - 실제 운영 환경에서 실행
  - 모니터링 및 유지보수 계획

## 구현 시 주의사항

### 슬랙 API
1. **Rate Limiting**: Slack API는 호출 제한이 있으므로 적절한 지연 시간 필요
2. **Thread Timestamp**: 출석체크 메시지의 `ts` 값이 필요 (스레드 식별자)
3. **Bot Permissions**: 충분한 권한(scopes) 설정 필수

### 구글 스프레드시트
1. **서비스 계정 권한**: 스프레드시트를 서비스 계정 이메일과 공유 필요
2. **셀 주소 형식**: A1 notation 사용 (예: `K5`, `K6:K10`)
3. **체크박스 값**: Google Sheets에서 체크박스는 `TRUE`/`FALSE` 또는 숫자로 표현

### 이름 매칭
1. **정규화**: 공백, 대소문자, 특수문자 처리
2. **별명 처리**: 슬랙 닉네임과 실명이 다를 수 있음
3. **동명이인**: 학번이나 추가 식별자로 구분 필요 시 고려

## 예상 프로젝트 구조 (Python 기준)

```
Slack_auto_attendance_check/
├── .env                          # 환경변수 (API 키)
├── .gitignore                    # Git 제외 파일 (비밀 정보)
├── requirements.txt              # Python 패키지 의존성
├── README.md                     # 프로젝트 설명서
├── CLAUDE.md                     # 프로젝트 계획서 (이 파일)
├── config/
│   ├── credentials.json          # 구글 서비스 계정 키
│   └── settings.py               # 설정 파일
├── src/
│   ├── __init__.py
│   ├── main.py                   # 메인 실행 파일
│   ├── slack_handler.py          # 슬랙 API 처리
│   ├── sheets_handler.py         # 구글 시트 처리
│   ├── parser.py                 # 출석 댓글 파싱
│   └── utils.py                  # 유틸리티 함수
├── tests/
│   ├── test_parser.py
│   └── test_integration.py
└── logs/
    └── attendance.log            # 실행 로그
```

## 현재 진행 상황

### ✅ 완료된 기능
1. **슬랙 API 연동**
   - 스레드 댓글 자동 수집
   - "이름/출석" 패턴 인식
   - 슬랙 링크 자동 파싱 (URL → Thread TS)

2. **구글 스프레드시트 연동**
   - 학생 명단 자동 읽기
   - O/X/△ 문자로 출석 상태 표시
   - 배치 업데이트 기능

3. **메인 프로그램**
   - 전체 플로우 통합 완료
   - 사용자가 열(H, K 등) 선택 가능
   - 출석자 자동 매칭 및 업데이트

### 🔄 진행 중
- 미출석자 자동 X 표시 기능 추가

### 📝 남은 작업
- Phase 5: 자동화 및 개선 (선택 사항)
- Phase 6: 테스트 및 문서화

## 실행 방법

```bash
# 가상환경 활성화
conda activate auto

# 프로그램 실행
python run.py
```

## 다음 단계
1. 미출석자 자동 X 표시 기능 구현
2. 추가 개선 사항 논의
3. 프로덕션 배포 준비

## 참고 자료
- [Slack API Documentation](https://api.slack.com/docs)
- [Google Sheets API Documentation](https://developers.google.com/sheets/api)
- [Slack Python SDK](https://slack.dev/python-slack-sdk/)
- [Google API Python Client](https://github.com/googleapis/google-api-python-client)
