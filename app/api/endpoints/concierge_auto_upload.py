from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import logging
from io import BytesIO
import base64
from datetime import datetime, timezone, timedelta
import asyncio
import os
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import asyncio
        # 네가 작성한 함수 import
from dotenv import load_dotenv
import time
import requests
import random

# ==== .env 로드 ====
load_dotenv()

UPLOAD_ROOT = "/app/uploads"  # 이미 쓰던 값
UPLOAD_PUBLIC_BASE_URL = os.getenv("UPLOAD_PUBLIC_BASE_URL", "https://wizmarket.ai/uploads")

IG_USER_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")
IG_ACCESS_TOKEN = os.getenv("INSTAGRAM_TOKEN")

from app.api.endpoints.insta_test import (
    create_media_container, publish_media, get_instagram_permalink, send_report_sms
)  
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
    get_concierge_user_with_store as service_get_concierge_user_with_store
)
from app.crud.concierge_auto_upload import (
    insert_concierge_user_history as crud_insert_concierge_user_history,
    update_concierge_user_history_status as crud_update_concierge_user_history_status,
)



router = APIRouter()
logger = logging.getLogger(__name__)


class ConciergeInstaUploadRequest(BaseModel):
    user_id: int
    image_base64: str    # AdsSwiper에서 캡쳐한 최종 템플릿 이미지
    caption: str         # 인스타 캡션 (copyright)
    channel: int         # 채널 번호 (1=카톡, 2=스토리, 3=피드 ...)
    register_tag: Optional[str] = None  # 김치찌개, 치킨 등 태그


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
# 🔥 Instagram 컨테이너 준비 상태 폴링 헬퍼
# ==================================================================
def wait_until_media_ready(
    creation_id: str,
    access_token: str,
    timeout_sec: int = 60,
    interval_sec: int = 3,
) -> None:
    """
    Instagram media 컨테이너가 게시 가능한 상태가 될 때까지 대기.
    - status_code == "FINISHED" : 정상 → return
    - status_code == "ERROR"    : 예외 발생
    - timeout 지나도 FINISHED 안 되면 TimeoutError
    """
    start = time.time()
    url = f"https://graph.facebook.com/v18.0/{creation_id}"

    while True:
        elapsed = time.time() - start
        if elapsed > timeout_sec:
            raise TimeoutError("Instagram media not ready within timeout")

        resp = requests.get(
            url,
            params={
                "fields": "status_code",
                "access_token": access_token,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        status = data.get("status_code")

        logger.info(f"[wait_until_media_ready] creation_id={creation_id}, status={status}")

        if status == "FINISHED":
            # 준비 완료 → 게시 가능
            return
        if status == "ERROR":
            raise RuntimeError(f"Instagram media status ERROR for creation_id={creation_id}")

        # 아직 처리 중(IN_PROGRESS 등) → 잠깐 대기 후 재시도
        time.sleep(interval_sec)



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
        random_item = random.choice(random_image_list)
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

    theme = {1: "매장 홍보", 2: "상품 소개"}.get(title_number, "이벤트")

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
                {init_data.store_name} 매장의 {channel_text}를 위한 이벤트 문구를 제작하려고 합니다.
                - 오늘 날짜는 {today}.
                - 세부업종 혹은 상품 : {menu_1}
                - 이벤트내용 : (미입력)
                - 특정 시즌/기념일(예: 발렌타인데이, 화이트데이, 빼빼로데이, 크리스마스, 추석, 설날 등)은 해당 기념일 특성 반영
                - 핵심 고객 연령대 : {ai_age}
                - 지역 고려: {init_data.district_name}
                제약: 연령·날씨·년도 직접 언급 금지, 특수기호/이모지/해시태그 제외.
                형식: 
                제목 : (20자 이내)
                내용 : (30자 이내)
            """
        else:
            copyright_prompt = f"""
                {init_data.store_name} 매장의 {channel_text}를 위한 이벤트 문구를 제작하려고 합니다.
                - 오늘 날짜는 {today}.
                - 세부업종 혹은 상품 : {menu_1}
                - 이벤트내용 : (미입력)
                - 특정 시즌/기념일(예: 발렌타인데이, 화이트데이, 빼빼로데이, 크리스마스, 추석, 설날 등)은 해당 기념일 특성 반영
                - 핵심 고객 연령대 : {ai_age}
                - 지역 고려: {init_data.district_name}
                출력: 20자 이하의 간결하고 호기심을 유발하는 한 문장.
                제약: 연령·날씨 직접 언급 금지, 특수기호/이모지/해시태그 제외.
            """

        copyright = service_generate_content(
            copyright_prompt, copyright_role, ""
        )

    except Exception:
        return {"user_id": user_id, "error": "문구 생성 오류"}

    # ------------------------------
    # 4) 이미지 생성
    # ------------------------------
    seed_prompt = random_item.prompt

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
async def process_single_user_history_and_upload_from_front(
    user_id: int,
    image_base64: str,
    caption: str,
    channel: int,
    register_tag: Optional[str],
) -> Dict[str, Any]:
    """
    프론트(AdsSwiper)에서 보낸 최종 이미지 + 캡션을 받아:
      - history 디렉토리에 이미지 저장
      - concierge_user_history INSERT (PENDING)
      - Instagram 업로드(컨테이너 생성 + 게시)
      - history 상태 업데이트
    까지 처리하는 비동기 함수
    """
    if not IG_USER_ID or not IG_ACCESS_TOKEN:
        return {
            "user_id": user_id,
            "success": False,
            "error": "Instagram 계정 정보(IG_USER_ID / IG_LONG_LIVED_TOKEN)가 설정되지 않았습니다.",
        }

    if not image_base64:
        return {
            "user_id": user_id,
            "success": False,
            "error": "image_base64 누락",
        }

    # 1) history 디렉토리에 파일 저장
    try:
        image_path = await asyncio.to_thread(
            service_save_history_image_from_base64,
            user_id,
            image_base64,
        )
    except Exception as e:
        print("error : " f"이미지 저장 실패: {e}")

    # 2) concierge_user_history INSERT (PENDING)
    try:
        history_id = crud_insert_concierge_user_history(
            user_id=user_id,
            image_path=image_path,
            caption=caption,
            channel=channel,
            register_tag=register_tag,
        )
    except Exception as e:
        # print("error : " f"히스토리 INSERT 실패: {e}")
        return {
            "user_id": user_id,
            "success": False,
            "error": f"히스토리 INSERT 실패: {e}",
        }

    # 3) public URL 구성 (인스타에 넘길 image_url)
    image_url = service_build_public_image_url(image_path)
    # print(f"[process_single_user_history_and_upload_from_front] image_url={image_url}")

    # 4) Instagram 업로드 (동기 함수 → to_thread)
    try:
        # 1단계: 컨테이너 생성
        creation_id = await asyncio.to_thread(
            create_media_container,
            IG_USER_ID,
            image_url,
            caption,
            IG_ACCESS_TOKEN,
        )

        logger.info(f"[process_single_user_history_and_upload] creation_id={creation_id}")

        # 1.5단계: 컨테이너 준비 완료될 때까지 폴링
        await asyncio.to_thread(
            wait_until_media_ready,
            creation_id,
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

        permalink = None
        if insta_media_id:
            try:
                permalink = get_instagram_permalink(insta_media_id, IG_ACCESS_TOKEN)
            except Exception as e:
                logger.exception("[process_single_user_history_and_upload] get_permalink error: %s", e)

        

        # 성공 상태 업데이트
        crud_update_concierge_user_history_status(
            history_id=history_id,
            status="SUCCESS",
            insta_media_id=insta_media_id,
            error_message=None,
        )


        # 문자 보내기
        # 🔹 DB에서 전화번호/가게명 가져오기 (예시)
        user_row = service_get_concierge_user_with_store(user_id)  # 이미 있다면 그 함수 사용
        phone = user_row["phone"]
        store_name = user_row["store_name"]

        # 🔹 문자 발송(블로킹) → 스레드로 넘기기
        if phone and permalink:
            await asyncio.to_thread(
                send_report_sms,
                phone,
                store_name,
                image_url,
                permalink,
            )
        
        
        return {
            "user_id": user_id,
            "history_id": history_id,
            "success": True,
            "insta_media_id": insta_media_id,
        }

    except Exception as e:
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
@router.post("/auto/upload/instagram")
async def concierge_upload_instagram(req: ConciergeInstaUploadRequest):
    """
    AdsSwiper에서 템플릿 캡쳐한 최종 이미지를 받아
    - history 저장
    - concierge_user_history 기록
    - Instagram 업로드
    를 처리하는 엔드포인트
    """
    # (원하면 서버 로그용)
    # print(
    #     f"[concierge_upload_instagram] user_id={req.user_id}, "
    #     f"caption_len={len(req.caption)}, channel={req.channel}, tag={req.register_tag}"
    # )

    result = await process_single_user_history_and_upload_from_front(
        user_id=req.user_id,
        image_base64=req.image_base64,
        caption=req.caption,
        channel=req.channel,
        register_tag=req.register_tag,
    )
    # print(result)

    if not result.get("success"):
        # 클라이언트에서 실패 알 수 있게 에러 코드 반환
        raise HTTPException(status_code=500, detail=result.get("error") or "업로드 실패")

    return JSONResponse(content=result)
