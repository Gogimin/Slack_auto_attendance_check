# 채용 사이트 크롤링 스크립트 생성 가이드

## 목적
사용자가 새로운 채용 사이트 URL을 제공하면, 해당 사이트의 구조에 맞는 크롤링 파이썬 스크립트를 자동으로 생성한다.

---

## 작업 프로세스

### 1. 사이트 분석 단계
사용자가 채용 사이트 URL을 제공하면 다음을 수행:

1. **사이트 접속 및 구조 파악**
   - 메인 페이지 URL 확인
   - 검색 기능이 있는지 확인
   - 검색 방식 파악 (버튼 클릭 / Enter 키 / URL 파라미터 등)

2. **CSS 선택자 식별** (개발자 도구 활용)
   - `SEARCH_INPUT_SELECTOR`: 검색어 입력창
   - `SEARCH_BUTTON_SELECTOR`: 검색 버튼 (있는 경우)
   - `JOB_LIST_CONTAINER_SELECTOR`: 검색 결과 목록 컨테이너
   - `JOB_POST_SELECTOR`: 개별 채용 공고 요소
   - `JOB_LINK_SELECTOR`: 공고 상세 페이지 링크
   - `JOB_TITLE_SELECTOR`: 공고 제목

3. **특이사항 파악**
   - 검색창 활성화를 위한 추가 클릭이 필요한가?
   - 검색 실행 방법 (버튼 클릭 vs Enter 키)
   - 동적 로딩이 있는가? (추가 대기 시간 필요)
   - 페이지네이션이 있는가?

---

### 2. 스크립트 생성 단계

**파일명 규칙**: `{사이트명영문}.py`
- 예: `saramin.py`, `inthiswork.py`, `wanted.py`

**템플릿 기반 코드 생성**:

```python
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import csv
import datetime

# --- 사이트별 맞춤 정보 ---
TARGET_URL = '사이트_메인_URL'
SEARCH_INPUT_SELECTOR = '검색창_선택자'
SEARCH_BUTTON_SELECTOR = '검색버튼_선택자_또는_None'
JOB_LIST_CONTAINER_SELECTOR = '결과목록_컨테이너_선택자'
JOB_POST_SELECTOR = '개별공고_선택자'
JOB_LINK_SELECTOR = '공고링크_선택자'
JOB_TITLE_SELECTOR = '공고제목_선택자'

def main():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(5)

    try:
        print("웹 드라이버를 초기화합니다.")
        print(f"'{TARGET_URL}' 사이트에 접속합니다.")
        driver.get(TARGET_URL)

        keyword = input("검색할 키워드를 입력하세요: ")
        print(f"'{keyword}' 키워드로 검색을 실행합니다.")

        # [검색 실행 로직 - 사이트별 맞춤]
        # 패턴 1: 직접 검색창 입력 + 버튼 클릭
        # 패턴 2: 검색 아이콘 클릭 → 검색창 활성화 → Enter
        # 패턴 3: placeholder 클릭 → 검색창 활성화 → 버튼 클릭

        # 검색 결과 대기
        print("검색 결과 페이지 로딩을 기다립니다.")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, JOB_LIST_CONTAINER_SELECTOR))
        )
        time.sleep(2)

        # 페이지 파싱
        print("페이지 소스를 파싱합니다.")
        html_source = driver.page_source
        soup = BeautifulSoup(html_source, 'html.parser')

        # 정보 추출
        print("채용 공고의 제목과 링크를 추출합니다.")
        job_posts = soup.select(JOB_POST_SELECTOR)

        collected_data = []
        for post in job_posts:
            title_tag = post.select_one(JOB_TITLE_SELECTOR)
            link_tag = post.select_one(JOB_LINK_SELECTOR)

            if title_tag and link_tag and 'href' in link_tag.attrs:
                title = title_tag.get_text(strip=True)
                relative_link = link_tag['href']
                absolute_link = urljoin(TARGET_URL, relative_link)
                collected_data.append([title, absolute_link])

        # CSV 저장
        if collected_data:
            today_str = datetime.date.today().strftime('%Y_%m_%d')
            filename = f"{today_str}_{사이트명}.csv"

            print(f"\n총 {len(collected_data)}개의 채용 정보를 '{filename}' 파일로 저장합니다.")

            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['공고명', '링크'])
                writer.writerows(collected_data)
        else:
            print("수집된 채용 정보가 없습니다.")

    finally:
        print("\n모든 작업이 완료되어 웹 드라이버를 종료합니다.")
        driver.quit()

if __name__ == '__main__':
    main()
```

---

### 3. 검증 및 조정

생성된 스크립트는 다음을 확인:
- [ ] CSS 선택자가 정확한가?
- [ ] 검색 실행 로직이 사이트에 맞는가?
- [ ] 대기 시간이 충분한가?
- [ ] 상대 경로가 절대 경로로 잘 변환되는가?
- [ ] CSV 파일명이 적절한가?

---

## 참고: 기존 구현 사례

### 사람인 (saramin.py)
- **특이사항**: placeholder 클릭 → 검색창 활성화 필요
- **검색 실행**: 버튼 클릭
- **파일명**: `YYYY_MM_DD_사람인.csv`

### 인디스워크 (inthiswork.py)
- **특이사항**: 검색 아이콘 클릭 → 오버레이 검색창
- **검색 실행**: Enter 키
- **파일명**: `YYYY_MM_DD_인디스워크.csv`

---

## 사용자 요청 시 Claude의 행동 지침

1. **사용자가 사이트 URL을 제공하면**:
   - 이 문서(CLAUDE.md)를 참고
   - 사이트 구조 분석 (필요시 사용자에게 질문)
   - CSS 선택자 식별
   - 템플릿 기반으로 스크립트 생성
   - `{사이트명}.py` 파일로 저장

2. **생성 후**:
   - 주요 선택자와 특이사항 설명
   - 테스트 권장 사항 안내

3. **에러 발생 시**:
   - 선택자 수정
   - 대기 시간 조정
   - 검색 로직 패턴 변경

---

## 체크리스트

새로운 사이트 스크립트 생성 시:
- [ ] TARGET_URL 설정
- [ ] 모든 CSS 선택자 식별 완료
- [ ] 검색 실행 로직 구현
- [ ] 명시적 대기 추가
- [ ] 상대/절대 경로 처리
- [ ] CSV 파일명에 사이트명 포함
- [ ] 한글 주석 추가
- [ ] try-finally로 드라이버 종료 보장

---

## 추가 고려사항

### 페이지네이션 처리 (향후 확장)
현재는 첫 페이지만 크롤링. 필요시 다음 페이지 버튼 클릭 로직 추가.

### 로그인 필요 사이트
로그인이 필요한 경우, 사용자에게 사전 안내 및 로그인 로직 추가.

### API 기반 사이트
Network 탭에서 API 엔드포인트 발견 시, API 직접 호출 고려.
