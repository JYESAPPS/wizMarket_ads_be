from fastapi import (
    APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, status, Query, Request, Response
)
import logging
from typing import List

from app.service.ads_notice import (
    save_notice_image as service_save_notice_image,
    save_notice_file as service_save_notice_file,
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
    notice_push: str = Form("Y"),
    notice_type: str = Form("일반"),
    notice_title: str = Form(...),
    notice_content: str = Form(...),
    # 하단 첨부파일(단일)
    notice_file: UploadFile | None = File(None),
    # 상단 첨부 이미지(여러 장)
    notice_images: List[UploadFile] = File([]),
):
    notice_id = None

    try:
        # 1) 단일 첨부파일 저장
        notice_file_path: str | None = None
        if notice_file is not None:
            notice_file_path = await service_save_notice_file(notice_file)

        # 2) 첨부 이미지들 저장 (모두 저장)
        image_paths: list[str] = []
        for img in notice_images:
            if not img or not img.filename:
                continue
            img_path = await service_save_notice_image(img)
            if img_path:
                image_paths.append(img_path)

        # 3) DB INSERT (파일/이미지 경로 포함)
        notice_id = service_create_notice(
            notice_post=notice_post,
            notice_type=notice_type,
            notice_title=notice_title,
            notice_content=notice_content,
            notice_file=notice_file_path,
            notice_images=image_paths,
            notice_push=notice_push,
        )

    except HTTPException:
        # 파일 검증 실패 등은 그대로 클라이언트로 전달
        raise
    except Exception as e:
        logger.error(f"Unexpected error in create_notice: {str(e)}")
        return {"success": False, "message": "서버 오류가 발생했습니다."}

    # 4) 푸시 알림 (옵션) - notice_push가 'Y'일 때만 전송
    push_enqueued = False
    if notice_push == "Y":
        try:
            background_tasks.add_task(
                service_select_notice_target,
                notice_id,
                notice_type,
                notice_title,
                notice_content,
                notice_file=None,  # 필요하면 이미지 경로도 넘기기
            )
            push_enqueued = True
        except Exception as e:
            push_enqueued = False
            logger.error(f"Unexpected error while enqueue push: {str(e)}")
            # 공지 자체는 이미 저장된 상태

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
    notice_push: str = Form("Y"),
    notice_type: str = Form("일반"),
    notice_title: str = Form(...),
    notice_content: str = Form(...),

    # 단일 첨부파일 (이미지 아닐 수도 있음)
    notice_file: UploadFile | None = File(None),
    remove_file: bool = Form(False),

    # 🔹 남겨둘 기존 첨부 이미지 목록 (JSON 문자열, 예: '["notice/a.png","notice/b.png"]')
    existing_images: str = Form("[]"),

    # 🔹 새로 추가할 첨부 이미지들 (이미지 파일)
    notice_images: List[UploadFile] = File([]),
):
    try:
        await service_update_notice(
            notice_no=notice_no,
            notice_post=notice_post,
            notice_push=notice_push,
            notice_type=notice_type,
            notice_title=notice_title,
            notice_content=notice_content,
            notice_file_upload=notice_file,
            remove_file=remove_file,
            existing_images_json=existing_images,
            notice_images_uploads=notice_images,
        )
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