import os, shutil, tempfile
from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
from app.schemas.ads_user import (
    UserRegisterRequest, StoreMatch, StoreAddInfo,
)

from app.service.ads_user import (
    check_user_id as service_check_user_id,
    register_user as service_register_user,
    get_store as service_get_store,
    register_store_info as service_register_store_info,
    read_ocr as service_read_ocr,
    _extract_biz_fields as service_extract_biz_fields,
)


router = APIRouter()


@router.get("/check/id")
def check_user_id(user_id: str):
    try:
        exists = service_check_user_id(user_id)
        return {"available": not bool(exists)}
    except Exception as e:
        print(f"중복 검사 오류: {e}")
        return {"available": False}


@router.post("/register/user")
def register_user(request: UserRegisterRequest):
    try:
        service_register_user(request.user_id, request.password)
        
        return {"success": True}

    except Exception as e:
        print(f"회원가입 오류: {e}")
        return {"success": False, "message": "서버 오류"}
    
# 본인인증 후 user_info 적용 여기로 데려올까 (현재 ads_login에 있음)

# 매장 정보 검색 : 있으면 목록 반환, 없으면 null 반환
@router.post("/store/match")
def match_store(request: StoreMatch):
    try: 
        store_name = request.store_name
        road_name = request.road_name

        store_info = service_get_store(store_name, road_name)

        if not store_info:
            return None

        return store_info
    except Exception as e:
        print(f"중복 검사 오류: {e}")
        return {"available": False}


# 기존 매장 추가 정보 처리
@router.post("/store/register")
def register_store_info(request: StoreAddInfo):
    try: 
        success = service_register_store_info(request)

        return success
    except Exception as e:
        print(f"매장 정보 등록 오류: {e}")
        return {"available": False}


# OCR로 사업자등록증에서 정보 뽑기
@router.post("/store/ocr")
async def get_ocr(file: UploadFile = File(...)):
    content = await file.read()
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg", ".webp", ".pdf"}:
        raise HTTPException(status_code=400, detail="PDF 또는 이미지 파일만 업로드 가능합니다.")
        
    api_key = os.getenv("GOOGLE_OCR_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing env GOOGLE_OCR_KEY")
        
    try:
        text = service_read_ocr(
            file_bytes=content,
            filename=file.filename or "",
            api_key=api_key,
        )

        fields = service_extract_biz_fields(text)

        return JSONResponse(status_code=200, content=fields)

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR failed: {e}")