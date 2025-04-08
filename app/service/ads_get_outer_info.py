from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
from collections import OrderedDict


def get_insta_info(user, post):
    # 글로벌 드라이버 사용
    options = Options()
    options.add_argument("--start-fullscreen")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu") 

    # WebDriver Manager를 이용해 ChromeDriver 자동 관리
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(f"https://www.instagram.com/p/{post}/")
        time.sleep(5)

        # ESC 키 누르기 (예: 로그인 팝업 닫기)
        actions = ActionChains(driver)
        actions.send_keys(Keys.ESCAPE).perform()
        time.sleep(1)  # 잠깐 대기


        image_urls = []
        try:
            while True:
                # 현재 이미지 URL 추출
                img_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div._aagv img"))
                )
                img_url = img_element.get_attribute("src")
                image_urls.append(img_url)

                # 다음 버튼 클릭 시도
                try:
                    next_button = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='다음']"))
                    )
                    next_button.click()
                    time.sleep(1)  # 이미지 로딩 대기
                except:
                    print("더 이상 다음 버튼이 없음.")
                    break

        except Exception as e:
            print("이미지 URL을 찾는 중 에러 발생:", e)

        # 중복 제거 + 순서 유지
        unique_image_urls = list(OrderedDict.fromkeys(image_urls))

        try:
            like_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//span[contains(text(), '좋아요')]"))
            )
            text = like_element.text  # 예: "좋아요 66.7만개" 또는 "좋아요 421개"
            print("전체 텍스트:", text)

            # 정규표현식으로 '좋아요'와 '개'를 제거하고 숫자만 추출
            match = re.search(r"좋아요\s*([\d.,]+[만]?)개", text)
            if not match:
                match = re.search(r"좋아요\s*([\d,]+)개", text)

            if match:
                like_count = match.group(1)
            else:
                print("좋아요 수를 찾을 수 없음")
        
        except Exception as e:
            print("좋아요 수를 찾는 중 에러 발생:", e)

        try:
            time_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//time"))
            )
            time_text = time_element.get_attribute("datetime")
            
            # UTC 시간 → datetime 객체로 파싱
            utc_time = datetime.strptime(time_text, "%Y-%m-%dT%H:%M:%S.000Z")
            
            # KST로 변환 (UTC + 9시간)
            kst_time = utc_time + timedelta(hours=9)

            # 보기 좋게 출력
            formatted_time = kst_time.strftime("%Y년 %m월 %d일 %p %I시 %M분 %S초")

        except Exception as e:
            print("게시물 시간을 찾는 중 에러 발생:", e)
        print(unique_image_urls)
        return unique_image_urls, like_count, formatted_time

    except Exception as e:
        print(f"검색 에러 : {e}")
    

def get_naver_info(user, post):
    # 글로벌 드라이버 사용
    options = Options()
    options.add_argument("--start-fullscreen")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu") 

    # WebDriver Manager를 이용해 ChromeDriver 자동 관리
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(f"https://blog.naver.com/{user}/{post}")
        time.sleep(5)

        try:
            # iframe 전환
            WebDriverWait(driver, 10).until(
                EC.frame_to_be_available_and_switch_to_it((By.ID, "mainFrame"))
            )

        except Exception as e:
            print("iframe 찾기 실패:", e)


        try:
            # 제목 찾기 (XPath로)
            title_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "/html/body/div[7]/div[1]/div[2]/div[2]/div[2]/div[1]/div[1]/div/div[8]/div[1]/div/table[2]/tbody/tr/td[2]/div[1]/div/div[1]/div/div/div[2]/div/p/span"))
            )
            title = title_element.text
            print("제목:", title)

        except Exception as e:
            print("제목을 찾는 중 에러 발생:", e)


        try:
            # 본문이 들어있는 컨테이너 찾기
            main_container = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "se-main-container"))
            )

            # p 태그 텍스트들만 추출
            paragraphs = main_container.find_elements(By.TAG_NAME, "p")
            content = "\n".join(p.text for p in paragraphs if p.text.strip() != "")

            print("본문 내용:\n", content)

        except Exception as e:
            print("본문을 찾는 중 에러 발생:", e)


        try:
            heart_container = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, f"area_sympathy{post}"))
            )

            paragraphs = heart_container.find_elements(By.TAG_NAME, "em")

            # 숫자만 추출 (숫자로 변환 가능한 텍스트만 필터링)
            like = "\n".join(
                p.text for p in paragraphs if p.text.strip().isdigit()
            )

            print("공감 수:", like)

        except Exception as e:
            print("공감 수를 찾는 중 에러 발생:", e)


        try:
            # 본문이 들어있는 컨테이너 찾기
            comment_container = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "commentCount"))
            )

            print("댓글 수 :\n", comment_container.text)
            comment = comment_container
        except Exception as e:
            print("댓글 수를 찾는 중 에러 발생:", e)


        return title, content, like, comment

        


    except Exception as e:
        print(f"검색 에러 : {e}")
    


if __name__=="__main__":
    user= "tpals213"
    post = "223824990635"
    get_naver_info(user, post)