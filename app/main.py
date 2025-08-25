import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles
from app.api.endpoints import (
    ads, ads_test, ads_notice, ads_user, ads_login, ads_app, ads_plan, ads_ticket, ads_push, ads_reserve, ads_faq, cms
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
scheduler = BackgroundScheduler()


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

@app.on_event("startup")
def start_scheduler():
    scheduler.add_job(
        select_user_id_token,                 # 실행할 함수
        CronTrigger(minute='*', timezone="Asia/Seoul"),  # 매 정각 매분
        id="push_job",
        replace_existing=True
    )
    scheduler.start()
    print("✅ APScheduler 시작됨")


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

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app", host="0.0.0.0", port=8002, reload=True, reload_dirs=["."]
    )
