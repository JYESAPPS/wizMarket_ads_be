import subprocess
from fastapi import FastAPI, Request, HTTPException
from fastapi import (
    APIRouter, HTTPException
)

router = APIRouter()
SECRET = "key"

@router.post("/webhook")
async def git_webhook(request: Request):
    # 1. Webhook 서명 검증 (GitHub의 경우)
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")
    
    # TODO: 서명 검증 로직 추가 (선택 사항)
    
    # 2. 요청 처리
    payload = await request.json()
    if "ref" in payload and payload["ref"] == "refs/heads/main":  # main 브랜치 확인
        try:
            # 3. Git Pull 명령 실행
            subprocess.run(["git", "pull"], check=True)
            return {"status": "success", "message": "Repository updated"}
        except subprocess.CalledProcessError as e:
            raise HTTPException(status_code=500, detail=f"Git pull failed: {e}")
    return {"status": "ignored", "message": "Not a push to the main branch"}
