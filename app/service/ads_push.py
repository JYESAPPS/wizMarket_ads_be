import json
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request
import os
from app.crud.ads_push import (
    select_user_id_token as crud_select_user_id_token,
    is_user_due_for_push
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_FILE = os.path.normpath(
    os.path.join(BASE_DIR, "../static/auth/mypushapp.json")
)
SCOPES = ["https://www.googleapis.com/auth/firebase.messaging"]
PROJECT_ID = "mypushapp-2af63"
FCM_ENDPOINT = f"https://fcm.googleapis.com/v1/projects/{PROJECT_ID}/messages:send"


def get_access_token():
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        credentials.refresh(Request())
        return credentials.token
    except Exception as e:
        print("❌ AccessToken 획득 실패:", e)
        return None


FN_BASE = "https://asia-northeast1-wizad-b69ee.cloudfunctions.net"  # 외주 제공

def send_push_fcm_v1(device_token: str, title: str, body: str):
    try:
        url = f"{FN_BASE}/sendPush"   # 외주 코드의 path와 동일하게
        payload = {"token": device_token, "title": title, "body": body}
        headers = {"Content-Type": "application/json"}
        # 필요 시 보안 헤더도 추가:
        # headers["x-webpush-secret"] = os.getenv("WEBPUSH_SECRET", "")

        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        text = resp.text or ""
        try:
            data = resp.json()
        except Exception:
            data = {"raw": text[:500]}

        return resp.status_code, data
    except Exception as e:
        return 500, {"error": str(e)}


def select_user_id_token():
    user_id_token = crud_select_user_id_token()

    for user in user_id_token:
        user_id = user.user_id
        device_token = user.device_token

        if not device_token:
            continue

        if is_user_due_for_push(user_id):
            send_push_fcm_v1(
                device_token=device_token,
                title="[예약 알림]",
                body="지금 홍보를 시작해보세요!"
            )
