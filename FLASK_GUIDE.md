# Flask 웹 UI 사용 가이드

## 🚀 빠른 시작

### 방법 1: Python으로 직접 실행

```bash
conda activate auto
pip install -r requirements.txt
python app_flask.py
```

브라우저가 자동으로 열리고 `http://127.0.0.1:5000`에서 앱이 실행됩니다.

### 방법 2: EXE 파일로 실행 (권장)

1. **EXE 파일 빌드**
   ```
   build_exe.bat 더블클릭
   ```

2. **빌드된 파일 실행**
   ```
   dist/슬랙출석체크/슬랙출석체크.exe 더블클릭
   ```

3. **완료!**
   - 브라우저가 자동으로 열립니다
   - Python 설치 필요 없음
   - 다른 컴퓨터에 복사해서 사용 가능

## 📦 EXE 빌드 방법

### 준비 사항
- Python 3.11 이상
- pip로 requirements.txt 설치 완료

### 빌드 실행

**방법 1: 배치 파일 (추천)**
```
build_exe.bat 더블클릭
```

**방법 2: 명령어**
```bash
conda activate auto
pip install pyinstaller
pyinstaller attendance_app.spec --clean
```

### 빌드 결과

```
dist/슬랙출석체크/
├── 슬랙출석체크.exe        # 메인 실행 파일
├── templates/               # HTML 템플릿
├── static/                  # CSS, JS 파일
├── workspaces/              # 워크스페이스 설정
└── ... (기타 의존성 파일들)
```

### 배포하기

1. `dist/슬랙출석체크/` 폴더 전체를 복사
2. 다른 컴퓨터에 붙여넣기
3. `슬랙출석체크.exe` 더블클릭
4. 완료!

**주의:** `workspaces/` 폴더가 포함되어 있어야 합니다.

## 🖥️ 웹 UI 사용법

### 1. 워크스페이스 선택
- 드롭다운에서 워크스페이스 선택
- 채널 ID와 시트 이름 자동 표시

### 2. 스레드 선택

**자동 감지 (권장)**
1. "자동 감지" 라디오 버튼 선택
2. "최신 출석 스레드 찾기" 버튼 클릭
3. 찾은 스레드 확인

**수동 입력**
1. "수동 입력" 라디오 버튼 선택
2. 슬랙 링크 또는 Thread TS 입력
   - 예: `https://workspace.slack.com/archives/.../p1234567890123456`
   - 예: `1234567890.123456`

### 3. 출석체크 설정

**열 입력**
- 출석을 표시할 구글 시트의 열 입력 (예: K, H, L)

**옵션 선택**
- ☑ 미출석자에게 'X' 표시
- ☑ 스레드에 완료 댓글 작성
- ☑ 작성자에게 DM 전송

### 4. 실행
- "출석체크 시작" 버튼 클릭
- 실시간 진행 상황 확인
- 완료 후 결과 확인

### 5. 결과 확인

**통계 요약**
- 총 인원, 출석, 미출석, 출석률

**상세 정보**
- 출석자 명단
- 미출석자 명단
- 명단에 없는 이름 (있는 경우)

## 🎨 UI 특징

### Streamlit vs Flask

| 항목 | Streamlit | Flask |
|------|-----------|-------|
| 실행 | `streamlit run app.py` | `python app_flask.py` |
| EXE 빌드 | ❌ 어려움 | ✅ 가능 |
| UI 디자인 | 제한적 | 완전 커스터마이징 |
| 배포 | 복잡 | 간단 (.exe 하나) |
| 브라우저 | 자동 열림 | 자동 열림 |

### Flask 장점
✅ **독립 실행 가능** - Python 없이도 실행
✅ **빠른 배포** - 폴더 복사만으로 완료
✅ **커스텀 디자인** - 원하는 대로 UI 수정 가능
✅ **가벼움** - 필요한 기능만 포함

## 🔧 문제 해결

### EXE 빌드 실패

**오류: PyInstaller를 찾을 수 없음**
```bash
pip install pyinstaller
```

**오류: 모듈을 찾을 수 없음**
```bash
pip install -r requirements.txt
```

**오류: 빌드는 성공했지만 실행 안 됨**
1. `attendance_app.spec` 파일의 `datas` 섹션 확인
2. `templates`, `static`, `workspaces` 폴더가 포함되었는지 확인

### EXE 실행 오류

**오류: 워크스페이스가 없습니다**
- `workspaces/` 폴더가 exe 파일과 같은 위치에 있는지 확인
- `workspaces/테스트/config.json` 파일 확인

**오류: 슬랙 연결 실패**
- `config.json`의 `slack_bot_token` 확인
- 봇이 채널에 초대되어 있는지 확인

**오류: 구글 시트 접근 실패**
- `credentials.json` 파일 확인
- 서비스 계정과 스프레드시트 공유 확인

### 브라우저가 자동으로 열리지 않음

수동으로 브라우저를 열고 다음 주소로 접속:
```
http://127.0.0.1:5000
```

### 포트 충돌

다른 프로그램이 5000 포트를 사용 중인 경우:
1. `app_flask.py` 열기
2. 마지막 줄의 `port=5000`을 다른 포트로 변경 (예: `port=5001`)
3. 재빌드

## 📝 커스터마이징

### UI 디자인 변경

**색상 변경**
- `static/css/style.css` 열기
- 상단의 색상 코드 수정

**로고 추가**
- `templates/index.html` 열기
- `<header>` 태그에 이미지 추가

**기능 추가**
- `app_flask.py`에 새 라우트 추가
- `static/js/app.js`에 JavaScript 함수 추가

### 아이콘 추가

1. 아이콘 파일 준비 (`.ico` 형식)
2. `attendance_app.spec` 파일 열기
3. `icon=None`을 `icon='icon.ico'`로 변경
4. 재빌드

## 🚀 고급 기능

### 다중 인스턴스 실행

여러 워크스페이스를 동시에 실행하려면:
1. 각각 다른 포트 사용
2. 여러 개의 EXE 복사본 생성
3. 각각의 `workspaces/` 폴더 구성

### 자동 시작

Windows 시작 프로그램에 추가:
1. `슬랙출석체크.exe` 바로가기 만들기
2. `C:\Users\사용자명\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup`에 복사

### 로그 확인

콘솔 창에서 실행 로그 확인 가능:
- 슬랙 API 호출
- 구글 시트 업데이트
- 오류 메시지

## 💡 팁

### 빠른 출석체크

1. 워크스페이스 선택
2. "자동 감지" + "최신 출석 스레드 찾기"
3. 열 입력 (K)
4. "출석체크 시작"
→ 약 10초면 완료!

### 여러 워크스페이스 관리

- `workspaces/` 폴더에 최대 6개 추가 권장
- 각각 독립적으로 설정 관리
- 드롭다운으로 빠르게 전환

### 오프라인 배포

1. EXE 빌드
2. `dist/슬랙출석체크/` 폴더를 USB에 복사
3. 다른 컴퓨터에서 바로 실행
→ Python 설치 불필요!

## 📞 지원

문제가 발생하면:
1. 콘솔 창의 오류 메시지 확인
2. 브라우저 개발자 도구 (F12) → Console 탭 확인
3. 이슈 등록

## 🎉 완료!

Flask 웹 UI로 더 편리하게 출석체크를 관리하세요!
