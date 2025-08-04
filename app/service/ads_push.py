# app/service/fcm.py
import json
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request

SERVICE_ACCOUNT_FILE = "../static/auth/mypuapp.json"
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
