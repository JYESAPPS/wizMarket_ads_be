import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles
from app.api.endpoints import (
    ads, ads_test, ads_notice, ads_user, ads_login, ads_app, ads_plan, 
    ads_ticket, ads_token_purchase, ads_push, ads_reserve, ads_faq, cms, help, admin,
    auth_name, play_store_test, concierge, concierge_auto_upload
)
from app.api.endpoints import webhook

# 예약 설정
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import pytz  # 시간대 고려
from app.service.ads_push import select_user_id_token


app = FastAPI()
scheduler = BackgroundScheduler(timezone="Asia/Seoul")


load_dotenv()

# CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_ROOT = os.getenv("STATIC_ROOT")
UPLOAD_ROOT = os.getenv("UPLOAD_ROOT")
POSTING_ROOT = os.getenv("POSTING_ROOT")


app.mount("/static",  StaticFiles(directory="app/static"),  name="static")   # 예전처럼
app.mount("/uploads", StaticFiles(directory=UPLOAD_ROOT),  name="uploads")  # env 사용
app.mount("/posting", StaticFiles(directory="app/posting"), name="posting") # 예전처럼



@app.get("/")
def root():
    return {"message": "FastAPI with Scheduler"}


def push_test_job():
    now = datetime.now(pytz.timezone("Asia/Seoul"))
    print(f"[{now.strftime('%H:%M:%S')}] 예약 테스트 실행됨!")


def as_bool(v: str, default=False):
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "y", "on")

ENABLE_SCHEDULER = as_bool(os.getenv("ENABLE_SCHEDULER"), False)
PUSH_ENABLED     = as_bool(os.getenv("PUSH_ENABLED"), False)


@app.on_event("startup")
def start_scheduler():
    print("✅ FastAPI startup")
    print(f"ENABLE_SCHEDULER={ENABLE_SCHEDULER}, PUSH_ENABLED={PUSH_ENABLED}")

    if not ENABLE_SCHEDULER:
        print("⏭️ Scheduler disabled (ENABLE_SCHEDULER=false)")
        return

    # 매 분 실행
    scheduler.add_job(
        select_user_id_token,
        CronTrigger(minute="*", timezone="Asia/Seoul"),
        id="push_job",
        replace_existing=True,
    )
    if not scheduler.running:
        scheduler.start()
    print("✅ APScheduler 시작됨 (push_job 등록)")


@app.on_event("shutdown")
def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        print("🛑 APScheduler 중지됨")


app.include_router(ads.router, prefix="/back/ads")
app.include_router(ads_test.router, prefix="/back/ads")
app.include_router(ads_notice.router, prefix="/back/ads")
app.include_router(ads_login.router, prefix="/back/ads")
app.include_router(ads_user.router, prefix="/back/ads")
app.include_router(ads_app.router, prefix="/back/ads")
app.include_router(ads_plan.router, prefix="/back/plan")
app.include_router(ads_ticket.router, prefix="/back/ticket")
app.include_router(ads_token_purchase.router, prefix="./back/token")
app.include_router(ads_push.router, prefix="/back/push")
app.include_router(ads_reserve.router, prefix="/back/reserve")
app.include_router(ads_faq.router, prefix="/back/faq")
app.include_router(cms.router, prefix="/back/cms")
app.include_router(webhook.router, prefix="/back/ad")
app.include_router(help.router, prefix="/back/help")
app.include_router(auth_name.router, prefix="/back")
app.include_router(play_store_test.router, prefix="/back")
app.include_router(concierge.router, prefix="/back")
app.include_router(concierge_auto_upload.router, prefix="/back")
app.include_router(admin.router, prefix="/back")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app", host="0.0.0.0", port=8002, reload=True, reload_dirs=["."]
    )
