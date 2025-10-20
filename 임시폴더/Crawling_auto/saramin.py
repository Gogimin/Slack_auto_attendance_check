

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
TARGET_URL = 'https://www.saramin.co.kr/zf_user/'
SEARCH_PLACEHOLDER_SELECTOR = '#btn_search > span.keyword.static'  # 검색창 활성화를 위해 먼저 클릭할 요소
SEARCH_INPUT_SELECTOR = '#ipt_keyword_recruit'          # 실제 키워드 입력창
SEARCH_BUTTON_SELECTOR = '#btn_search_recruit'             # 검색 실행 버튼
JOB_LIST_CONTAINER_SELECTOR = '#content > div.content_wrap'
# 참고: '#recruit_info_list > div.content > div'는 모든 div를 대상으로 하므로,
# 광고 등 원치 않는 정보가 포함될 수 있습니다. '.item_recruit'가 더 정확할 수 있습니다.
JOB_POST_SELECTOR = '#recruit_info_list > div.content > div.item_recruit'
JOB_LINK_SELECTOR = 'div.area_job > h2 > a'
JOB_TITLE_SELECTOR = 'div.area_job > h2 > a > span'  # 공고 제목 선택자

def main():
    """
    메인 크롤링 함수
    """
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--start-maximized")  # 창을 최대화하는 옵션 추가
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(5) # 암시적 대기

    try:
        # 1. [준비] 웹 드라이버 초기화 및 라이브러리 임포트 (상단 참조)
        print("웹 드라이버를 초기화합니다.")

        # 2. [접속] 지정된 채용 사이트의 메인 페이지에 접속
        print(f"'{TARGET_URL}' 사이트에 접속합니다.")
        driver.get(TARGET_URL)

        # 3. [입력] 사용자에게 터미널을 통해 검색어 입력받기
        keyword = input("검색할 키워드를 입력하세요: ")

        # 4. [검색] 검색창에 키워드 입력 및 검색 실행
        print(f"'{keyword}' 키워드로 검색을 실행합니다.")

        # 4-1. [클릭] 검색창 활성화를 위해 placeholder 클릭
        placeholder = driver.find_element(By.CSS_SELECTOR, SEARCH_PLACEHOLDER_SELECTOR)
        placeholder.click()

        # 4-2. [입력] 실제 검색창에 키워드 입력
        # 명시적으로 실제 검색창이 나타날 때까지 대기
        search_input = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, SEARCH_INPUT_SELECTOR))
        )
        search_input.send_keys(keyword)

        # 4-3. [클릭] 검색 버튼 클릭
        search_button = driver.find_element(By.CSS_SELECTOR, SEARCH_BUTTON_SELECTOR)
        search_button.click()

        # 5. [대기] 검색 결과 페이지가 로딩될 때까지 대기
        print("검색 결과 페이지 로딩을 기다립니다.")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, JOB_LIST_CONTAINER_SELECTOR))
        )
        
        # 페이지가 완전히 그려질 시간을 추가로 확보
        time.sleep(2)

        # 6. [파싱] 검색 결과 페이지의 소스 코드를 BeautifulSoup으로 파싱
        print("페이지 소스를 파싱합니다.")
        html_source = driver.page_source
        soup = BeautifulSoup(html_source, 'html.parser')

        # 7. [정보 추출] 모든 채용 공고의 제목과 링크 수집
        print("채용 공고의 제목과 링크를 추출합니다.")
        job_posts = soup.select(JOB_POST_SELECTOR)

        collected_data = []
        for post in job_posts:
            title_tag = post.select_one(JOB_TITLE_SELECTOR)
            link_tag = post.select_one(JOB_LINK_SELECTOR)

            if title_tag and link_tag and 'href' in link_tag.attrs:
                title = title_tag.get_text(strip=True)
                relative_link = link_tag['href']
                # 8. [경로 변환] 상대 경로를 절대 경로 URL로 변환
                absolute_link = urljoin(TARGET_URL, relative_link)
                collected_data.append([title, absolute_link])

        # 9. [CSV 저장] 수집된 데이터를 CSV 파일로 저장
        if collected_data:
            # 파일명 생성 (YYYY_MM_DD_사람인.csv)
            today_str = datetime.date.today().strftime('%Y_%m_%d')
            filename = f"{today_str}_사람인.csv"

            print(f"\n총 {len(collected_data)}개의 채용 정보를 '{filename}' 파일로 저장합니다.")

            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['공고명', '링크'])  # 헤더 작성
                writer.writerows(collected_data)  # 데이터 작성
        else:
            print("수집된 채용 정보가 없습니다.")

    finally:
        # 10. [종료] 웹 드라이버 종료
        print("\n모든 작업이 완료되어 웹 드라이버를 종료합니다.")
        driver.quit()

if __name__ == '__main__':
    main()
