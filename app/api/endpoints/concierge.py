from fastapi import APIRouter, HTTPException, status, UploadFile, File, Request, Query, Form
from fastapi.responses import JSONResponse
from typing import List, Dict, Optional, Any
import logging
import os
from typing import List
from datetime import datetime
from fastapi import UploadFile, File, Request
from io import BytesIO
import base64
from datetime import datetime, timezone, timedelta
import asyncio

from app.schemas.concierge import (
    IsConcierge, AddConciergeStore, ConciergeUploadRequest, ConciergeExcelUploadRequest, ConciergeDeleteRequest
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
    update_concierge as service_update_concierge,
)
from app.service.ads import (
    select_ads_init_info as service_select_ads_init_info,
    random_design_style as service_random_design_style,
    select_ai_age as service_select_ai_age,
    select_ai_data as service_select_ai_data,
)
from app.service.ads_app import (
    get_style_image as service_get_style_image,
)
from app.service.ads_generate import (
    generate_content as service_generate_content,
)
from app.service.ads_app import (
    generate_by_seed_prompt as service_generate_by_seed_prompt,
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

    created_count = 0

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






# ==================================================================
# 🔥 1) 병렬로 돌릴 “개별 매장 처리 함수”
# ==================================================================

# --- 하드코딩 리스트 ---
user_id_list = [1, 7]
store_business_number_list = ["JS0079", "JS0081"]
menu_list = ["초밥", "찜닭"]
road_name_list = ["경기도 안양시 동안구 평의길 8", "충청남도 금산군 금산읍 삼풍로 19"]
KST = timezone(timedelta(hours=9))


async def process_user_task(idx: int):
    """
    idx 번째 user 데이터로
    - init_data
    - 문구 생성
    - 이미지 생성
    전부 수행해서 dict 로 결과 반환하는 함수
    """

    
    user_id = user_id_list[idx]
    store_business_number = store_business_number_list[idx]
    menu_1 = menu_list[idx]
    road_name = road_name_list[idx]

    # ------------------------------
    # 1) 초기 정보 로딩
    # ------------------------------
    try:
        init_data = service_select_ads_init_info(store_business_number)
        ai_age = service_select_ai_age(init_data, menu_1)
        ai_data = service_select_ai_data(init_data, ai_age, menu_1)
        random_image_list = service_random_design_style(init_data, ai_data[0])
    except Exception:
        return {"user_id": user_id, "error": "기본 정보 불러오기 오류"}

    style_number = ai_data[0]
    channel_number = ai_data[2]
    title_number = ai_data[3]

    today = datetime.now(KST)

    # ------------------------------
    # 2) 채널 텍스트 처리
    # ------------------------------
    channel_text = {
        1: "카카오톡",
        2: "인스타그램 스토리",
        3: "인스타그램 피드 게시글",
        4: "블로그",
        5: "문자메시지",
        6: "네이버밴드",
        7: "X(트위터)",
    }.get(channel_number, "")

    theme = {1: "매장홍보", 2: "상품소개"}.get(title_number, "이벤트")

    # ------------------------------
    # 3) 문구 생성
    # ------------------------------
    try:
        copyright_role = """
            당신은 인스타그램, 블로그 등 소셜미디어 광고 전문가입니다.
        """

        # 이벤트이면 기념일 룰 적용
        if title_number == 3:
            copyright_prompt = f"""
                {init_data.store_name} 매장의 {channel_text} 이벤트 문구 생성.
                오늘 날짜는 {today}.
                ...
                (기념일 규칙 생략)
            """
        else:
            copyright_prompt = f"""
                {init_data.store_name} 매장의 {channel_text} 광고 문구 생성.
                세부 업종 : {menu_1}
                홍보 컨셉 : {theme}
                지역 : {road_name}
            """

        copyright = service_generate_content(
            copyright_prompt, copyright_role, ""
        )

    except Exception:
        return {"user_id": user_id, "error": "문구 생성 오류"}

    # ------------------------------
    # 4) 이미지 생성
    # ------------------------------
    seed_prompt = random_image_list.prompt

    try:
        origin_image = service_generate_by_seed_prompt(
            channel_number,
            copyright,
            "",
            seed_prompt,
            menu_1
        )

        # Base64 변환
        output_images = []
        for image in origin_image:
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            buffer.seek(0)
            output_images.append(
                base64.b64encode(buffer.getvalue()).decode("utf-8")
            )

    except Exception as e:
        return {"user_id": user_id, "error": f"이미지 생성 오류: {str(e)}"}

    # ------------------------------
    # 5) 최종 결과 반환
    # ------------------------------
    return {
        "user_id": user_id,
        "copyright": copyright,
        "origin_image": output_images,
        "title": title_number,
        "channel": channel_number,
        "style": style_number,
        "core_f": ai_age,
        "main": init_data.main,
        "temp": init_data.temp,
        "detail_category_name": init_data.detail_category_name,
        "register_tag": menu_1,
        "store_name": init_data.store_name,
        "road_name": init_data.road_name,
        "store_business_number": store_business_number,
        "prompt": seed_prompt,
    }


# ==================================================================
# 🔥 2) test_interval() → 병렬 처리 적용
# ==================================================================
@router.post("/test/interval1")
async def test_interval():
    """
    모든 user_id를 병렬 처리로 돌리고
    결과를 배열로 반환.
    """
    tasks = []

    # 유저 수만큼 task 생성
    for idx in range(len(user_id_list)):
        tasks.append(process_user_task(idx))

    # 병렬 실행
    results = await asyncio.gather(*tasks)

    # 최종 응답
    return JSONResponse(content={
        "count": len(results),
        "results": results,
    })
