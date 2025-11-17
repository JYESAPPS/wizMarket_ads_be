from fastapi import APIRouter, HTTPException, status, UploadFile, File, Request, Query
from fastapi.responses import JSONResponse
from typing import List, Dict, Optional, Any
import logging
import os
from uuid import uuid4
from typing import List
from datetime import datetime
from fastapi import UploadFile, File, Request
from io import BytesIO
import base64
from PIL import Image
import uuid
from instagrapi import Client

from app.schemas.concierge import (
    IsConcierge, AddConciergeStore, ConciergeUploadRequest
) 
from app.service.concierge import (
    is_concierge as service_is_concierge,
    submit_concierge as service_submit_concierge,
    select_concierge_list as service_select_concierge_list,
    select_concierge_detail as service_select_concierge_detail,
    get_report_store as service_get_report_store,
    concierge_add_new_store as service_concierge_add_new_store,
    update_concierge_status as service_update_concierge_status
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


# 상세 페이지
@router.get("/select/concierge/detail/{user_id}")
def select_concierge_detail(user_id: int) -> Dict[str, Any]:
    """
    컨시어지 신청 상세 조회
    - 프론트: /admin/concierge/:id 에서 사용
    """
    detail = service_select_concierge_detail(user_id)
    return detail



# 승인 처리 후 DB 동기화 & 이미지 + 텍스트 생성
@router.post("/approve/concierge")
def approve_concierge(request : AddConciergeStore):
    
    user_id = request.user_id
    store_name = request.store_name
    road_name = request.road_name
    menu_1 = request.menu_1

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
            result = service_concierge_add_new_store(request)
            store_business_number = result.get("store_business_number")

    except Exception as e:
        return {
            "messeage" : "매장 복사 오류"
        }

    # Repoer TB is_concierge 컬럼과 Concierge_User TB store_busienss_number, status 컬럼 업데이트
    try:
        service_update_concierge_status(user_id, store_business_number)

    except Exception as e:
        return {
            "messeage" : "유저 업데이트 오류"
        }
    
    # 이미지 생성 때 필요한 기본 정보 가져오기
    try:
        init_data = service_select_ads_init_info(store_business_number)
        ai_age = service_select_ai_age(init_data, menu_1)
        ai_data = service_select_ai_data(init_data, ai_age, menu_1)
        random_image_list = service_random_design_style(init_data, ai_data[0])
    
    except Exception as e:
        return {
            "messeage" : "기본 정보 불러오기 오류"
        }

    style_nunmber = ai_data[0]
    channel_number = ai_data[2]
    title_number = ai_data[3]


    detail_content = ""
    today = datetime.now()

    channel_text = ""
    if channel_number == 1:
        channel_text = "카카오톡"
    elif channel_number == 2:
        channel_text = "인스타그램 스토리"
    elif channel_number == 3:
        channel_text = "인스타그램 피드 게시글"
    elif channel_number == 4:
        channel_text = "블로그"
    elif channel_number == 5:
        channel_number = "문자메시지"
    elif channel_number == 6:
        channel_text = "네이버밴드"
    elif channel_number == 7:
        channel_text = "X(트위터)"


    theme = ""
    if title_number == 1: theme = "매장홍보"
    elif title_number ==2: theme = "상품소개"
    else: title_number = "이벤트"


    # 문구 생성
    try:
        copyright_role = '''
                당신은 인스타그램, 블로그 등 소셜미디어 광고 전문가입니다. 
                인스타그램과 블로그 광고의 노출 알고리즘을 잘 알고 있으며 광고 카피문구를 능숙하게 작성할 수 있고 
                마케팅에 대한 상당한 지식으로 지금까지 수 많은 소상공인 기업들의 마케팅에 도움을 주었습니다.  
        '''
        copyright_prompt = ""

        if title_number == 3 or title_number == "3":
            copyright_role = f'''
                    당신은 인스타그램, 블로그 등 소셜미디어 광고 전문가입니다. 
                    인스타그램과 블로그 광고의 노출 알고리즘을 잘 알고 있으며 광고 카피문구를 능숙하게 작성할 수 있고 
                    마케팅에 대한 상당한 지식으로 지금까지 수많은 소상공인 기업들의 마케팅에 도움을 주었습니다.

                    특히 한국의 시즌/기념일 마케팅을 다룰 때, 다음 규칙을 매우 엄격하게 지킵니다.

                    1. 사용자가 제공한 '오늘 날짜'를 기준으로 앞으로 7일 이내(오늘 포함)에 실제로 다가오는 기념일이 있을 때에만 그 기념일을 언급합니다.
                    2. 이미 지나간 기념일(오늘보다 이전 날짜)은 7일 이내이더라도 절대 언급하지 않습니다.
                    3. 발렌타인데이, 화이트데이, 블랙데이, 할로윈, 빼빼로데이, 크리스마스, 추석, 설날 등은 예시 목록일 뿐입니다.
                        - 오늘 기준 앞으로 7일 이내에 실제로 다가오는 경우가 아니라면, 이 기념일 이름들을 문구에 쓰지 않습니다.
                    4. 7일 이내에 다가오는 기념일이 없다면, 어떤 기념일/시즌도 언급하지 않고
                        매장의 업종, 상품, 혜택만 매력적으로 강조하는 이벤트 문구를 작성합니다.
                    5. 추석, 설날처럼 날짜가 해마다 달라지는 기념일은, 오늘 기준으로 7일 이내인지 확실하지 않으면 언급하지 않습니다.
                    '''

            copyright_prompt = f'''
                    {request.store_name} 매장의 {channel_text}를 위한 이벤트 문구를 제작하려고 합니다.

                    오늘 날짜는 {today}입니다.

                    [기념일 관련 규칙]
                    - 아래 기념일 목록은 참고용 예시입니다.
                        (발렌타인데이 2월 14일, 화이트데이 3월 14일, 블랙데이 4월 14일,
                        할로윈 10월 31일, 빼빼로데이 11월 11일, 크리스마스 12월 25일, 추석, 설날 등)
                    - {today}를 기준으로 앞으로 7일 이내(오늘 포함)에 실제로 다가오는 기념일이 있을 때에만,
                        해당 기념일을 포함한 이벤트 문구를 작성하세요.
                    - 오늘보다 이전 날짜의 기념일(이미 지나간 기념일)은 7일 이내이더라도 절대 언급하지 마세요.
                        예: 오늘이 11월 14일이면, 11월 11일 빼빼로데이는 이미 지났으므로 절대 언급하지 않습니다.
                    - 7일 이내에 다가오는 기념일이 없다면, 어떤 기념일/시즌도 언급하지 말고
                        매장과 상품, 혜택 중심의 일반 이벤트 문구만 작성하세요.
                    - 추석, 설날처럼 날짜가 매년 달라지는 기념일은, 오늘 기준으로 7일 이내인지 확실하지 않으면 언급하지 마세요.

                    [매장 및 타겟 정보]
                    - 세부 업종 혹은 상품 : {menu_1}
                    - 핵심 고객 연령대 : {ai_age}
                    - 매장 지역 : {request.road_name}

                    [작성 규칙]
                    - 20자 이하의 제목과 30자 내외의 호기심을 유발할 수 있는 본문을 작성하세요.
                    - {channel_text}에 업로드할 이벤트 문구를 작성하세요.
                    - 연령대, 날씨, 년도, 해시태그는 이벤트 문구에 직접적으로 언급하지 마세요.
                    - 특수기호, 이모티콘은 사용하지 마세요.
                    - 아래 형식을 정확히 지키세요.
                        제목 : (제목)
                        내용 : (본문)
                    '''
        else:
            copyright_prompt = f'''
                    {request.store_name} 매장의 {channel_text}에 포스팅할 광고 문구를 제작하려고 합니다.
                    - 세부 업종 혹은 상품 : {menu_1}
                    - 홍보 컨셉 : {theme}
                    - 특정 시즌/기념일 이벤트 (예: 발렌타인데이 2월 14일, 화이트데이 3월14일, 블랙데이 4월14일, 
                        빼빼로데이 11월 11일, 크리스마스 12월 25일, 추석, 설날 등)엔 해당 내용으로 문구 생성
                    - 핵심 고객 연령대 : {ai_age} 
                    {request.road_name} 지역의 특성을 살려서 {ai_age}이 선호하는 문체 스타일을 기반으로 
                    20자 이하로 간결하고 호기심을 유발할 수 있는 {channel_text} 이미지에 업로드할 {theme} 문구를 작성해주세요. 
                    단, 연령대와 날씨, 년도, 해시태그를 광고 문구에 직접적으로 언급하지 말고 특수기호, 이모티콘도 제외해 주세요.
                '''
                # copyright_role = f'''
                #     you are professional writer.
                #     10자 내외 간결하고 호기심을 유발할 수 있는 문구
                # '''

                # copyright_prompt = f'''
                #     {request.store_name} 업체를 위한 문구.
                #     {request.detail_category_name}, {formattedToday}, {request.main}, {request.temp}℃
                #     주요 고객층: {age}을 바탕으로 15자 이내로 작성해주세요
                # '''
        copyright = service_generate_content(
                copyright_prompt,
                copyright_role,
                detail_content
        )
        print(copyright)
            
        route = "auto_prompt_app"

    except Exception as e:
        return {
            "messeage" : "문구 생성 오류"
        }
    

    # 이미지 생성
    seed_prompt = random_image_list.prompt
    try:
        origin_image = service_generate_by_seed_prompt(
            channel_number,
            copyright,
            "",
            seed_prompt,
            menu_1
        )

        output_images = []
        for image in origin_image:  # 리스트의 각 이미지를 순회
            buffer = BytesIO()
            image.save(buffer, format="PNG")  # 이미지 저장
            buffer.seek(0)
                
            # Base64 인코딩 후 리스트에 추가
            output_images.append(base64.b64encode(buffer.getvalue()).decode("utf-8"))

    except Exception as e:
        # print(f"Error occurred: {e}, 이미지 생성 오류")
        raise HTTPException(
            status_code=500,
            detail=f"이미지 생성 오류: {str(e)}"
        )
    
    insta_copyright = ""

    return JSONResponse(content={
            "copyright": copyright, "origin_image": output_images, "insta_copyright" : insta_copyright,
            "title": title_number, "channel":channel_number, "style": style_nunmber,  "core_f": ai_age,
            "main": init_data.main, "temp" : init_data.temp, "detail_category_name" : init_data.detail_category_name, "register_tag": menu_1,
            "store_name": init_data.store_name, "road_name": init_data.road_name, "store_business_number":store_business_number, "prompt" : seed_prompt
        })



@router.post("/concierge/upload")
def upload_insta(payload: ConciergeUploadRequest):
    """
    프론트에서 온 data:image/png;base64,... 문자열을 받아
    1080x1080으로 리사이즈 후 인스타에 업로드
    """
    raw = payload.image

    if not raw:
        raise HTTPException(status_code=400, detail="image 데이터가 비어 있습니다.")

    # 1) data URL 형식이면 'data:image/png;base64,' 부분 제거
    #    (이미 순수 base64만 넘어오는 경우도 안전하게 처리)
    if "," in raw:
        _, b64 = raw.split(",", 1)
    else:
        b64 = raw

    # 2) base64 디코딩
    try:
        image_bytes = base64.b64decode(b64)
    except Exception:
        raise HTTPException(status_code=400, detail="잘못된 base64 이미지입니다.")

    # 3) Pillow로 이미지 열기
    try:
        buf = BytesIO(image_bytes)
        image = Image.open(buf)
    except Exception:
        raise HTTPException(status_code=400, detail="이미지 파일을 열 수 없습니다.")

    # 4) RGB 변환 + 1080x1080 리사이즈
    image = image.convert("RGB")
    image = image.resize((1080, 1080))

    # 5) 임시 파일 경로에 저장 (instagrapi는 파일 경로 필요)
    filename = f"concierge_{uuid.uuid4().hex}.jpg"
    save_dir = "/tmp"  # 필요하면 UPLOAD_ROOT 등으로 변경
    os.makedirs(save_dir, exist_ok=True)
    photo_path = os.path.join(save_dir, filename)

    image.save(photo_path, format="JPEG", quality=95)

    INSTAGRAM_ID = "tpals213@gmail.com"
    INSTAGRAM_PW = "101603sm!!"

    # 6) instagrapi로 업로드
    try:
        cl = Client()
        cl.login(INSTAGRAM_ID, INSTAGRAM_PW)

        caption = "hello this is a test from instagrapi"
        media = cl.photo_upload(photo_path, caption)

    except Exception as e:
        # 1) 서버 로그에 찍고
        print(f"[Instagram 업로드 실패]: {e}")

        # 2) 프론트에도 에러 내용을 그대로 전달
        raise HTTPException(
            status_code=500,
            detail=f"Instagram 업로드 실패: {e}"
        )

    # 여기까지 왔다는 건 media가 무조건 존재하는 상태
    return {
        "success": True,
        "media_id": media.pk,
        "code": getattr(media, "code", None),
        "image_path": photo_path,
    }

