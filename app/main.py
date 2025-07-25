import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles
from app.api.endpoints import ads, ads_test, ads_notice, ads_user, ads_login, ads_app, ads_plan, ads_ticket
from app.api.endpoints import webhook

app = FastAPI()

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
async def read_root():
    return {"message": "Welcome to FastAPI!"}



app.include_router(ads.router, prefix="/ads")
app.include_router(ads_test.router, prefix="/ads")
app.include_router(ads_notice.router, prefix="/ads")
app.include_router(ads_login.router, prefix="/ads")
app.include_router(ads_user.router, prefix="/ads")
app.include_router(ads_app.router, prefix="/ads")
app.include_router(ads_plan.router, prefix="/plan")
app.include_router(ads_ticket.router, prefix="/ticket")
app.include_router(webhook.router, prefix="/ad")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app", host="0.0.0.0", port=8002, reload=True, reload_dirs=["."]
    )
