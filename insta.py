# insta_crawler.py
import sys
import json
from playwright.sync_api import sync_playwright

def get_insta_stats(insta_account: str):
    url = f"https://www.instagram.com/{insta_account}/"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url, timeout=10000)
        page.wait_for_selector("ul", timeout=5000)

        ul = page.query_selector("ul")
        posts_el = ul.query_selector("li:nth-child(1) > div > button > span > span > span")
        followers_el = ul.query_selector("li:nth-child(2) > div > button > span > span > span")
        following_el = ul.query_selector("li:nth-child(3) > div > button > span > span > span")

        result = {
            "posts": posts_el.inner_text().strip() if posts_el else "0",
            "followers": followers_el.inner_text().strip() if followers_el else "0",
            "following": following_el.inner_text().strip() if following_el else "0",
        }

        print(json.dumps(result))  # stdout으로 출력
        browser.close()

# if __name__ == "__main__":
#     if len(sys.argv) < 2:
#         print("Usage: python insta_crawler.py insta_id", file=sys.stderr)
#         sys.exit(1)

#     insta_id = sys.argv[1]
#     get_insta_stats(insta_id)
if __name__ == "__main__":
    insta_id = sys.argv[1] if len(sys.argv) >= 2 else "smjang_1995"
    get_insta_stats(insta_id)