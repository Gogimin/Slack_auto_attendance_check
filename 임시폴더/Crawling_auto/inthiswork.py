
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

# --- 사이트별 맞춤 정보 (인디스워크) ---
TARGET_URL = 'https://inthiswork.com/'
# 1. 메인 페이지의 검색 아이콘
SEARCH_ICON_SELECTOR = '#menu-primary > li.fusion-custom-menu-item.fusion-main-menu-search.fusion-search-overlay > a'
# 2. 아이콘 클릭 후 나타나는 검색어 입력창
SEARCH_INPUT_SELECTOR = '.fusion-search-field input'
# 3. 검색 실행은 Enter 키로 하므로 버튼 선택자는 없음
SEARCH_BUTTON_SELECTOR = None
# 4. 검색 결과 목록을 감싸는 컨테이너
JOB_LIST_CONTAINER_SELECTOR = '#content'
# 5. 개별 채용 공고 (article 태그 사용)
JOB_POST_SELECTOR = 'article.post'
# 6. 공고 제목과 링크는 동일한 a 태그에 있음
JOB_LINK_SELECTOR = 'h2 > a'
JOB_TITLE_SELECTOR = 'h2 > a'

def main():
    """
    메인 크롤링 함수
    """
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

        # 1. 검색 아이콘 클릭
        search_icon = driver.find_element(By.CSS_SELECTOR, SEARCH_ICON_SELECTOR)
        search_icon.click()

        # 2. 검색창이 나타날 때까지 대기 후 키워드 입력
        search_input = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, SEARCH_INPUT_SELECTOR))
        )
        search_input.send_keys(keyword)

        # 3. Enter 키를 입력하여 검색 실행
        search_input.send_keys(Keys.RETURN)

        # 4. 검색 결과 페이지가 로딩될 때까지 대기
        print("검색 결과 페이지 로딩을 기다립니다.")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, JOB_LIST_CONTAINER_SELECTOR))
        )
        time.sleep(2) # 렌더링 시간 추가 확보

        # 5. 검색 결과 페이지 소스 파싱
        print("페이지 소스를 파싱합니다.")
        html_source = driver.page_source
        soup = BeautifulSoup(html_source, 'html.parser')

        # 6. 정보 추출
        print("채용 공고의 제목과 링크를 추출합니다.")
        job_posts = soup.select(JOB_POST_SELECTOR)

        collected_data = []
        for post in job_posts:
            # 제목과 링크를 포함하는 a 태그를 직접 찾음
            link_tag = post.select_one(JOB_LINK_SELECTOR)

            if link_tag and 'href' in link_tag.attrs:
                title = link_tag.get_text(strip=True)
                link = link_tag['href']
                # 인디스워크는 절대 경로를 사용하므로 urljoin이 필요 없지만, 안정성을 위해 유지
                absolute_link = urljoin(TARGET_URL, link)
                collected_data.append([title, absolute_link])

        # 7. CSV 파일로 저장
        if collected_data:
            today_str = datetime.date.today().strftime('%Y_%m_%d')
            filename = f"{today_str}_인디스워크.csv"

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
