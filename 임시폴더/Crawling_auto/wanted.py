
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote
import csv
import datetime

# --- 사이트별 맞춤 정보 (원티드) ---
TARGET_URL = 'https://www.wanted.co.kr/search'
# 원티드는 URL 파라미터로 검색하는 방식 사용
# 검색 결과는 동적으로 로딩됨
JOB_LIST_CONTAINER_SELECTOR = 'div[class*="JobList"]'
# 개별 공고 선택자
JOB_POST_SELECTOR = 'div[data-cy="job-card"]'
# 링크는 a 태그에 포함
JOB_LINK_SELECTOR = 'a'
JOB_TITLE_SELECTOR = 'strong[class*="JobCard_title"]'

def main():
    """
    메인 크롤링 함수
    """
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # 봇 감지 방지
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(5)

    try:
        # 1. [준비] 웹 드라이버 초기화 및 라이브러리 임포트 (상단 참조)
        print("웹 드라이버를 초기화합니다.")

        # 2. [입력] 사용자에게 터미널을 통해 검색어 입력받기
        keyword = input("검색할 키워드를 입력하세요: ")

        # 3. [접속] URL 파라미터에 검색어를 포함하여 직접 검색 결과 페이지로 이동
        print(f"'{keyword}' 키워드로 검색을 실행합니다.")
        encoded_keyword = quote(keyword)
        search_url = f"{TARGET_URL}?query={encoded_keyword}&tab=position"

        print(f"검색 URL: {search_url}")
        driver.get(search_url)

        # 4. [대기] 검색 결과 페이지가 로딩될 때까지 대기
        print("검색 결과 페이지 로딩을 기다립니다.")
        time.sleep(5)  # 초기 로딩 대기

        # 페이지가 완전히 로드될 때까지 대기 (body 태그 확인)
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            print("페이지 로딩 완료")
        except Exception as e:
            print(f"페이지 로딩 대기 중 오류: {e}")

        # 동적 콘텐츠 로딩을 위한 스크롤
        print("페이지를 스크롤하여 모든 콘텐츠를 로드합니다.")
        last_height = driver.execute_script("return document.body.scrollHeight")
        for _ in range(3):  # 3번 스크롤
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # 6. [파싱] 검색 결과 페이지의 소스 코드를 BeautifulSoup으로 파싱
        print("페이지 소스를 파싱합니다.")
        html_source = driver.page_source
        soup = BeautifulSoup(html_source, 'html.parser')

        # 7. [정보 추출] 모든 채용 공고의 제목과 링크 수집
        print("채용 공고의 제목과 링크를 추출합니다.")

        # 여러 가능한 선택자 시도
        job_posts = []
        selectors_to_try = [
            'div[data-cy="job-card"]',
            'div[class*="JobCard"]',
            'article[class*="JobCard"]',
            'li[class*="JobCard"]',
            'a[class*="JobCard"]',
        ]

        for selector in selectors_to_try:
            job_posts = soup.select(selector)
            if job_posts:
                print(f"공고를 찾았습니다. 선택자: {selector}, 개수: {len(job_posts)}")
                break

        if not job_posts:
            print("공고를 찾을 수 없습니다. 페이지 구조를 분석합니다.")
            # 링크가 있는 요소들을 찾아봄
            all_links = soup.select('a[href*="/wd/"]')
            if all_links:
                print(f"채용 공고로 보이는 링크를 {len(all_links)}개 찾았습니다.")
                job_posts = all_links
            else:
                print("페이지 구조 샘플:")
                print(soup.prettify()[:2000])

        collected_data = []
        for post in job_posts:
            try:
                # 링크 추출 (post 자체가 a 태그인지, 내부에 a 태그가 있는지 확인)
                if post.name == 'a' and 'href' in post.attrs:
                    link_tag = post
                else:
                    link_tag = post.select_one('a')

                if link_tag and 'href' in link_tag.attrs:
                    href = link_tag['href']

                    # 채용 공고 링크인지 확인 (/wd/로 시작)
                    if '/wd/' not in href:
                        continue

                    # 제목 추출 (여러 선택자 시도)
                    title = None
                    title_selectors = [
                        'strong[class*="JobCard_title"]',
                        'h2',
                        'strong',
                        'span[class*="title"]',
                    ]

                    for title_sel in title_selectors:
                        title_tag = post.select_one(title_sel)
                        if title_tag:
                            title = title_tag.get_text(strip=True)
                            break

                    # 제목을 찾지 못하면 링크 텍스트 사용
                    if not title:
                        title = link_tag.get_text(strip=True)

                    if not title:
                        title = "제목 없음"

                    # 절대 경로로 변환
                    absolute_link = urljoin('https://www.wanted.co.kr', href)
                    collected_data.append([title, absolute_link])
            except Exception as e:
                print(f"공고 처리 중 오류: {e}")
                continue

        # 중복 제거 (같은 공고가 여러 번 나올 수 있음)
        collected_data = list(dict.fromkeys([tuple(x) for x in collected_data]))
        collected_data = [list(x) for x in collected_data]

        # 9. [CSV 저장] 수집된 데이터를 CSV 파일로 저장
        if collected_data:
            # 파일명 생성 (YYYY_MM_DD_원티드.csv)
            today_str = datetime.date.today().strftime('%Y_%m_%d')
            filename = f"{today_str}_원티드.csv"

            print(f"\n총 {len(collected_data)}개의 채용 정보를 '{filename}' 파일로 저장합니다.")

            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['공고명', '링크'])  # 헤더 작성
                writer.writerows(collected_data)  # 데이터 작성
        else:
            print("수집된 채용 정보가 없습니다.")

    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 10. [종료] 웹 드라이버 종료
        print("\n모든 작업이 완료되어 웹 드라이버를 종료합니다.")
        driver.quit()

if __name__ == '__main__':
    main()
