from fastapi import (
    APIRouter, UploadFile, File, Form, HTTPException, status
)
import logging

from app.service.ads_faq import (
    get_faq as service_get_faq,
    get_tag as service_get_tag,
    create_faq as service_create_faq,
    update_faq as service_update_faq,
    delete_faq as service_delete_faq
)
from app.schemas.ads_faq import (
    AdsFAQCreateRequest, AdsFAQUpdateRequest, AdsFAQDeleteRequest
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
        return {"success": True, "message": "FAQ가 등록되었습니다."}
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {"success": False, "message": "서버 오류가 발생했습니다."}
    

# FAQ 수정
@router.post("/update", status_code=201)
def update_faq(request: AdsFAQUpdateRequest):
    try:
        service_update_faq(request)
        return {"success": True, "message": "FAQ가 업데이트되었습니다."}
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {"success": False, "message": "서버 오류가 발생했습니다."}
    


# FAQ 삭제
@router.post("/delete", status_code=201)
def delete_faq(request: AdsFAQDeleteRequest):
    try:
        service_delete_faq(request)
        return {"success": True, "message": "FAQ가 업데이트되었습니다."}
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {"success": False, "message": "서버 오류가 발생했습니다."}


