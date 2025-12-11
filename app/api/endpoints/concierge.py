from fastapi import APIRouter, HTTPException, status, UploadFile, File, Request, Query, Form
from fastapi.responses import JSONResponse
from typing import List, Dict, Optional, Any
import logging
import os
from typing import List
from fastapi import UploadFile, File, Request


from app.schemas.concierge import (
    IsConcierge, ConciergeExcelUploadRequest, ConciergeDeleteRequest
) 
from app.service.concierge import (
    is_concierge as service_is_concierge,
    submit_concierge as service_submit_concierge,
    select_concierge_list as service_select_concierge_list,
    get_concierge_system_list as service_get_concierge_system_list,
    select_concierge_detail as service_select_concierge_detail,
    get_report_store as service_get_report_store,
    concierge_add_new_store as service_concierge_add_new_store,
    submit_concierge_excel as service_submit_concierge_excel,
    delete_concierge_user as service_delete_concierge_user,
    reserve_schedule as service_reserve_schedule,
    update_concierge as service_update_concierge,
    select_history_list as service_select_history_list,
)
from app.service.ads_generate import (
    generate_content as service_generate_content,
)


router = APIRouter()
logger = logging.getLogger(__name__)


# 존재 여부
@router.post("/is/concierge/store")
def check_concierge(request: IsConcierge):
    exists = not service_is_concierge(request)  # True면 이미 등록됨
    if exists:
        return {"success": False, "message": "이미 등록 된 컨시어지 매장입니다."}
    return {"success": True, "message": ""}


# 신청
UPLOAD_DIR = "uploads/concierge"  # 원하는 경로로 바꿔도 됨
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/submit/concierge")
async def submit_concierge(
    request: Request,
    images: List[UploadFile] = File(None),
):
    form = await request.form()

    # 1) 일반 필드 뽑기
    fields = {}
    from starlette.datastructures import UploadFile as StarletteUploadFile
    for key, value in form.items():
        if isinstance(value, (UploadFile, StarletteUploadFile)):
            continue
        fields[key] = value

    # 2) 서비스에 fields + 이미지 원본 그대로 넘김
    success, msg = await service_submit_concierge(fields, images or [])

    return {
        "success": success,
        "msg": msg,
    }


# 리스트 + 검색 조회
@router.get("/select/concierge/list")
def get_concierge_list(
    keyword: str | None = Query(None),
    search_field: str | None = Query(None),
    status: str | None = Query(None),
    apply_start: str | None = Query(None),
    apply_end: str | None = Query(None),
):
    rows = service_select_concierge_list(
        keyword=keyword,
        search_field=search_field,
        status=status,
        apply_start=apply_start,
        apply_end=apply_end,
    )
    return {"items": rows}



# 시스템용 리스트 조회
@router.get("/select/concierge/system/list")
def get_concierge_system_list():
    rows = service_get_concierge_system_list()
    return {"items": rows}




# 상세 페이지
@router.get("/select/concierge/detail/{user_id}")
def select_concierge_detail(user_id: int) -> Dict[str, Any]:
    """
    컨시어지 신청 상세 조회
    - 프론트: /admin/concierge/:id 에서 사용
    """
    detail = service_select_concierge_detail(user_id)
    return detail



# 엑셀 파일 제출
@router.post("/concierge/submit/excel")
def submit_concierge_excel(request: ConciergeExcelUploadRequest):
    if not request.rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="rows가 비어 있습니다.",
        )

    result = service_submit_concierge_excel(request.rows)
    return result




# 삭제 요청
@router.post("/concierge/delete")
def delete_concierge_user(request: ConciergeDeleteRequest):
    if not request.ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ids가 비어 있습니다.",
        )

    result = service_delete_concierge_user(request.ids)

    if not result.get("success"):
        # 서비스에서 메시지 리턴한 경우
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("message", "컨시어지 삭제 중 오류가 발생했습니다."),
        )

    return result

# 승인 처리
@router.post("/concierge/approve/{concierge_id}")
async def update_concierge_status(
    concierge_id: int,
    status: str = Form(...),          # APPROVED / PENDING 등

    # 기본 정보
    user_name: str = Form(""),
    phone: str = Form(""),
    memo: str = Form(""),

    # 가게 정보
    store_name: str = Form(""),
    road_name: str = Form(""),

    # 메뉴
    menu_1: str = Form(""),
    menu_2: str = Form(""),
    menu_3: str = Form(""),

    # 업종 코드 (승인 상태에서는 프론트가 기존값을 그대로 담아서 보냄)
    main_category_code: Optional[str] = Form(None),
    sub_category_code: Optional[str] = Form(None),
    detail_category_code: Optional[str] = Form(None),

    # 삭제할 파일 id 들 (FormData에 여러 번 넣기: removed_file_ids=1, removed_file_ids=2 ...)
    removed_file_ids: List[int] = Form([]),

    # 새 파일들
    new_files: List[UploadFile] = File([]),
):
    
    try:
    # 기존 매장 조회
        store_business_number = service_get_report_store(store_name, road_name)
    except Exception as e:
        return {
            "messeage" : "매장 조회 오류"
        }

    try:
    # 매장 없을 시 DB 복사
        if not store_business_number :
            result = service_concierge_add_new_store(store_name, road_name, main_category_code, sub_category_code, detail_category_code)
            store_business_number = result.get("store_business_number")

    except Exception as e:
        return {
            "messeage" : "매장 복사 오류"
        }
    

    # GPT로 스케줄링 작성
    schedule_role = """
        너는 매장 홍보 스케줄을 추천하는 어시스턴트이다.

        반드시 아래 JSON 형식 **만** 출력해라. 그 외의 설명, 문장, 코드블록, 주석, 마크다운은 절대 쓰지 마라.

        형식 예시:
        {
        "days": ["MON", "WED"],
        "time": "15:00:00"
        }

        규칙:
        - days에는 정확히 2개의 요일만 넣어라.
        - 요일은 아래 중 하나의 영문 대문자 코드를 사용해라.
        ["SUN","MON","TUE","WED","THU","FRI","SAT"]
        - time은 24시간 HH:MM:SS 형식으로, 초는 항상 "00"으로 맞춘다.
        - 오직 위 JSON 객체 한 개만 출력한다.
    """


    schedule_prompt = f"""
        매장 업종  : {menu_1}
    """

    schedule = service_generate_content(
        schedule_prompt, schedule_role, ""
    )
    service_reserve_schedule(concierge_id, schedule)

    # 수정 처리
    result = await service_update_concierge(
        concierge_id=concierge_id,
        status=status,
        user_name=user_name,
        phone=phone,
        memo=memo,
        store_business_number = store_business_number,
        main_category_code=main_category_code,
        sub_category_code=sub_category_code,
        detail_category_code=detail_category_code,
        menu_1=menu_1,
        menu_2=menu_2,
        menu_3=menu_3,
        removed_file_ids=removed_file_ids,
        new_files=new_files,
    )

    return result
    

# 수정 처리
@router.post("/concierge/update/{concierge_id}")
async def update_concierge_status(
    concierge_id: int,
    status: str = Form(...),          # APPROVED / PENDING 등

    # 기본 정보
    user_name: str = Form(""),
    phone: str = Form(""),
    memo: str = Form(""),

    # 가게 정보
    store_name: str = Form(""),
    road_name: str = Form(""),
    store_business_number: str = Form(""),

    # 메뉴
    menu_1: str = Form(""),
    menu_2: str = Form(""),
    menu_3: str = Form(""),

    # 업종 코드 (승인 상태에서는 프론트가 기존값을 그대로 담아서 보냄)
    main_category_code: Optional[str] = Form(None),
    sub_category_code: Optional[str] = Form(None),
    detail_category_code: Optional[str] = Form(None),

    # 삭제할 파일 id 들 (FormData에 여러 번 넣기: removed_file_ids=1, removed_file_ids=2 ...)
    removed_file_ids: List[int] = Form([]),

    # 새 파일들
    new_files: List[UploadFile] = File([]),
):

    result = await service_update_concierge(
        concierge_id=concierge_id,
        status=status,
        user_name=user_name,
        phone=phone,
        memo=memo,
        store_business_number = store_business_number,
        main_category_code=main_category_code,
        sub_category_code=sub_category_code,
        detail_category_code=detail_category_code,
        menu_1=menu_1,
        menu_2=menu_2,
        menu_3=menu_3,
        removed_file_ids=removed_file_ids,
        new_files=new_files,
    )

    return result



# 히스토리 조회
@router.get("/select/concierge/history/list")
def select_history_list(
    keyword: str | None = Query(None),
    search_field: str | None = Query(None),
    status: str | None = Query(None),
    apply_start: str | None = Query(None),
    apply_end: str | None = Query(None),
):
    rows = service_select_history_list(
        keyword=keyword,
        search_field=search_field,
        status=status,
        apply_start=apply_start,
        apply_end=apply_end,
    )
    return {"items": rows}


