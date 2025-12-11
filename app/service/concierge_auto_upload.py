import os
import base64
from uuid import uuid4
from  app.crud.concierge_auto_upload import (
    get_concierge_user_with_store as crud_get_concierge_user_with_store
)





UPLOAD_ROOT = "/app/uploads"  # 이미 쓰던 값
UPLOAD_PUBLIC_BASE_URL = os.getenv("UPLOAD_PUBLIC_BASE_URL", "https://your-domain.com/uploads")

IG_USER_ID = os.getenv("IG_USER_ID")
IG_ACCESS_TOKEN = os.getenv("IG_LONG_LIVED_TOKEN")


def save_history_image_from_base64(user_id: int, image_b64: str) -> str:
    """
    origin_image[0] 같은 base64 문자열을 받아
    /app/uploads/concierge/user_{user_id}/history 에 저장하고
    DB에 넣을 상대 경로(예: concierge/user_13/history/abc123.jpg)를 반환
    """

    # data URL 형태일 경우 "data:image/png;base64,..." 앞부분 제거
    if image_b64.startswith("data:"):
        image_b64 = image_b64.split(",", 1)[1]

    # base64 디코딩
    binary = base64.b64decode(image_b64)

    # 디렉토리 생성
    user_history_dir = os.path.join(
        UPLOAD_ROOT, "concierge", f"user_{user_id}", "history"
    )
    os.makedirs(user_history_dir, exist_ok=True)

    # 파일명
    filename = f"{uuid4().hex}.jpg"
    save_path = os.path.join(user_history_dir, filename)

    # 실제 파일 쓰기
    with open(save_path, "wb") as f:
        f.write(binary)

    # DB에 저장할 상대 경로
    storage_path = os.path.join(
        "concierge", f"user_{user_id}", "history", filename
    ).replace("\\", "/")

    return storage_path


def build_public_image_url(storage_path: str) -> str:
    """
    DB에 저장된 상대 경로를 인스타에서 쓸 수 있는 절대 URL로 변환
    예: "concierge/user_13/history/abc.jpg"
      -> "https://your-domain.com/uploads/concierge/user_13/history/abc.jpg"
    """
    base = UPLOAD_PUBLIC_BASE_URL.rstrip("/")
    return f"{base}/{storage_path.lstrip('/')}"



def get_concierge_user_with_store(user_id):
    return crud_get_concierge_user_with_store(user_id)


