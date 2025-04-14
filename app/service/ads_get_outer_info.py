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
        driver.get(f"https://www.instagram.com/{user}/")
        time.sleep(5)

        # ESC 키 누르기 (예: 로그인 팝업 닫기)
        actions = ActionChains(driver)
        actions.send_keys(Keys.ESCAPE).perform()
        time.sleep(1)  # 잠깐 대기

        try:
            post_element = driver.find_element(By.CSS_SELECTOR, f'a[href="/{user}/p/{post}/"]')

            # 마우스를 해당 게시물 위로 이동
            actions.move_to_element(post_element).perform()
            time.sleep(3)  # 3초 대기 (호버 효과 보기 위해)

            # hover 이후 등장하는 div 내 span 정보 추출
            hover_info_div = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//div[contains(@style, "background: rgba(0, 0, 0, 0.7)")]')
                )
            )

            # 그 안에 있는 모든 숫자 span 찾기
            spans = hover_info_div.find_elements(By.XPATH, './/span/span')

            # span 안의 텍스트 출력 (좋아요, 댓글 순서로 있다고 가정)
            likes = spans[0].text if len(spans) > 0 else None
            comments = spans[1].text if len(spans) > 1 else None

            print("❤️ 좋아요 수:", likes)
            print("💬 댓글 수:", comments)
        
        except Exception as e:
            print("댓글 수를 찾는 중 에러 발생:", e)

        return likes, comments

    except Exception as e:
        print(f"검색 에러 : {e}")


def get_insta_reel_info(user, post):
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
        driver.get(f"https://www.instagram.com/{user}/reels/")
        time.sleep(5)

        # ESC 키 누르기 (예: 로그인 팝업 닫기)
        actions = ActionChains(driver)
        actions.send_keys(Keys.ESCAPE).perform()
        time.sleep(1)  # 잠깐 대기

        try:
            post_element = driver.find_element(By.CSS_SELECTOR, f'a[href="/{user}/reel/{post}/"]')

            # 마우스를 해당 게시물 위로 이동
            actions.move_to_element(post_element).perform()
            time.sleep(3)  # 3초 대기 (호버 효과 보기 위해)

            # hover 이후 등장하는 div 내 span 정보 추출
            hover_info_div = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//div[contains(@style, "background: rgba(0, 0, 0, 0.7)")]')
                )
            )

            # 그 안에 있는 모든 숫자 span 찾기
            spans = hover_info_div.find_elements(By.XPATH, './/span/span')

            # span 안의 텍스트 출력 (좋아요, 댓글 순서로 있다고 가정)
            likes = spans[0].text if len(spans) > 0 else None
            comments = spans[1].text if len(spans) > 1 else None

            print("❤️ 좋아요 수:", likes)
            print("💬 댓글 수:", comments)
        
        except Exception as e:
            print("댓글 수를 찾는 중 에러 발생:", e)

        return likes, comments

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


        return like, comment

    except Exception as e:
        print(f"검색 에러 : {e}")
    


if __name__=="__main__":
    user= "xxxibgdrgn"
    post = "DGmlIjkvV9g"
    # get_naver_info(user, post)
    get_insta_info(user, post)
