import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# ==== .env 로드 ====
load_dotenv()


# ===== 설정값 =====
IG_USER_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")  # 환경 변수로 관리 권장
ACCESS_TOKEN = os.getenv("INSTAGRAM_TOKEN")  # 환경 변수로 관리 권장

# IG_USER_ID="17841470834511905"
# ACCESS_TOKEN="EAAMnnXg1BtMBP0gWoTPa7FmZB82PVAchaqV6yCM48z4TSfXgDSgW6lnDvkL5VKAXGpzHES3XKY0DLIJUrWVcCgYfi9VHoWxw7dPf3ImBitIZBe0ZCFj2n7mdq5pQK8eI6Oijo3o3XZB6NE5nC44sfH8rfvWyXtbFZAEKazNZCIbEy1jkA06ZAjBiz35SYdY"


IMAGE_URL = "https://i.namu.wiki/i/-58TM2X7iyob-8KdYDwcbi4gZpBrXRwn71YEPEGh8RNlWqBPISCAxHxMpWRWKljISp7YdVaD--cflN6VYqRraw.jpg"
# IMAGE_URL = "http://wizmarket.ai:8000/uploads/thumbnail/171/6/thumbnail_4_thumb.jpg"
CAPTION = "테스트 자동 포스팅입니다. #wizMarket #auto_post"


def create_media_container(ig_user_id, image_url, caption, access_token):
    """
    1단계: 이미지 컨테이너 생성
    POST https://graph.facebook.com/v18.0/{ig_user_id}/media
    """
    url = f"https://graph.facebook.com/v18.0/{ig_user_id}/media"
    payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": access_token,
    }

    resp = requests.post(url, data=payload)
    print("create_media_container status:", resp.status_code)
    print("response:", resp.text)

    resp.raise_for_status()
    data = resp.json()
    return data.get("id")  # 컨테이너 ID


def publish_media(ig_user_id, creation_id, access_token):
    """
    2단계: 컨테이너를 실제 게시물로 발행
    POST https://graph.facebook.com/v18.0/{ig_user_id}/media_publish
    """
    url = f"https://graph.facebook.com/v18.0/{ig_user_id}/media_publish"
    payload = {
        "creation_id": creation_id,
        "access_token": access_token,
    }

    resp = requests.post(url, data=payload)
    print("publish_media status:", resp.status_code)
    print("response:", resp.text)

    resp.raise_for_status()
    data = resp.json()
    return data


if __name__ == "__main__":
    if not ACCESS_TOKEN:
        raise RuntimeError("ACCESS_TOKEN(IG_LONG_LIVED_TOKEN) 환경 변수를 설정해 주세요.")

    # 1) 컨테이너 생성
    try:
        creation_id = create_media_container(
            IG_USER_ID,
            IMAGE_URL,
            CAPTION,
            ACCESS_TOKEN,
        )
        print("▶ creation_id:", creation_id)
    except Exception as e:
        print("컨테이너 생성 실패:", e)
        exit(1)

    # 2) 컨테이너 게시
    try:
        publish_result = publish_media(
            IG_USER_ID,
            creation_id,
            ACCESS_TOKEN,
        )
        print("▶ 게시 성공:", publish_result)
    except Exception as e:
        print("게시 실패:", e)
        exit(1)
