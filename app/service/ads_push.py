import json
from typing import List
from fastapi import logger
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request
import os
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.crud.ads_push import (
    select_user_id_token as crud_select_user_id_token,
    is_user_due_for_push,
    select_recent_id_token as crud_select_recent_id_token,
    select_notice_target as crud_select_notice_target,
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
    user_id_token = crud_select_recent_id_token()

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

CONCURRENCY   = int(os.getenv("PUSH_CONCURRENCY", "30"))  # 동시 요청 개수

def select_notice_target(
    notice_id: int,
    notice_title: str,
    notice_content: str,
    notice_file: str | None = None,
):
    try:
        targets: List[str] = crud_select_notice_target()

        # (선택) 너무 긴 본문은 잘라서 전송
        safe_title = _truncate_for_fcm(notice_title, 128)
        safe_body  = _truncate_for_fcm(notice_content, 1024)

        # for token in targets:
        #     if not token:
        #         continue
            
        #     send_push_fcm_v1(
        #         device_token=token,
        #         title=safe_title,
        #         body=safe_body
        #     )

        # 병렬 핵심: 유효 토큰만 중복 제거 후 스레드 풀에 제출
        uniq = list(dict.fromkeys(t for t in targets if t))

        with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
            futs = [
                ex.submit(
                    send_push_fcm_v1,
                    device_token=tkn,
                    title=safe_title,
                    body=safe_body,
                )
                for tkn in uniq
            ]
            # 완료되며 예외만 흡수(전체 진행은 계속)
            for fut in as_completed(futs):
                try:
                    fut.result()
                except Exception as e:
                    logger.warning(f"[notice push] one token failed: {e}")
    except Exception:
        logger.exception("notice push batch failed")


# FCM 전체 메시지 4KB 제한 감안해 notification body는 너무 길지 않게 절단
def _truncate_for_fcm(text: str, limit: int = 1024) -> str:
    if not text:
        return ""
    return text if len(text) <= limit else (text[:limit-1] + "…")