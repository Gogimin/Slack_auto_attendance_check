
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

# --- 사이트별 맞춤 정보 (잡코리아) ---
TARGET_URL = 'https://www.jobkorea.co.kr/theme/entry-level-internship'
SEARCH_INPUT_SELECTOR = '#stext'  # 검색어 입력창
SEARCH_BUTTON_SELECTOR = 'button.tplBtn.btnSearch'  # 검색 버튼
JOB_LIST_CONTAINER_SELECTOR = 'div.recruit-info'
JOB_POST_SELECTOR = 'li.list-post'
JOB_LINK_SELECTOR = 'a.link-recruits'
JOB_TITLE_SELECTOR = 'a.link-recruits'

def main():
    """
    메인 크롤링 함수
    """
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(5)

    try:
        # 1. [준비] 웹 드라이버 초기화
        print("웹 드라이버를 초기화합니다.")

        # 2. [접속] 지정된 채용 사이트의 메인 페이지에 접속
        print(f"'{TARGET_URL}' 사이트에 접속합니다.")
        driver.get(TARGET_URL)
        time.sleep(3)  # 초기 로딩 대기

        # 3. [입력] 사용자에게 터미널을 통해 검색어 입력받기
        keyword = input("검색할 키워드를 입력하세요: ")

        # 4. [검색] 검색창에 키워드 입력 및 검색 실행
        print(f"'{keyword}' 키워드로 검색을 실행합니다.")

        # 검색창 찾기 - 여러 선택자 시도
        search_input = None
        search_selectors = [
            '#recruitSearchForm input[type="text"]',
            '#recruitSearchForm input.ipt',
            'input[placeholder*="검색"]',
            'input[name="stext"]',
            '#stext',
        ]

        for selector in search_selectors:
            try:
                search_input = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                if search_input:
                    print(f"검색창 발견: {selector}")
                    break
            except:
                continue

        if not search_input:
            print("검색창을 찾을 수 없습니다.")
        else:
            search_input.clear()
            search_input.send_keys(keyword)

            # 검색 버튼 클릭 시도
            button_clicked = False
            button_selectors = [
                '#recruitSearchForm button[type="submit"]',
                '#recruitSearchForm .btnSearch',
                'button.tplBtn.btnSearch',
                '#recruitSearchForm button',
            ]

            for selector in button_selectors:
                try:
                    search_button = driver.find_element(By.CSS_SELECTOR, selector)
                    search_button.click()
                    print(f"검색 버튼 클릭: {selector}")
                    button_clicked = True
                    break
                except:
                    continue

            if not button_clicked:
                # Enter 키로 검색
                try:
                    search_input.send_keys(Keys.RETURN)
                    print("Enter 키로 검색 실행")
                except:
                    pass

        # 5. [대기] 검색 결과 페이지가 로딩될 때까지 대기
        print("검색 결과 페이지 로딩을 기다립니다.")
        time.sleep(3)

        # 6. [파싱] 검색 결과 페이지의 소스 코드를 BeautifulSoup으로 파싱
        print("페이지 소스를 파싱합니다.")
        html_source = driver.page_source
        soup = BeautifulSoup(html_source, 'html.parser')

        # 7. [정보 추출] 모든 채용 공고의 제목과 링크 수집
        print("채용 공고의 제목과 링크를 추출합니다.")

        # 채용 공고 제목 링크만 정확히 찾기
        # p.rTit > a 선택자 사용 (공고 제목만)
        job_links = soup.select('p.rTit > a')

        if job_links:
            print(f"채용 공고를 {len(job_links)}개 찾았습니다.")
        else:
            print("공고를 찾을 수 없습니다.")
            print(f"현재 URL: {driver.current_url}")

        collected_data = []

        for link in job_links:
            try:
                if 'href' not in link.attrs:
                    continue

                href = link['href']
                title = link.get_text(strip=True)

                # 제목이 없으면 스킵
                if not title:
                    continue

                # 절대 경로로 변환
                absolute_link = urljoin('https://www.jobkorea.co.kr', href)

                collected_data.append([title, absolute_link])
                print(f"수집: {title[:50]}...")

            except Exception as e:
                continue

        # 중복 제거
        collected_data = list(dict.fromkeys([tuple(x) for x in collected_data]))
        collected_data = [list(x) for x in collected_data]

        # 8. [CSV 저장] 수집된 데이터를 CSV 파일로 저장
        if collected_data:
            today_str = datetime.date.today().strftime('%Y_%m_%d')
            filename = f"{today_str}_잡코리아.csv"

            print(f"\n총 {len(collected_data)}개의 채용 정보를 '{filename}' 파일로 저장합니다.")

            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['공고명', '링크'])
                writer.writerows(collected_data)
        else:
            print("수집된 채용 정보가 없습니다.")

    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 9. [종료] 웹 드라이버 종료
        print("\n모든 작업이 완료되어 웹 드라이버를 종료합니다.")
        driver.quit()

if __name__ == '__main__':
    main()
