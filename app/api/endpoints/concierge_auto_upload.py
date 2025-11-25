from fastapi import APIRouter
from fastapi.responses import JSONResponse
import logging
from datetime import datetime
from io import BytesIO
import base64
from datetime import datetime, timezone, timedelta
import asyncio
import os
from typing import Dict, List, Any
from datetime import datetime
import asyncio
from app.api.endpoints.insta_test import create_media_container, publish_media          # 네가 작성한 함수 import

UPLOAD_ROOT = "/app/uploads"  # 이미 쓰던 값
UPLOAD_PUBLIC_BASE_URL = os.getenv("UPLOAD_PUBLIC_BASE_URL", "https://your-domain.com/uploads")

IG_USER_ID = os.getenv("IG_USER_ID")
IG_ACCESS_TOKEN = os.getenv("IG_LONG_LIVED_TOKEN")

from app.service.concierge import (
    get_user_id_list as service_get_user_id_list,
    get_concierge_user_info_map as service_get_concierge_user_info_map,
)
from app.service.ads import (
    select_ads_init_info as service_select_ads_init_info,
    random_design_style as service_random_design_style,
    select_ai_age as service_select_ai_age,
    select_ai_data as service_select_ai_data,
)
from app.service.ads_generate import (
    generate_content as service_generate_content,
)
from app.service.ads_app import (
    generate_by_seed_prompt as service_generate_by_seed_prompt,
)
from app.service.concierge_auto_upload import (
    save_history_image_from_base64 as service_save_history_image_from_base64,
    build_public_image_url as service_build_public_image_url,
)
from app.crud.concierge_auto_upload import (
    insert_concierge_user_history as crud_insert_concierge_user_history,
    update_concierge_user_history_status as crud_update_concierge_user_history_status,
)



router = APIRouter()
logger = logging.getLogger(__name__)


# 내부 공용 서비스 함수 (엔드포인트 X)
async def service_concierge_generate_interval() -> Dict[str, Any]:
    WEEKDAY_CODES = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
    KST = timezone(timedelta(hours=9))

    now_kst = datetime.now(KST)
    window_start = now_kst
    window_end = now_kst + timedelta(hours=1)

    today_idx = now_kst.weekday()          # 0=Mon, 6=Sun
    today_code = WEEKDAY_CODES[today_idx]  # 'MON' ~ 'SUN'

    next_day_idx = (today_idx + 1) % 7
    next_day_code = WEEKDAY_CODES[next_day_idx]

    start_time_str = window_start.strftime("%H:%M:%S")
    end_time_str = window_end.strftime("%H:%M:%S")

    same_day = window_start.date() == window_end.date()

    user_id_list = service_get_user_id_list(
        same_day, today_code, next_day_code, start_time_str, end_time_str
    )

    if not user_id_list:
        return {"count": 0, "results": []}

    user_info_map = service_get_concierge_user_info_map(user_id_list)

    tasks = [
        process_user_task(idx, user_id_list, user_info_map)
        for idx in range(len(user_id_list))
    ]
    results = await asyncio.gather(*tasks)

    return {"count": len(results), "results": results}



# ==================================================================
# 🔥 1) 병렬로 돌릴 “개별 매장 처리 함수”
# ==================================================================


async def process_user_task(idx: int, user_id_list, user_info_map):
    """
    idx 번째 user 데이터로
    - init_data
    - 문구 생성
    - 이미지 생성
    전부 수행해서 dict 로 결과 반환하는 함수
    """

    KST = timezone(timedelta(hours=9))

    # 예: idx번째 유저 처리
    user_id = user_id_list[idx]
    user_info = user_info_map.get(user_id)

    if not user_info:
        # 해당 user_id의 concierge_user 정보가 없을 때 처리
        return

    store_business_number = user_info["store_business_number"]
    menu_1 = user_info["menu_1"]
    road_name = user_info["road_name"]
    

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
@router.post("/test/interval")
async def test_interval():
    generation_results = await service_concierge_generate_interval()
    return JSONResponse(content=generation_results)

# ==================================================================
# 🔥 3) 병렬로 돌릴 "개별 유저 저장 처리 함수"
# ==================================================================
async def process_single_user_history_and_upload(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    process_user_task() 결과 1건(result)을 받아서:
      - history 디렉토리에 이미지 저장
      - concierge_user_history INSERT (PENDING)
      - Instagram 업로드(컨테이너 생성 + 게시)
      - history 상태 업데이트
    까지 처리하는 비동기 함수
    """

    if not IG_USER_ID or not IG_ACCESS_TOKEN:
        return {
            "user_id": result.get("user_id"),
            "success": False,
            "error": "Instagram 계정 정보(IG_USER_ID / IG_LONG_LIVED_TOKEN)가 설정되지 않았습니다.",
        }

    user_id = result.get("user_id")
    origin_images: List[str] = result.get("origin_image") or []
    caption: str = result.get("copyright") or ""
    channel: int = int(result.get("channel") or 0)
    register_tag: str | None = result.get("register_tag")

    if not user_id:
        return {"success": False, "error": "user_id 누락"}

    if not origin_images:
        return {"user_id": user_id, "success": False, "error": "origin_image 없음"}

    # 1) base64 이미지 1장 선택 (여기서는 첫 장 사용)
    image_b64 = origin_images[0]

    # 2) history 디렉토리에 파일 저장 (sync → 별도 스레드로)
    try:
        image_path = await asyncio.to_thread(
            service_save_history_image_from_base64,
            user_id,
            image_b64,
        )
    except Exception as e:
        return {
            "user_id": user_id,
            "success": False,
            "error": f"이미지 저장 실패: {e}",
        }

    # 3) concierge_user_history INSERT (PENDING)
    try:
        history_id = crud_insert_concierge_user_history(
            user_id=user_id,
            image_path=image_path,
            caption=caption,
            channel=channel,
            register_tag=register_tag,
        )
    except Exception as e:
        return {
            "user_id": user_id,
            "success": False,
            "error": f"히스토리 INSERT 실패: {e}",
        }

    # 4) public URL 구성 (인스타에 넘길 image_url)
    image_url = service_build_public_image_url(image_path)

    # 5) Instagram 업로드 (동기 함수 → to_thread 로 병렬 실행)
    try:
        # 1단계: 컨테이너 생성
        creation_id = await asyncio.to_thread(
            create_media_container,
            IG_USER_ID,
            image_url,
            caption,
            IG_ACCESS_TOKEN,
        )

        # 2단계: 게시
        publish_result = await asyncio.to_thread(
            publish_media,
            IG_USER_ID,
            creation_id,
            IG_ACCESS_TOKEN,
        )

        insta_media_id = publish_result.get("id") or publish_result.get("media_id")

        # 성공 상태 업데이트
        crud_update_concierge_user_history_status(
            history_id=history_id,
            status="SUCCESS",
            insta_media_id=insta_media_id,
            error_message=None,
        )

        return {
            "user_id": user_id,
            "history_id": history_id,
            "success": True,
            "insta_media_id": insta_media_id,
        }

    except Exception as e:
        # 실패 상태 업데이트
        crud_update_concierge_user_history_status(
            history_id=history_id,
            status="FAILED",
            insta_media_id=None,
            error_message=str(e),
        )
        return {
            "user_id": user_id,
            "history_id": history_id,
            "success": False,
            "error": f"Instagram 업로드 실패: {e}",
        }



# ==================================================================
# 🔥 4) upload_instagram() → 병렬 처리 적용
# ==================================================================
async def upload_instagram(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    process_user_task() 결과 리스트를 받아
    user_id 별로 Instagram 업로드를 병렬 처리.
    - 이미지 저장
    - concierge_user_history 기록
    - Instagram 게시
    까지 모두 수행한 뒤 요약 결과를 반환.
    """

    # 에러가 있는 항목은 업로드 대상에서 제외 (원하면 포함 로직 변경 가능)
    valid_results = [
        r for r in results
        if r and not r.get("error")
    ]

    if not valid_results:
        return {
            "count": 0,
            "results": [],
        }

    tasks = [
        process_single_user_history_and_upload(r)
        for r in valid_results
    ]

    # 병렬 실행
    upload_results = await asyncio.gather(*tasks, return_exceptions=False)

    return {
        "count": len(upload_results),
        "results": upload_results,
    }

# ==================================================================
# 🔥 5) 최종 적용
# ==================================================================
@router.post("/auto/upload/instagram")
async def concierge_auto_run():
    """
    1) 지금~1시간 내 예약된 user_id 기준으로 이미지/문구 생성 (이미 구현된 test_interval 로직 재사용)
    2) 그 결과를 그대로 upload_instagram()에 넘겨서
       - 이미지 저장
       - history 기록
       - 인스타 업로드
    까지 수행
    """
    # 이미 구현된 생성 파트 (예: service_concierge_generate_interval)
    generation_results = await service_concierge_generate_interval()  # 내부에서 process_user_task 병렬 실행

    # 인스타 업로드 병렬 처리
    upload_summary = await upload_instagram(generation_results["results"])

    return {
        "generation_count": len(generation_results["results"]),
        "upload": upload_summary,
    }


