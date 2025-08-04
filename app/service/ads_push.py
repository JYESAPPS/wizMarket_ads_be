# app/service/fcm.py
import json
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request
import os
from  app.crud.ads_push import (
    select_user_id_token as crud_select_user_id_token,
    is_user_due_for_push
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_FILE = os.path.normpath(
    os.path.join(BASE_DIR, "../static/auth/mypushapp.json")
)
SCOPES = ["https://www.googleapis.com/auth/firebase.messaging"]
PROJECT_ID = "mypushapp-2af63"  # 예: mypushapp-abc123
FCM_ENDPOINT = f"https://fcm.googleapis.com/v1/projects/{PROJECT_ID}/messages:send"

def get_access_token():
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    credentials.refresh(Request())
    return credentials.token

def send_push_fcm_v1(device_token: str, title: str, body: str):
    access_token = get_access_token()

    message = {
        "message": {
            "token": device_token,
            "notification": {
                "title": title,
                "body": body
            }
        }
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; UTF-8",
    }

    response = requests.post(
        FCM_ENDPOINT,
        headers=headers,
        data=json.dumps(message)
    )

    return response.status_code, response.json()



def select_user_id_token():
    print("매분 실행")
    user_id_token = crud_select_user_id_token()

    for user in user_id_token:
        user_id = user.user_id
        device_token = user.device_token

        if not device_token:
            continue  # 디바이스 토큰이 없는 경우 건너뜀

        # 예약 조건 일치 여부 확인
        if is_user_due_for_push(user_id):
            print(f"📨 푸시 전송 대상: user_id={user_id}")
            send_push_fcm_v1(
                device_token=device_token,
                title="[예약 알림]",
                body="지금 홍보를 시작해보세요!"
            )


    # return user_id_token