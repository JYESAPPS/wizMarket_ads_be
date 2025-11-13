import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles
from app.api.endpoints import (
    ads, ads_test, ads_notice, ads_user, ads_login, ads_app, ads_plan, ads_ticket, ads_push, ads_reserve, ads_faq, cms, help, admin,
    auth_name, play_store_test, concierge
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


app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/uploads", StaticFiles(directory="app/uploads"), name="uploads")
app.mount("/posting", StaticFiles(directory="app/posting"), name="posting")



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


app.include_router(ads.router, prefix="/ads")
app.include_router(ads_test.router, prefix="/ads")
app.include_router(ads_notice.router, prefix="/ads")
app.include_router(ads_login.router, prefix="/ads")
app.include_router(ads_user.router, prefix="/ads")
app.include_router(ads_app.router, prefix="/ads")
app.include_router(ads_plan.router, prefix="/plan")
app.include_router(ads_ticket.router, prefix="/ticket")
app.include_router(ads_push.router, prefix="/push")
app.include_router(ads_reserve.router, prefix="/reserve")
app.include_router(ads_faq.router, prefix="/faq")
app.include_router(cms.router, prefix="/cms")
app.include_router(webhook.router, prefix="/ad")
app.include_router(help.router, prefix="/help")
app.include_router(auth_name.router)
app.include_router(play_store_test.router)
app.include_router(concierge.router)
app.include_router(admin.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app", host="0.0.0.0", port=8002, reload=True, reload_dirs=["."]
    )
