from fastapi import (
    APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, status, Query, Request, Response
)
import logging

from app.service.ads_notice import (
    save_notice_image as service_save_notice_image,
    get_notice as service_get_notice,
    create_notice as service_create_notice,
    update_notice as service_update_notice,
    delete_notice as service_delete_notice,
    get_notice_read as service_get_notice_read,
    insert_notice_read as service_insert_notice_read,
    notice_views as service_notice_views,
    NoticeNotFoundError,
)

from app.service.ads_push import (
    select_notice_target as service_select_notice_target, 
)

from app.schemas.ads_notice import (
    AdsNoticeCreateRequest,
    AdsNoticeUpdateRequest,
    AdsNoticeDeleteRequest,
    AdsNoticeReadInsertRequest
)


router = APIRouter()
logger = logging.getLogger(__name__)


# 공지사항 목록 가져오기
@router.get("/get/notice")
def get_notice(request: Request):
    return service_get_notice(request=request)    

# 공지사항 단건 가져오기
@router.get("/get/notice/{notice_no}")
def get_notice_by_id(notice_no: int):
    try:
        items = service_get_notice()
        for n in items:
            if n.get("notice_no") == notice_no:
                return n
        raise HTTPException(status_code=404, detail="공지사항을 찾을 수 없습니다.")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {"success": False, "message": "서버 오류가 발생했습니다."}  

# 공지사항 등록
@router.post("/create/notice", status_code=201)
async def create_notice(
    background_tasks: BackgroundTasks,
    notice_post: str = Form("Y"),
    notice_title: str = Form(...),
    notice_content: str = Form(...),
    notice_file: UploadFile | None = File(None),
):
    notice_id = None
    try:
        path = await service_save_notice_image(notice_file)
        notice_id = service_create_notice(notice_post, notice_title, notice_content, path)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {"success": False, "message": "서버 오류가 발생했습니다."}
    
    push_enqueued = True
    # try:
    #     # 공지사항 등록 푸시
    #     background_tasks.add_task(
    #         service_select_notice_target,
    #         notice_id,
    #         notice_title,
    #         notice_content,
    #         notice_file=None,
    #     )

    # except Exception as e:
    #     push_enqueued = False
    #     logger.error(f"Unexpected error: {str(e)}")
    #     return {"success": False, "message": "푸시 알림 전송에 실패했습니다."}

    return {
        "success": True,
        "message": "공지사항이 등록되었습니다.",
        "notice_id": notice_id,
        "push_enqueued": push_enqueued,
    }

# 공지사항 수정
@router.post("/edit/notice/{notice_no}", status_code=200)
async def update_notice(
    notice_no: int,
    notice_post: str = Form("Y"),
    notice_title: str = Form(...),
    notice_content: str = Form(...),
    notice_file: UploadFile | None = File(None),
    remove_file: bool = Form(False),
):
    try:
        path = await service_save_notice_image(notice_file)
        service_update_notice(notice_no, notice_post, notice_title, notice_content, new_path=path, remove_file=remove_file)
        return {"success": True, "message": "공지사항이 수정되었습니다."}
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {"success": False, "message": "서버 오류가 발생했습니다."}

# 공지사항 삭제
@router.post("/delete/notice/{notice_no}", status_code=201)
def delete_notice(notice_no: int):
    try:
        service_delete_notice(notice_no)
        return {"success": True, "message": "공지사항이 삭제되었습니다."}
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

# 공지사항 조회수
@router.post("/notice/view/{notice_no}", status_code=status.HTTP_204_NO_CONTENT)
async def notice_views(notice_no: int):
    try:
        service_notice_views(notice_no)
    except NoticeNotFoundError:
        raise HTTPException(status_code=404, detail="Notice not found")
    # 데코레이터에 204를 지정했어도, 안전하게 명시 반환
    return Response(status_code=status.HTTP_204_NO_CONTENT)