from fastapi import (
    APIRouter, UploadFile, File, Form, HTTPException, status
)
import logging

from app.service.ads_faq import (
    get_faq as service_get_faq,
    get_tag as service_get_tag,
    create_faq as service_create_faq
)
from app.schemas.ads_faq import (
    AdsFAQCreateRequest
)

router = APIRouter()
logger = logging.getLogger(__name__)



# FAQ 목록 가져오기
@router.get("")
def get_faq():
    try:
        faq = service_get_faq()

        # JSON 형태로 반환
        return faq

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {"success": False, "message": "서버 오류가 발생했습니다."}



# FAQ 태그 목록 가져오기
@router.get("/tag")
def get_tag():
    try:
        tag = service_get_tag()

        # JSON 형태로 반환
        return tag

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {"success": False, "message": "서버 오류가 발생했습니다."}


# FAQ 등록
@router.post("/create", status_code=201)
def create_faq(request: AdsFAQCreateRequest):
    try:
        service_create_faq(request)
        return {"success": True, "message": "공지사항이 등록되었습니다."}
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {"success": False, "message": "서버 오류가 발생했습니다."}