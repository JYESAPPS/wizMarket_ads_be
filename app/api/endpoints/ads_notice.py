from fastapi import (
    APIRouter, UploadFile, File, Form, HTTPException, status
)
import logging

from app.service.ads_notice import (
    get_notice as service_get_notice,
    create_notice as service_create_notice,
    get_notice_read as service_get_notice_read,
    insert_notice_read as service_insert_notice_read
)

from app.schemas.ads_notice import (
    AdsNoticeCreateRequest,
    AdsNoticeReadInsertRequest
)


router = APIRouter()
logger = logging.getLogger(__name__)


# 공지사항 목록 가져오기
@router.get("/get/notice")
def get_notice():
    try:
        notice = service_get_notice()

        # JSON 형태로 반환
        return notice

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {"success": False, "message": "서버 오류가 발생했습니다."}
    

# 공지사항 등록
@router.post("/create/notice", status_code=201)
def create_notice(request: AdsNoticeCreateRequest):
    try:
        service_create_notice(request.notice_title, request.notice_content)
        return {"success": True, "message": "공지사항이 등록되었습니다."}
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {"success": False, "message": "서버 오류가 발생했습니다."}
    

# 공지사항 해당 유저가 읽었는지 검사
@router.get("/get/notice/check/read")
def get_notice_read(user_id: str):
    try:
        data = service_get_notice_read(user_id)
        return data

    except Exception as e:
        return {"success": False, "message": "조회 중 오류 발생"}
    

# 공지사항 읽음 처리
@router.post("/notice/read")
def insert_notice_read(request: AdsNoticeReadInsertRequest):
    try:
        success = service_insert_notice_read(request.user_id, request.notice_no)
        return {"success": success}
    except Exception as e:
        print(f"읽음 처리 오류: {e}")
        return {"success": False, "message": "읽음 처리 중 오류 발생"}