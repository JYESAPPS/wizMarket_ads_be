from fastapi import (
    APIRouter, UploadFile, File, Form, HTTPException, status
)
import httpx
from app.schemas.ads_app import (
    AutoAppMain,
    AutoApp, AutoAppRegen, AutoAppSave, UserRecoUpdate, AutoGenCopy,
    ManualGenCopy, ManualImageListAIReco, ManualApp,
    UserInfo, UserInfoUpdate, UserRecentRecord, UserRecoDelete,
    ImageList, ImageUploadRequest, StoreInfo, EventGenCopy, CameraGenCopy
)
import io
from fastapi import Request, Body
from PIL import ImageOps, Image
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
from io import BytesIO
from types import SimpleNamespace
import base64
import logging
import re
import json
from app.service.ads_generate import (
    generate_content as service_generate_content,
)
from app.service.ads_app import (
    generate_option as service_generate_option,
    parse_age_gender_info as service_parse_age_gender_info,
    select_random_image as service_select_random_image,
    generate_by_seed_prompt as service_generate_by_seed_prompt,
    get_style_image as service_get_style_image,
    insert_upload_record as service_insert_upload_record,
    get_style_image_ai_reco as sercvice_get_style_image_ai_reco,
    get_user_info as service_get_user_info,
    get_user_reco as service_get_user_reco,
    get_user_profile as service_get_user_profile,
    service_insert_user_info,
    update_user_info as service_update_user_info,
    get_user_recent_reco as service_get_user_recent_reco,
    update_user_reco as service_update_user_reco,
    delete_user_reco as service_delete_user_reco,
    get_manual_ai_reco as service_get_manual_ai_reco,
    generate_template_manual_camera as service_generate_template_manual_camera,
    generate_image_remove_bg as service_generate_image_remove_bg,
    generate_bg as service_generate_bg,
    generate_option_without_gender as service_generate_option_without_gender,
    get_manual_ai_reco_without_gender as service_get_manual_ai_reco_without_gender,
    validation_test as service_validation_test,
    extract_age_group as service_extract_age_group,
    get_store_info as service_get_store_info,
    update_register_tag as service_update_register_tag,
    update_user_custom_menu as service_update_user_custom_menu,
    get_season as service_get_season,
    pick_effective_menu as service_pick_effective_menu,
    generate_vertex_bg as service_generate_vertex_bg,
    cartoon_image as service_cartoon_image,
    trim_newline as service_trim_newline,
)
from app.service.ads_ticket import (
    get_valid_ticket as service_get_valid_ticket
)
import os
import uuid


router = APIRouter()
logger = logging.getLogger(__name__)



# 메인 페이지에서 바로 생성
@router.post("/auto/prompt/app")
def generate_template(request: AutoAppMain):
    try:
        title = request.ai_data[3]
        channel = request.ai_data[2]
        design = request.ai_data[0]
        age = request.ai_age

        channel_text = ""
        if channel == 1:
            channel_text = "카카오톡"
        elif channel == 2:
            channel_text = "인스타그램 스토리"
        elif channel == 3:
            channel_text = "인스타그램 피드 게시글"
        elif channel == 4:
            channel_text = "블로그"
        elif channel == 5:
            channel_text = "문자메시지"
        elif channel == 6:
            channel_text = "네이버밴드"
        elif channel == 7:
            channel_text = "X(트위터)"


        # menu = request.custom_menu 
        # menu = request.register_tag 
        # if request.custom_menu == '' : 
        # if request.register_tag == '' :
        #     menu = request.detail_category_name

        menu = (getattr(request, "register_tag", None) or "").strip()
        if not menu:
            try:
                # 가능하면 user_id로 조회 (스키마에 user_id 없으면 건너뜀)
                user_id = int(getattr(request, "user_id", 0) or 0)
                if user_id:
                    info, _ = service_get_user_info(user_id)
                    menu = (info or {}).get("register_tag") or ""
            except Exception:
                pass
        if not menu:
            # 최종 폴백: 업종 세부명
            menu = request.detail_category_name

        theme = ""
        if title == 1: theme = "매장홍보"
        elif title ==2: theme = "상품소개"
        else: theme = "이벤트"

        today = datetime.now()
        # formattedToday = today.strftime('%Y-%m-%d')
        # season = service_get_season(formattedToday)

        detail_content = ""
        # 문구 생성
        try:
            copyright_role = '''
                당신은 인스타그램, 블로그 등 소셜미디어 광고 전문가입니다. 
                인스타그램과 블로그 광고의 노출 알고리즘을 잘 알고 있으며 광고 카피문구를 능숙하게 작성할 수 있고 
                마케팅에 대한 상당한 지식으로 지금까지 수 많은 소상공인 기업들의 마케팅에 도움을 주었습니다.  
            '''
            copyright_prompt = ""

            if title == 3 or title == "3":
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
                    - 세부 업종 혹은 상품 : {menu}
                    - 핵심 고객 연령대 : {age}
                    - 매장 지역 : {request.district_name}

                    [작성 규칙]
                    - 20자 이하의 제목과 30자 내외의 호기심을 유발할 수 있는 본문을 작성하세요.
                    - {channel_text}에 업로드할 이벤트 문구를 작성하세요.
                    - 연령대, 날씨, 년도, 해시태그는 이벤트 문구에 직접적으로 언급하지 마세요.
                    - 특수기호, 이모티콘은 사용하지 마세요.
                    - 아래 형식을 정확히 지키세요.
                        제목 : (제목)
                        내용 : (본문)
                    '''
                # copyright_role = f'''
                #     you are professional writer.
                #     - 제목 : 10자 내외 간결하고 호기심을 유발할 수 있는 문구
                #     - 내용 : 20자 내외 간결하고 함축적인 내용
                #     - 특수기호, 이모티콘은 제외할 것
                # '''

                # copyright_prompt = f'''
                #     {request.store_name} 업체를 위한 광고 컨텐츠를 제작하려고 합니다.
                #     {request.detail_category_name}, {formattedToday}, {request.main}, {request.temp}℃
                #     주요 고객층: {age} 제목 :, 내용 : 형식으로 작성해주세요
                # '''
            else:
                copyright_prompt = f'''
                    {request.store_name} 매장의 {channel_text}에 포스팅할 광고 문구를 제작하려고 합니다.
                    - 세부 업종 혹은 상품 : {menu}
                    - 홍보 컨셉 : {theme}
                    - 특정 시즌/기념일 이벤트 (예: 발렌타인데이 2월 14일, 화이트데이 3월14일, 블랙데이 4월14일, 
                        빼빼로데이 11월 11일, 크리스마스 12월 25일, 추석, 설날 등)엔 해당 내용으로 문구 생성
                    - 핵심 고객 연령대 : {age} 
                    {request.district_name} 지역의 특성을 살려서 {age}이 선호하는 문체 스타일을 기반으로 
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
            
            route = "auto_prompt_app"

        except Exception as e:
            print(f"Error occurred: {e}, 문구 생성 오류")


        # 전달받은 선택한 템플릿의 시드 프롬프트 gpt로 소분류에 맞게 바꾸기
        seed_prompt = request.image_list.prompt
        style = design
        # 이미지 생성
        try:
            origin_image = service_generate_by_seed_prompt(
                channel,
                copyright,
                request.detail_category_name,
                seed_prompt,
                menu
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

        # 인스타 문구 테스트
        try:
            insta_copyright = ''
            
            if channel == 3 or channel == 4:

                copyright_prompt = f'''
                    {request.store_name} 업체의 {channel_text}를 위한 광고 콘텐츠를 제작하려고 합니다. 
                    업종: {request.detail_category_name}
                    세부정보: {menu}
                    주소: {request.district_name}
                    
                    단! "대표 메뉴 앞에 아이콘만 넣고, 메뉴 이름 뒤에는 아이콘을 넣지 않는다." 
                    "위치는 📍로 표현한다."
                    "'\n'으로 문단을 나눠 표현한다."
                '''

                insta_role = f'''
                    1. '{copyright}' 를 100~150자까지 {channel_text} 인플루언서가 {request.detail_category_name}을 소개하는 듯한 느낌으로 광고 문구 만들어줘.
                    2.광고 타겟들이 흥미를 갖을만한 내용의 키워드를 뽑아서 검색이 잘 될만한 SEO기반 해시태그도 최소 3개에서 6개까지 생성한다.
                    3.핵심 고객인 {age}가 선호하는 문체로 작성하되 나이는 표현하지 않는다.
                '''

                insta_copyright = service_generate_content(
                    copyright_prompt,
                    insta_role,
                    detail_content
                )
        except Exception as e:
            print(f"Error occurred: {e}, 인스타 생성 오류")

        if age == "10대":
            age = "1"
        elif age == "20대":
            age = "2"
        elif age == "30대":
            age = "3"
        elif age == "40대":
            age = "4"
        elif age == "50대":
            age = "5"
        elif age == "60대 이상":
            age = "6"

        

        # 문구와 합성된 이미지 반환
        return JSONResponse(content={
            "copyright": copyright, "origin_image": output_images, "insta_copyright" : insta_copyright,
            "title": str(title), "channel":str(channel), "style": style, "core_f": age,
            "main": request.main, "temp" : request.temp, "detail_category_name" : request.detail_category_name, "register_tag": menu,
            "store_name": request.store_name, "road_name": request.road_name, "district_name": request.district_name,
            "store_business_number":request.store_business_number, "prompt" : seed_prompt, "route": route
        })

    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"  
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)




# AI 생성 자동
@router.post("/auto/app")
def generate_template(request: AutoApp):
    female_text = ""
    options = ""
    try:
        # GPT 로 옵션 값 자동 생성
        try : 
            female_text = service_parse_age_gender_info(request.commercial_district_max_sales_f_age)
        except Exception as e:
            print(f"Error occurred: {e}, 문구 생성 오류")

        try:
            if female_text : 
                options = service_generate_option(
                    request
                )
            else : 
                options = service_generate_option_without_gender(
                    request
                )
        except Exception as e:
            print(f"Error occurred: {e}, 문구 생성 오류")

        raw = options.replace(",", "-").replace(" ", "")  # "3-1-4"
        parts = raw.split("-")  # ["3", "1", "4"]
        
        if female_text : 
            title, channel, style = parts
        else : 
            title, channel, female_text, style = parts

        # 유효성 검사 및 기본값 지정
        title, channel, female_text, style = service_validation_test(title, channel, female_text, style)

        detail_content = ""
        # 문구 생성
        try:
            copyright_role = ""
            copyright_prompt = ""
            # print(request.example_image)
            today = datetime.now()
            formattedToday = today.strftime('%Y-%m-%d')

            if title == 3 or title == "3":
                copyright_role = '''
                    you are professional writer.
                    - 제목 : 10자 내외 간결하고 호기심을 유발할 수 있는 문구
                    - 내용 : 20자 내외 간결하고 함축적인 내용
                    - 특수기호, 이모티콘은 제외할 것
                '''

                copyright_prompt = f'''
                    {request.store_name} 업체를 위한 광고 컨텐츠를 제작하려고 합니다.
                    {request.register_tag}, {formattedToday}, {request.main}, {request.temp}℃
                    주요 고객층: {female_text} 제목 :, 내용 : 형식으로 작성해주세요
                '''
            else:
                copyright_role = f'''
                    you are professional writer.
                    10자 내외 간결하고 호기심을 유발할 수 있는 문구
                '''

                copyright_prompt = f'''
                    {request.store_name} 업체를 위한 문구.
                    {request.register_tag}, {formattedToday}, {request.main}, {request.temp}℃
                    주요 고객층: {female_text}을 바탕으로 15자 이내로 작성해주세요
                '''
            copyright = service_generate_content(
                copyright_prompt,
                copyright_role,
                detail_content
            )

        except Exception as e:
            print(f"Error occurred: {e}, 문구 생성 오류")


        # 전달받은 선택한 템플릿의 시드 프롬프트 gpt로 소분류에 맞게 바꾸기
        seed_prompt = service_select_random_image(style)

        # 이미지 생성
        try:
            origin_image = service_generate_by_seed_prompt(
                channel,
                copyright,
                request.detail_category_name,
                seed_prompt,
                request.register_tag
            )

            output_images = []
            for image in origin_image:  # 리스트의 각 이미지를 순회
                buffer = BytesIO()
                image.save(buffer, format="PNG")  # 이미지 저장
                buffer.seek(0)
                
                # Base64 인코딩 후 리스트에 추가
                output_images.append(base64.b64encode(buffer.getvalue()).decode("utf-8"))

        except Exception as e:
            print(f"Error occurred: {e}, 이미지 생성 오류")

        # 인스타 문구 테스트
        try:
            insta_copyright = ''
            
            if channel == "3":
                today = datetime.now()
                formattedToday = today.strftime('%Y-%m-%d')

                copyright_prompt = f'''
                    {request.store_name} 업체의 {channel}를 위한 광고 콘텐츠를 제작하려고 합니다. 
                    업종: {request.detail_category_name}
                    메뉴 : {request.register_tag}
                    일시 : {formattedToday}
                    주요 고객층: {female_text}

                    주소: {request.road_name}
                    
                    단! "대표 메뉴 앞에 아이콘만 넣고, 메뉴 이름 뒤에는 아이콘을 넣지 않는다." "위치는 📍로 표현한다. 
                    '\n'으로 문단을 나눠 표현한다
                '''

                insta_role = f'''
                    1. '{copyright}' 를 100~150자까지 인플루언서가 {request.register_tag} 을 소개하는 듯한 느낌으로 광고 문구 만들어줘 
                    
                    2.광고 타겟들이 흥미를 갖을만한 내용의 키워드를 뽑아서 검색이 잘 될만한 해시태그도 최소 3개에서 6개까지 생성한다

                    3.나이는 표현하지 않는다.
                '''

                insta_copyright = service_generate_content(
                    copyright_prompt,
                    insta_role,
                    detail_content
                )
        except Exception as e:
            print(f"Error occurred: {e}, 인스타 생성 오류")

        # 문구와 합성된 이미지 반환
        return JSONResponse(content={
            "copyright": copyright, "origin_image": output_images, "insta_copyright" : insta_copyright,
            "title": title, "channel":channel, "style": style,  "core_f": female_text,
            "main": request.main, "temp" : request.temp, "detail_category_name" : request.detail_category_name, "register_tag": request.register_tag,
            "store_name": request.store_name, "road_name": request.road_name, "store_business_number":request.store_business_number, "prompt" : seed_prompt
        })

    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)






# 스타일별 이미지 값 가져오기
@router.post("/auto/style/image")
def get_style_image(request : ImageList):
    image_list = service_get_style_image(request)

    return JSONResponse(content={
        "image_list":image_list
    })

# AI 생성 자동 - 재생성
@router.post("/auto/app/regen")
def generate_template_regen(request: AutoAppRegen):
    try:
        style = request.style
        channel = request.channel
        prompt = request.prompt
        age = request.age
        temp = request.temp
        store_name= request.store_name
        main= request.main
        detail_category_name = request.detail_category_name
        title = request.title
        road_name = request.road_name
        store_business_number = request.store_business_number
        
        female_text = f"{age}0대"
        channel_text = ""

        if channel == "1" : 
            channel_text = "카카오톡"
        elif channel == "2":
            channel_text = "인스타그램 스토리"
        elif channel == "3":
            channel_text = "인스타그램 피드 게시글"
        elif channel == "4":
            channel_text = "블로그"
        elif channel == "5":
            channel_text = "문자메시지"
        elif channel == "6":
            channel_text = "네이버밴드"
        elif channel == "7":
            channel_text = "X(트위터)"
        else :
            channel_text = "네이버 블로그"

        theme = ""
        if title == "1" : theme = "매장홍보"
        elif title =="2": theme = "상품소개"
        else: theme = "이벤트"

        # menu = request.custom_menu 
        # menu = request.register_tag
        # if request.custom_menu == '' : 
        # if request.register_tag == '' : 
        #     menu = request.detail_category_name
        menu = service_pick_effective_menu(request)

        detail_content = getattr(request, "ad_text", "") or ""

        # 1) 클라이언트에서 온 값들
        # - ad_text_override: 이번(재생성 화면)에서 사용자가 방금 입력한 값
        # - use_override: override를 실제로 사용하려는 의사(빈 문자열도 '의도적 삭제'로 인정하기 위해 필요)
        # - ad_text / ad_text_theme: 1차 생성 때 사용자가 썼던 과거 값과 그 주제
        ad_text_override = getattr(request, "ad_text_override", None)  # None이면 '이번에 안 보냄'
        use_override     = bool(getattr(request, "use_override", False))
        ad_text          = getattr(request, "ad_text", "") or ""
        ad_text_theme    = getattr(request, "ad_text_theme", None)  # "매장홍보"|"상품소개"|"이벤트"|None

        # 2) 우선순위 적용
        if use_override:
            # 이번에 입력창을 건드린 경우(의도적으로 보냄)
            # - 빈 문자열("") 이면 '지우기' → AI 생성
            # - 비어있지 않으면 그 값을 사용(현재 주제에 종속)
            detail_content = (ad_text_override or "").strip()
            if detail_content == "":
                detail_content = ""  # → 아래 생성 분기로 감
            else:
                if ad_text_theme and ad_text_theme == theme and ad_text.strip() != "":
                    detail_content = ad_text.strip()
                else:
                    detail_content = ""
        else:
            # 이번에 새로 입력하지 않았음 → 과거 값 검토
            if ad_text_theme and ad_text_theme == theme and ad_text.strip() != "":
                detail_content = ad_text.strip()
            else:
                detail_content = ""  # → 아래 생성 분기로 감

        # --------------------------
        # 주제 확정 → 그 주제의 입력 유무 판단 → AI 생성(필요 시)
        # --------------------------
        event_title = ""  # 이벤트에만 사용
        copyright = ""
        copy_role = '''
            당신은 인스타그램, 블로그 등 소셜미디어 광고 전문가입니다. 
            인스타그램과 블로그 광고의 노출 알고리즘을 잘 알고 있으며 광고 카피문구를 능숙하게 작성할 수 있고 
            마케팅에 대한 상당한 지식으로 지금까지 수 많은 소상공인 기업들의 마케팅에 도움을 주었습니다.
        '''

        try:
            if theme == "이벤트":
                if detail_content:
                    # 입력 있음 → 본문 그대로 사용 + 제목만 20자 이내 생성
                    copyright = detail_content
                    copy_prompt = f'''
                        {store_name} 매장의 {channel_text}에 올릴 이벤트 제목을 만듭니다.
                        - 세부업종/상품: {menu}
                        - 이벤트 내용: {detail_content}
                        - 핵심 고객 연령대: {female_text}
                        - 지역 반영: {getattr(request, "district_name", "")}
                        제약: 연령/날씨 직접 언급 금지, 특수기호/이모지/해시태그 제외, 20자 이내 한국어 제목만 출력.
                    '''
                    event_title = service_generate_content(copy_prompt, copy_role, detail_content)
                else:
                    # 입력 없음 → "제목 :, 내용 :" 형식으로 둘 다 생성
                    copy_prompt = f'''
                        {store_name} 매장의 {channel_text}를 위한 이벤트 문구를 제작하려고 합니다.
                        - 세부업종 혹은 상품 : {menu}
                        - 이벤트내용 : (미입력)
                        - 특정 시즌/기념일(예: 발렌타인데이, 화이트데이, 빼빼로데이, 크리스마스, 추석, 설날 등)은 해당 기념일 특성 반영
                        - 핵심 고객 연령대 : {female_text}
                        - 지역 고려: {getattr(request, "district_name", "")}
                        제약: 연령·날씨·년도 직접 언급 금지, 특수기호/이모지/해시태그 제외.
                        형식: 
                        제목 : (20자 이내)
                        내용 : (30자 이내)
                    '''
                    full = service_generate_content(copy_prompt, copy_role, detail_content)
                    # 간단 파싱
                    evt_title, evt_body = "", ""
                    for line in [p.strip() for p in full.splitlines() if p.strip()]:
                        if line.startswith("제목"):
                            evt_title = line.split(":", 1)[1].strip() if ":" in line else line.replace("제목", "").strip()
                        elif line.startswith("내용"):
                            evt_body = line.split(":", 1)[1].strip() if ":" in line else line.replace("내용", "").strip()
                    event_title = evt_title[:20]
                    copyright  = (evt_body or full).strip()
            else:
                # 매장홍보/상품소개
                if detail_content:
                    # 입력 있음 → 그대로 사용
                    copyright = detail_content
                else:
                    # 입력 없음 → 해당 주제 컨텍스트로 간결 카피 생성
                    copy_prompt = f'''
                        {store_name} 매장의 {channel_text}에 포스팅할 광고 문구를 제작하려고 합니다.
                        - 세부업종 혹은 상품 : {menu}
                        - 홍보컨셉 : {theme}
                        - 특정 시즌/기념일(예: 발렌타인데이, 화이트데이, 빼빼로데이, 크리스마스, 추석, 설날 등)은 반영 가능
                        - 핵심 고객 연령대 : {female_text}
                        - 지역 고려: {getattr(request, "district_name", "")}
                        출력: 20자 이하의 간결하고 호기심을 유발하는 한 문장.
                        제약: 연령·날씨 직접 언급 금지, 특수기호/이모지/해시태그 제외.
                    '''
                    copyright = service_generate_content(
                        copy_prompt, copy_role, ""
                    )
        except Exception as e:
            print(f"Error occurred: {e}, 문구 생성 오류")


        # 이미지 생성
        try:
            origin_image = service_generate_by_seed_prompt(
                channel,
                copyright,
                detail_category_name,
                prompt,
                menu
            )

            output_images = []
            for image in origin_image:  # 리스트의 각 이미지를 순회
                buffer = BytesIO()
                image.save(buffer, format="PNG")  # 이미지 저장
                buffer.seek(0)
                
                # Base64 인코딩 후 리스트에 추가
                output_images.append(base64.b64encode(buffer.getvalue()).decode("utf-8"))

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"이미지 생성 오류: {str(e)}"
            )

        # 인스타 문구 테스트
        try:
            insta_copyright = ''
            
            if channel == "3" or channel == "4" or channel == "6" or channel == "7":

                copyright_prompt = f'''
                    {store_name} 업체의 {channel_text}을 위한 광고 콘텐츠를 제작하려고 합니다. 
                    업종: {detail_category_name}
                    세부정보: {menu}
                    주소: {request.district_name}
                    
                    단! "대표 메뉴 앞에 아이콘만 넣고, 메뉴 이름 뒤에는 아이콘을 넣지 않는다." 
                    "위치는 📍로 표현한다."
                    "'\n'으로 문단을 나눠 표현한다."
                '''

                insta_role = f'''
                    1. '{copyright}' 를 100~150자까지 {channel_text} 인플루언서가 {request.detail_category_name}을 소개하는 듯한 느낌으로 광고 문구 만들어줘. 
                    2. 광고 타겟들이 흥미를 갖을만한 내용의 키워드를 뽑아서 검색이 잘 될만한 SEO기반 해시태그도 최소 3개에서 6개까지 생성한다.
                    3. 핵심 고객인 {female_text}가 선호하는 문체로 작성하되 나이는 표현하지 않는다.
                '''

                insta_copyright = service_generate_content(
                    copyright_prompt,
                    insta_role,
                    detail_content
                )
        except Exception as e:
            print(f"Error occurred: {e}, 인스타 생성 오류")

        # 반환 전 프론트와 맞춰주기
        if title == "매장홍보":
            title = "1"
        elif title == "상품소개":
            title = "2"
        elif title == "이벤트":
            title = "3"

        if female_text == "10대":
            age = "1"
        elif female_text == "20대":
            age = "2"
        elif female_text == "30대":
            age = "3"
        elif female_text == "40대":
            age = "4"
        elif female_text == "50대":
            age = "5"
        elif female_text == "60대":
            age = "6"
        else: age = "3"

        # 문구와 합성된 이미지 반환
        return JSONResponse(content={
            "copyright": copyright, "origin_image": output_images, "insta_copyright" : insta_copyright, "event_title": event_title,
            "title": title, "channel":channel, "style": style, "core_f": age,
            "main": main, "temp" : temp, "detail_category_name" : detail_category_name,
            "menu": menu, "register_tag": request.register_tag, "custom_menu": request.custom_menu,
            "store_name": store_name, "road_name": road_name, "district_name": request.district_name,
            "store_business_number": store_business_number, "prompt":prompt,
            "ad_text": getattr(request, "ad_text", ""), "ad_text_theme": getattr(request, "ad_text_theme", None),  "ad_text_override": getattr(request, "ad_text_override", None),
        })

    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


# AI 생성 자동 - 저장
@router.post("/auto/app/save")
async def insert_upload_record_endpoint(req: Request):
    ctype = req.headers.get("content-type", "")
    try:
        if ctype.startswith("multipart/form-data"):
            # Blob 업로드
            form = await req.form()
            file = form.get("image")
            if file is None:
                raise HTTPException(status_code=400, detail="file 필드가 필요합니다.")
            # 서비스가 기대하는 필드만 만들어 전달 (image=None)
            data = SimpleNamespace(
                age=form.get("age"),
                alert_check=json.loads(form.get("alert_check", "false")),
                channel=form.get("channel"),
                repeat=form.get("repeat"),
                style=form.get("style"),
                title=form.get("title"),
                upload_time=form.get("upload_time"),
                user_id=int(form.get("user_id")),
                date_range=json.loads(form.get("date_range") or "[]"),
                image=None,
                type=form.get("type"),
                prompt=form.get("prompt"),
                insta_copyright=form.get("insta_copyright") or "",
                copyright=form.get("copyright")
            )
            result = await service_insert_upload_record(data, file=file)
            return JSONResponse(content=result)

        else:
            # JSON(Base64) 업로드 (레거시)
            body = await req.json()
            data = AutoAppSave(**body)
            result = await service_insert_upload_record(data, file=None)
            return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")



# AI 생성 자동 - 문구 생성하기
@router.post("/auto/gen/copy")
def generate_template_regen_auto(request: AutoGenCopy):
    try:
        category = request.category
        store_name= request.store_name
        main= request.main
        temp = request.temp
        road_name = request.road_name
        title = request.title

        detail_content = ""
        copyright_role = f'''
            you are a marketing expert
        '''
        # 문구 생성
        try:
            today = datetime.now()
            formattedToday = today.strftime('%Y-%m-%d')
            
            copyright_prompt = f'''
                {store_name} 업체를 위한 홍보 내용을 작성해주세요.
                주소는 {road_name} 이고 홍보할 주제는 {title} 입니다.
                {category} 업종이며 오늘은 {formattedToday}, {main} 입니다, 
                다음을 바탕으로 100자 이내로 작성해주세요.
                ex) 오늘 방문하신 고객에게 테이블 당 소주 1병 서비스
                ex2) 마라 칼국수 신메뉴! 얼얼하게 매운 맛!
                ex3) 7월 대 오픈! 시원한 냉면 드시러 오세요~
            '''

            copyright = service_generate_content(
                copyright_prompt,
                copyright_role,
                detail_content
            )
            copyright = service_trim_newline(copyright)

        except Exception as e:
            print(f"Error occurred: {e}, 문구 생성 오류")


        # 문구 반환
        return JSONResponse(content={
            "copyright": copyright
        })

    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)




# AI 생성 수동 - 초기 값 가져오기
@router.post("/manual/ai/reco")
def manual_ai_reco(request : AutoApp):
    try : 
        female_text = service_parse_age_gender_info(request.commercial_district_max_sales_f_age)
    except Exception as e:
        print(f"Error occurred: {e}, 문구 생성 오류")

    try:
        if female_text : 
            options = service_generate_option(
                request
            )
        else : 
            options = service_generate_option_without_gender(
                request
            )
    except Exception as e:
        print(f"Error occurred: {e}, 문구 생성 오류")

    raw = options.replace(",", "-").replace(" ", "")  # "3-1-4"
    parts = raw.split("-")  # ["3", "1", "4"]

    if female_text : 
        title, channel, style= parts
    else : 
        title, channel, female_text, style = parts

    title, channel, female_text, style = service_validation_test(title, channel, female_text, style)
    female_text = service_extract_age_group(female_text)

    return JSONResponse(content={
        "title" : title, 
        "channel" : channel, 
        "female_text" : female_text,
        "style": style
    })

# AI 생성 수동 - 문구 생성하기
@router.post("/manual/gen/copy")
def generate_template_regen_manual(request: ManualGenCopy):
    try:
        category = request.category
        channel = request.channel
        age = request.age
        subChannel = request.subChannel
        theme = request.theme
        store_name= request.store_name
        main= request.main
        temp = request.temp
        road_name = request.road_name
        female_text = f"{age}대"

        detail_content = ""
        copyright_role = f'''
            you are a marketing expert
        '''
        # 문구 생성
        try:
            
            copyright_prompt = f'''
                    {store_name} 업체를 위한 {subChannel} 에 포스팅할 홍보 내용을 작성해주세요.
                    {category} 업종의 홍보할 주제는 {theme} 입니다.
                    주요 고객층: {female_text}을 바탕으로 100자 이내로 작성해주세요.
                    나이는 표현하지 않는다.
                    ex) 오늘 방문하신 고객에게 테이블 당 소주 1병 서비스
                    ex2) 마라 칼국수 신메뉴! 얼얼하게 매운 맛!
                    ex3) 7월 대 오픈! 시원한 냉면 드시러 오세요~
                '''

            copyright = service_generate_content(
                copyright_prompt,
                copyright_role,
                detail_content
            )
            copyright = service_trim_newline(copyright)

        except Exception as e:
            print(f"Error occurred: {e}, 문구 생성 오류")


        # 문구 반환
        return JSONResponse(content={
            "copyright": copyright
        })

    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

# AI 생성 수동 - 문구 생성하기
@router.post("/camera/gen/copy")
def generate_template_regen_manual(request: CameraGenCopy):
    try:
        category = request.category
        theme = request.theme
        store_name= request.store_name
        main= request.main
        temp = request.temp
        road_name = request.road_name
        # resister_tag = request.resister_tag
        # female_text = f"{age}대"
        # if request.resister_tag == '' : 
        #     menu = request.category

        detail_content = ""
        copyright_role = f'''
            you are a marketing expert
        '''

        base_ctx = f"{store_name} 매장, 업종/상품: {category}"
        if theme == "매장홍보":
            task = "매장 방문 욕구를 높이는 카피"
            focus = "매장 경험·분위기·가치"
        elif theme == "상품소개":
            task = "핵심 장점을 강조하는 상품 카피"
            focus = "구체적 특징·맛/식감·차별점"
        else:  # 이벤트
            task = "이벤트 참여를 유도하는 카피"
            focus = "혜택·기간·행동 촉구"

        # 문구 생성
        try:
            today = datetime.now()

            copyright_prompt = f'''
                아래 조건을 만족하는 한국어 카피 문장 '한 줄'을 1개만 생성하라.

                맥락: {base_ctx}
                테마: {theme}
                목표: {task}
                핵심 초점: {focus}
                
                세부업종 혹은 상품 : {category}
                내용 :  {detail_content}
                
                제약:
                - 한 줄짜리 카피 '1개'만 생성
                - 줄바꿈/번호/불릿/따옴표/콜론/이모지/해시태그 금지
                - 설명/예시/제목·내용 같은 라벨 금지
                - 날씨 언급 금지
                - 실제로 존재하지 않는 축제나 기념일, 이벤트 생성 금지

                20자 이하의 호기심을 유발할 수 있는 {theme}에 업로드할 이벤트 문구를 작성해주세요. 
                단, 날씨를 이벤트 문구에 직접적으로 언급하지 말고 특수기호, 이모티콘, 해시태그도 제외해 주세요.
            '''
            copyright = service_generate_content(
                copyright_prompt,
                copyright_role,
                detail_content
            )
            copyright = service_trim_newline(copyright)

        except Exception as e:
            print(f"Error occurred: {e}, 문구 생성 오류")


        # 문구 반환
        return JSONResponse(content={
            "copyright": copyright
        })

    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

# 이벤트 문구 생성하기
@router.post("/event/gen/copy")
def generate_event(request: EventGenCopy):
    try:
        category = request.category
        # channel = request.channel
        # age = request.age
        # subChannel = request.subChannel
        store_name= request.store_name
        # weather= request.weather
        # temp = request.temp
        # road_name = request.road_name
        # female_text = f"{age}대"

        detail_content = ""
        copyright_role = f'''
            you are a marketing expert
        '''
        # 문구 생성
        try:
            
            copyright_prompt = f'''
                    {store_name} 업체의 단기 이벤트 내용을 작성해주세요.
                    이벤트 상품은 {category} 입니다.
                    이벤트 상품을 바탕으로 100자 이내로 작성해주세요.

                    ex) 오늘 방문하신 고객에게 테이블 당 소주 1병 서비스
                    ex2) 마라 칼국수 신메뉴! 10% 할인!
                    ex3) 7월 대 오픈! 첫 100명에게 냉면 1000원에 제공
                    ex4) 8월 여름맞이 이벤트! 금일 방문하여 3인분 주문 시 숙성 삼겹살 100g 서비스
                '''

            copyright = service_generate_content(
                copyright_prompt,
                copyright_role,
                detail_content
            )
            copyright = service_trim_newline(copyright)
        except Exception as e:
            print(f"Error occurred: {e}, 문구 생성 오류")


        # 문구 반환
        return JSONResponse(content={
            "copyright": copyright
        })

    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


# 이벤트 문구 재생성
@router.post("/event/regen/copy")
def regenerate_event(request: EventGenCopy):
    try:
        category = request.category
        # resister_tag = request.register_tag
        store_name= request.store_name
        # weather= request.weather
        # road_name = request.road_name
        # custom_text = request.custom_text

        detail_content = ""
        copyright_role = f'''
            you are a marketing expert
        '''
        # 문구 생성
        try:
            copyright_prompt = f'''
                    {store_name} 업체의 단기 이벤트 내용을 작성해주세요.
                    이벤트 상품은 {category} 입니다.
                    이벤트 상품을 바탕으로 100자 이내로 작성해주세요.

                    ex) 오늘 방문하신 고객에게 테이블 당 소주 1병 서비스
                    ex2) 마라 칼국수 신메뉴! 10% 할인!
                    ex3) 7월 대 오픈! 첫 100명에게 냉면 1000원에 제공
                    ex4) 8월 여름맞이 이벤트! 금일 방문하여 3인분 주문 시 숙성 삼겹살 100g 서비스
                    ex5) 12월 겨울맞이 이벤트! 헬스장 신규 등록 고객 10% 할인
                '''

            copyright = service_generate_content(
                copyright_prompt,
                copyright_role,
                detail_content
            )
            copyright = service_trim_newline(copyright)
        except Exception as e:
            print(f"Error occurred: {e}, 문구 생성 오류")


        # 문구 반환
        return JSONResponse(content={
            "copyright": copyright
        })

    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

# AI 생성 수동 - 이벤트 
@router.post("/manual/style/image")
def get_style_image_ai_reco(request: ManualImageListAIReco):
    # image_list = service_get_style_image(request)
    raw_ai_style = sercvice_get_style_image_ai_reco(request)

    # 숫자만 추출
    match = re.match(r"(\d+)", str(raw_ai_style))
    ai_style = int(match.group(1)) if match else None

    return JSONResponse(content={
        # "image_list": image_list,
        "ai_style": ai_style
    })

# AI 생성 수동 - 선택 한 값들로 이미지 생성
@router.post("/manual/app")
def generate_template_manual(request : ManualApp):
    try:
        store_business_number= request.store_business_number
        main= request.main
        temp= request.temp
        style=request.style
        female_text= request.age
        sub_channel= request.subChannel
        theme= request.theme
        store_name= request.store_name
        road_name= request.road_name
        district_name = request.district_name
        detail_category_name= request.detail_category_name
        prompt = request.prompt
        channel = request.channel
        channel_text = ""

        menu = request.customMenu
        if request.customMenu == '' : 
            menu = request.category

        if channel =="카카오톡":
            channel_text = "1"
            sub_channel = ""
        elif channel == "블로그":
            channel_text = "4"
            sub_channel = ""
        elif channel == "문자메시지":
            channel_text = "5"
            sub_channel = ""
        elif channel == "네이버밴드":
            channel_text = "6"
            sub_channel = ""
        elif channel == "X(트위터)":
            channel_text = "7"
            sub_channel = ""
        elif sub_channel == "스토리":
            channel_text = "2"
        else:
            channel_text = "3"

        detail_content = getattr(request, "customText", "") or ""

        # 사용자 커스텀 메뉴 값 업데이트
        try : 
            service_update_user_custom_menu(menu, store_business_number)
        except Exception as e:
            print(f"Error occurred: {e}, 유저 커스텀 메뉴 업데이트 오류")

        # today = datetime.now()
        # formattedToday = today.strftime('%Y-%m-%d')
        # season = service_get_season(formattedToday)

        # 문구 생성
        try:
            copyright_role = '''
                당신은 인스타그램, 블로그 등 소셜미디어 광고 전문가입니다. 
                인스타그램과 블로그 광고의 노출 알고리즘을 잘 알고 있으며 광고 카피문구를 능숙하게 작성할 수 있고 
                마케팅에 대한 상당한 지식으로 지금까지 수 많은 소상공인 기업들의 마케팅에 도움을 주었습니다.  
            '''
            event_title = ""

            # 내용 있을 시 그대로 사용
            if detail_content != "" :
                # 이벤트일 경우 제목 생성
                if theme == "이벤트":
                    copyright = detail_content
                    copyright_prompt = f'''
                        {store_name} 매장의 {channel} {sub_channel}에 포스팅할 광고 문구를 제작하려고 합니다.
                        - 세부업종 혹은 상품 : {menu}
                        - 홍보컨셉 : {theme}, {detail_content}
                        - 특정 시즌/기념일 이벤트 (예: 발렌타인데이 2월 14일, 화이트데이 3월14일, 블랙데이 4월14일, 
                            빼빼로데이 11월 11일, 크리스마스 12월 25일, 추석, 설날 등) 엔 해당 내용으로 문구 생성
                        - 핵심 고객 연령대 : {female_text} 
                        {district_name} 지역의 특성을 살려서 {female_text}이 선호하는 문체 스타일을 기반으로 
                        20자 이하의 간결하고 호기심을 유발할 수 있는 {channel} {sub_channel} 이미지에 업로드할 
                        {theme} ({detail_content}) 문구를 작성해주세요. 
                        단, 연령대와 날씨를 광고 문구에 직접적으로 언급하지 말고 특수기호, 이모티콘, 해시태그도 제외해 주세요.
                    '''

                    event_title = service_generate_content(
                        copyright_prompt,
                        copyright_role,
                        detail_content
                    )

                else :
                    copyright = detail_content

            else :
                copyright_prompt = ""
                if theme == "이벤트":
                    copyright_prompt = f'''
                        {store_name} 매장의 {channel} {sub_channel}를 위한 이벤트 문구를 제작하려고 합니다.

                        - 세부업종 혹은 상품 : {menu}
                        - 이벤트내용 :  {detail_content}
                        - 특정 시즌/기념일 이벤트 (예: 발렌타인데이 2월 14일, 화이트데이 3월14일, 블랙데이 4월14일, 
                            빼빼로데이 11월 11일, 크리스마스 12월 25일, 추석, 설날 등) 엔 해당 기념일을 포함한 이벤트 문구 생성
                        - 핵심 고객 연령대 : {female_text} 

                        {district_name} 지역의 특성, 기념일 이라면 기념일 특성을 살려서 
                        {female_text}가 선호하는 문체 스타일을 기반으로 20자 이하의 제목과 30자 이하의 
                        호기심을 유발할 수 있는 {channel} {sub_channel}에 업로드할 이벤트 문구를 작성해주세요. 

                        단, 연령대와 날씨를 이벤트 문구에 직접적으로 언급하지 말고 특수기호, 이모티콘, 해시태그도 제외해 주세요.
                        제목 :, 내용 : 형식으로 작성해주세요.
                    '''

                else:
                    copyright_prompt = f'''
                        {store_name} 매장의 {channel} {sub_channel}에 포스팅할 광고 문구를 제작하려고 합니다.
                        - 세부업종 혹은 상품 : {menu}
                        - 홍보컨셉 : {theme}, {detail_content}
                        - 특정 시즌/기념일 이벤트 (예: 발렌타인데이 2월 14일, 화이트데이 3월14일, 블랙데이 4월14일, 
                            빼빼로데이 11월 11일, 크리스마스 12월 25일, 추석, 설날 등) 엔 해당 내용으로 문구 생성
                        - 핵심 고객 연령대 : {female_text} 
                        {district_name} 지역의 특성을 살려서 {female_text}이 선호하는 문체 스타일을 기반으로 
                        20자 이하의 간결하고 호기심을 유발할 수 있는 {channel} {sub_channel} 이미지에 업로드할 
                        {theme} ({detail_content}) 문구를 작성해주세요. 
                        단, 연령대와 날씨를 광고 문구에 직접적으로 언급하지 말고 특수기호, 이모티콘, 해시태그도 제외해 주세요.
                    '''

                copyright = service_generate_content(
                    copyright_prompt,
                    copyright_role,
                    detail_content
                )

        except Exception as e:
            print(f"Error occurred: {e}, 문구 생성 오류")


        # 이미지 생성
        try:
            origin_image = service_generate_by_seed_prompt(
                channel_text,
                copyright,
                detail_category_name,
                prompt,
                menu
            )

            output_images = []
            for image in origin_image:  # 리스트의 각 이미지를 순회
                buffer = BytesIO()
                image.save(buffer, format="PNG")  # 이미지 저장
                buffer.seek(0)
                
                # Base64 인코딩 후 리스트에 추가
                output_images.append(base64.b64encode(buffer.getvalue()).decode("utf-8"))

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"이미지 생성 오류: {str(e)}"
            )

        # 인스타 문구 테스트
        try:
            insta_copyright = ''
            
            if channel_text == "3" or channel_text == "4" or channel_text == "6" or channel_text == "7":

                copyright_prompt = f'''
                    {store_name} 업체의 {channel} {sub_channel}을 위한 광고 콘텐츠를 제작하려고 합니다. 
                    업종: {detail_category_name}
                    세부정보: {menu}
                    주소: {district_name}
                    
                    단! "대표 메뉴 앞에 아이콘만 넣고, 메뉴 이름 뒤에는 아이콘을 넣지 않는다." 
                    "위치는 📍로 표현한다."
                    "'\n'으로 문단을 나눠 표현한다."
                '''

                insta_role = f'''
                    1. '{copyright}' 를 100~150자까지 {channel} 인플루언서가 {detail_category_name}을 소개하는 듯한 느낌으로 광고 문구 만들어줘. 
                    2. 광고 타겟들이 흥미를 갖을만한 내용의 키워드를 뽑아서 검색이 잘 될만한 SEO기반 해시태그도 최소 3개에서 6개까지 생성한다
                    3. 핵심 고객인 {female_text}가 선호하는 문체로 작성하되 나이는 표현하지 않는다.
                '''

                insta_copyright = service_generate_content(
                    copyright_prompt,
                    insta_role,
                    detail_content
                )
        except Exception as e:
            print(f"Error occurred: {e}, 인스타 생성 오류")

        # 반환 전 프론트와 맞춰주기
        if theme == "매장홍보":
            title = "1"
        elif theme == "상품소개":
            title = "2"
        elif theme == "이벤트":
            title = "3"

        if female_text == "10대":
            age = "1"
        elif female_text == "20대":
            age = "2"
        elif female_text == "30대":
            age = "3"
        elif female_text == "40대":
            age = "4"
        elif female_text == "50대":
            age = "5"
        elif female_text == "60대 이상":
            age = "6"
        
        style = str(style)

        # 문구와 합성된 이미지 반환
        return JSONResponse(content={
            "copyright": copyright, "origin_image": output_images, "insta_copyright" : insta_copyright,
            "title": title, "channel":channel_text, "style": style, "core_f": age,
            "main": main, "temp" : temp, "menu" : menu, "detail_category_name" : detail_category_name,
            "store_name": store_name, "road_name": road_name, "district_name": district_name, 
            "store_business_number": store_business_number, "prompt" : prompt, "customText" : request.customText,
            "event_title": event_title
        })

    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    

# 이벤트 마케팅 ai 생성
@router.post("/event/app")
def generate_template_event(request : ManualApp):
    try:
        store_business_number= request.store_business_number
        main= request.main
        temp= request.temp
        style=request.style
        female_text= request.age
        sub_channel= request.subChannel
        theme= request.theme
        store_name= request.store_name
        road_name= request.road_name
        district_name = request.district_name
        detail_category_name= request.detail_category_name
        prompt = request.prompt
        channel = request.channel
        menu = request.customMenu

        channel_text = ""
        if channel =="카카오톡":
            channel_text = "1"
            sub_channel = ""
        elif channel == "블로그":
            channel_text = "4"
            sub_channel = ""
        elif channel == "문자메시지":
            channel_text = "5"
            sub_channel = ""
        elif channel == "네이버밴드":
            channel_text = "6"
            sub_channel = ""
        elif channel == "X(트위터)":
            channel_text = "7"
            sub_channel = ""
        elif sub_channel == "스토리":
            channel_text = "2"
        else:
            channel_text = "3"

        detail_content = getattr(request, "customText", "") or ""

        # custom menu DB 수정
        try : 
            service_update_user_custom_menu(menu, store_business_number)
        except Exception as e:
            print(f"Error occurred: {e}, 유저 커스텀 메뉴 업데이트 오류")

        event_title = ""
        # 문구 생성
        try:
            copyright_role = '''
                당신은 인스타그램, 블로그 등 소셜미디어 광고 전문가입니다. 
                인스타그램과 블로그 광고의 노출 알고리즘을 잘 알고 있으며 광고 카피문구를 능숙하게 작성할 수 있고 
                마케팅에 대한 상당한 지식으로 지금까지 수 많은 소상공인 기업들의 마케팅에 도움을 주었습니다.  
            '''

            if detail_content != "" :
                # 이벤트일 경우 제목 생성
                copyright = detail_content
                copyright_prompt = f'''
                    {store_name} 매장의 {channel} {sub_channel}에 포스팅할 광고 문구를 제작하려고 합니다.
                    - 세부업종 혹은 상품 : {menu}
                    - 홍보컨셉 : {theme}, {detail_content}
                    - 특정 시즌/기념일 이벤트 당일(예: 발렌타인데이 2월 14일, 화이트데이 3월14일, 블랙데이 4월14일, 
                        빼빼로데이 11월 11일, 크리스마스 12월 25일, 추석, 설날 등) 엔 해당 내용으로 문구 생성
                    - 핵심 고객 연령대 : {female_text} 
                    {district_name} 지역의 특성을 살려서 {female_text}이 선호하는 문체 스타일을 기반으로 
                    20자 이하의 간결하고 호기심을 유발할 수 있는 {channel} {sub_channel} 이미지에 업로드할 
                    {theme} ({detail_content}) 문구를 작성해주세요. 
                    단, 연령대와 날씨를 광고 문구에 직접적으로 언급하지 말고 특수기호, 이모티콘, 해시태그도 제외해 주세요.
                '''
                event_title = service_generate_content(
                    copyright_prompt,
                    copyright_role,
                    detail_content
                )

            else :
                

                copyright_prompt = f'''
                    {store_name} 매장의 {channel} {sub_channel}를 위한 이벤트 문구를 제작하려고 합니다.

                    - 세부업종 혹은 상품 : {menu}
                    - 이벤트내용 :  {detail_content}
                    - 특정 시즌/기념일 이벤트 (예: 발렌타인데이 2월 14일, 화이트데이 3월14일, 블랙데이 4월14일, 
                        빼빼로데이 11월 11일, 크리스마스 12월 25일, 추석, 설날 등) 엔 해당 기념일을 포함한 이벤트 문구 생성
                    - 핵심 고객 연령대 : {female_text} 

                    {district_name} 지역의 특성, 기념일 이라면 기념일 특성을 살려서 
                    {female_text}가 선호하는 문체 스타일을 기반으로 20자 이하의 제목과 30자 이하의 
                    호기심을 유발할 수 있는 {channel} {sub_channel}에 업로드할 이벤트 문구를 작성해주세요. 

                    단, 연령대와 날씨를 이벤트 문구에 직접적으로 언급하지 말고 특수기호, 이모티콘, 해시태그도 제외해 주세요.
                    제목 :, 내용 : 형식으로 작성해주세요.
                '''

                copyright = service_generate_content(
                    copyright_prompt,
                    copyright_role,
                    detail_content
                )

        except Exception as e:
            print(f"Error occurred: {e}, 문구 생성 오류")


        # 이미지 생성
        try:
            origin_image = service_generate_by_seed_prompt(
                channel_text,
                copyright,
                detail_category_name,
                prompt,
                menu
            )

            output_images = []
            for image in origin_image:  # 리스트의 각 이미지를 순회
                buffer = BytesIO()
                image.save(buffer, format="PNG")  # 이미지 저장
                buffer.seek(0)
                
                # Base64 인코딩 후 리스트에 추가
                output_images.append(base64.b64encode(buffer.getvalue()).decode("utf-8"))

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"이미지 생성 오류: {str(e)}"
            )

        # 인스타 문구 테스트
        try:
            insta_copyright = ''
            
            if channel_text == "3" or channel_text == "4" or channel_text == "6" or channel_text == "7":

                copyright_prompt = f'''
                    {store_name} 업체의 {channel} {sub_channel}를 위한 광고 콘텐츠를 제작하려고 합니다. 
                    업종: {detail_category_name}
                    세부정보: {menu}
                    주소: {district_name}
                    
                    단! "대표 메뉴 앞에 아이콘만 넣고, 메뉴 이름 뒤에는 아이콘을 넣지 않는다." 
                    "위치는 📍로 표현한다."
                    "'\n'으로 문단을 나눠 표현한다."
                '''

                insta_role = f'''
                    1. '{copyright}' 를 100~150자까지 {channel} 인플루언서가 {detail_category_name}을 소개하는 듯한 느낌으로 광고 문구 만들어줘. 
                    2. 광고 타겟들이 흥미를 갖을만한 내용의 키워드를 뽑아서 검색이 잘 될만한 SEO기반 해시태그도 최소 3개에서 6개까지 생성한다.
                    3. 핵심 고객인 {female_text}가 선호하는 문체로 작성하되 나이는 표현하지 않는다.
                '''

                insta_copyright = service_generate_content(
                    copyright_prompt,
                    insta_role,
                    detail_content
                )
        except Exception as e:
            print(f"Error occurred: {e}, 인스타 생성 오류")

        # 반환 전 프론트와 맞춰주기
        if theme == "매장홍보":
            title = "1"
        elif theme == "상품소개":
            title = "2"
        elif theme == "이벤트":
            title = "3"
        
        if female_text == "10대":
            age = "1"
        elif female_text == "20대":
            age = "2"
        elif female_text == "30대":
            age = "3"
        elif female_text == "40대":
            age = "4"
        elif female_text == "50대":
            age = "5"
        elif female_text == "60대 이상":
            age = "6"

        style = str(style)


        # 문구와 합성된 이미지 반환
        return JSONResponse(content={
            "copyright": copyright, "origin_image": output_images, "insta_copyright" : insta_copyright,
            "title": title, "channel":channel_text, "style": style, "core_f": age,
            "main": main, "temp" : temp, "menu" : menu, "detail_category_name" : detail_category_name,
            "store_name": store_name, "road_name": road_name, "district_name": district_name, 
            "store_business_number": store_business_number, "prompt" : prompt, "customText" : request.customText,
            "event_title": event_title
        })

    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    

# 유저 정보 + 기록 가져오기
@router.post("/get/user/info")
def get_user_info(request : UserInfo):
    try:
        user_id = int(request.userId)
        if request.register_tag is not None:
            service_update_register_tag(user_id, request.register_tag)
        info, record = service_get_user_info(user_id)
        ticket_info = service_get_valid_ticket(user_id)

        return JSONResponse(content={
            "info": info,
            "record": record,
            "ticket_info": ticket_info
        })

    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    

# 유저 이번달 기록 가져오기
@router.post("/get/user/reco")
def get_user_reco(request : UserInfo):
    try:
        user_id = int(request.userId)
        record = service_get_user_reco(user_id)

        return JSONResponse(content={
            "record": record
        })

    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    


# 유저 이미지 프로필 가져오기
@router.post("/get/user/profile")
def get_user_info(request : UserInfo):
    try:
        user_id = int(request.userId)
        profile_image = service_get_user_profile(user_id)
        return JSONResponse(content={
            "profile_image": profile_image
        })

    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

# 유저 정보 업데이트
@router.post("/update/user/info")
def update_user_info(request : UserInfoUpdate):
    ok = service_update_user_info(request.user_id, request.register_tag)
    return JSONResponse({"success": ok}, status_code=200 if ok else 500)
    # try:
    #     user_id = int(request.user_id)

    #     exists = service_get_user_profile(user_id)

    #     if exists:
    #         success = service_update_user_info(user_id, request)
    #     else:
    #         success = service_insert_user_info(user_id, request)

    #     return JSONResponse(content={
    #         "success": success
    #     })

    # except HTTPException as http_ex:
    #     logger.error(f"HTTP error occurred: {http_ex.detail}")
    #     raise http_ex
    # except Exception as e:
    #     error_msg = f"Unexpected error while processing request: {str(e)}"
    #     logger.error(error_msg)
    #     raise HTTPException(status_code=500, detail=error_msg)
    

# 유저 최근 포스팅 기록 3개 가져오기
@router.post("/get/user/recent/record/auto")
def get_user_recent_record(request: UserRecentRecord):
    try:
        reco_list = service_get_user_recent_reco(request)

        if not reco_list:
            return JSONResponse(content={
                "reco_list": []
            }, status_code=status.HTTP_200_OK)


        return JSONResponse(content={
            "reco_list": reco_list
        })

    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    

# 유저 기록 게시물 1개 업데이트
@router.post("/auto/update/user/reco")
def update_user_reco(request : UserRecoUpdate):
    try:
        user_id = int(request.user_id)
        success = service_update_user_reco(user_id, request)

        return JSONResponse(content={
            "success": success
        })

    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    

# 유저 기록 게시물 1개 삭제
@router.post("/auto/delete/user/reco")
def delete_user_reco(request : UserRecoDelete):
    try:
        user_id = int(request.user_id)
        success = service_delete_user_reco(user_id, request)

        return JSONResponse(content={
            "success": success
        })

    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    



# AI 생성 수동 카메라 - AI 추천 받기
@router.post("/manual/camera/ai/reco")
def get_manual_ai_reco(request: AutoApp):

    try:
        try :
            female_text = service_parse_age_gender_info(request.commercial_district_max_sales_f_age)
        except Exception as e:
            print(f"Error occurred: {e}, 문구 생성 오류")


        try:
            if female_text :
                options = service_get_manual_ai_reco(
                    request
                )
            else :
                options = service_get_manual_ai_reco_without_gender(
                    request
                )
        except Exception as e:
            print(f"Error occurred: {e}, 문구 생성 오류")

        raw = options.replace(",", "-").replace(" ", "")  # "3-1-4"
        parts = raw.split("-")  # ["3", "1", "4"]

        if female_text:
            title, channel, style = parts
        else :
            title, channel, female_text, style = parts

        title, channel, female_text, style = service_validation_test(title, channel, female_text, style)

        return JSONResponse(content={
            "title": title, "channel":channel, "style": style, "core_f": female_text,
        })
    
    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    

# AI 생성 수동 카메라 - 선택 한 값들로 이미지 처리
@router.post("/manual/app/camera") 
async def generate_template_manual_camera(
    image: UploadFile = File(None),
    channel: str = Form(...),
    title: str = Form(...),
    age: str = Form(...),
    style: str = Form(...),
    bg_prompt: str = Form(None),  
    filter: int = Form(None),  
    category: str = Form(...),
    custom_menu: str = Form(None),
    register_tag: str = Form(None),
    store_name: str = Form(...),
    road_name: str = Form(...),
    district_name: str = Form(...),
    main: str = Form(...),
    temp: float = Form(...),
    custom_text: str = Form(None),
):
    try:
        custom_menu = custom_menu or register_tag

        # 문구 생성
        try:
            detail_content = ""
            copyright_role = f'''
                {store_name} 매장의 {channel}를 위한 문구를 제작하려고 합니다.
                다음과 같은 속성을 반영하여 연관성있는 카피문구를 작성해주세요.
            '''
            copyright_prompt = ""
            event_title = ""

            if title == "이벤트" :
                # if custom_text != None :
                if custom_text and custom_text.strip():
                    copyright = custom_text

                    copyright_prompt = f'''
                    {store_name} 매장의 {channel}를 위한 이벤트 문구를 제작하려고 합니다.
                    - 홍보 컨셉 : {custom_menu}
                    - 이벤트 컨셉 : {custom_menu}을 주제로 생성
                    - 핵심 고객 연령대 : {age} 
                    - 톤&스타일 : {channel} 스타일로 
                    - 작성요령 : {age} 고객관심사, 트랜드, 짧고 강렬함, CTA 명확(구매유도, 방문유도)
                    단, 연령대와 날씨, 년도, 해시태그를 이벤트 문구에 직접적으로 언급하지 말고 20자 이하로 특수기호, 이모티콘도 제외해 주세요.
                    '''

                    event_title = service_generate_content(
                        copyright_prompt,
                        copyright_role,
                        detail_content
                    )

                else :
                    copyright_prompt = f'''
                        {store_name} 매장의 {channel}를 위한 이벤트 문구를 제작하려고 합니다.
                        - 홍보 컨셉 : {custom_menu}
                        - 이벤트 컨셉 : {custom_menu}을 주제로 생성
                        - 핵심 고객 연령대 : {age} 
                        - 톤&스타일 : {channel} 스타일로 
                        - 작성요령 : {age} 고객관심사, 트랜드, 짧고 강렬함, CTA 명확(구매유도, 방문유도)
                        단, 연령대와 날씨, 년도, 해시태그를 이벤트 문구에 직접적으로 언급하지 말고 20자 이하로 특수기호, 이모티콘도 제외해 주세요.
                        제목 :, 내용 : 형식으로 작성해주세요.
                    '''

                    copyright = service_generate_content(
                        copyright_prompt,
                        copyright_role,
                        detail_content
                    ) 

            else:
                # if custom_text != None :
                if custom_text and custom_text.strip():
                    copyright = custom_text
                
                else : 
                    copyright_prompt = f'''
                        {store_name} 매장의 {channel}를 위한 이벤트 문구를 제작하려고 합니다.
                        - 홍보 컨셉 : {custom_menu}
                        - 이벤트 컨셉 : {custom_menu}을 주제로 생성
                        - 핵심 고객 연령대 : {age} 
                        - 톤&스타일 : {channel} 스타일로 
                        - 작성요령 : {age} 고객관심사, 트랜드, 짧고 강렬함, CTA 명확(구매유도, 방문유도)
                        단, 연령대와 날씨, 년도, 해시태그를 이벤트 문구에 직접적으로 언급하지 말고 20자 이하로 특수기호, 이모티콘도 제외해 주세요.
                    '''
                    copyright = service_generate_content(
                        copyright_prompt,
                        copyright_role,
                        detail_content
                    )

        except Exception as e:
            print(f"Error occurred: {e}, 문구 생성 오류")

        output_images = []

        # 이미지 처리 우선순위: bg_prompt > image
        if bg_prompt:
            content = image.file.read()
            origin_images = service_generate_vertex_bg(content, bg_prompt)
            output_images.extend(origin_images)

        elif image:                
            input_image = Image.open(BytesIO(await image.read()))
            input_image = ImageOps.exif_transpose(input_image)  # ✅ 회전 보정

            # 스타일에 따라 분기
            if style == "배경만 제거" or style == "배경 제거":
                origin_images = service_generate_image_remove_bg(input_image)  # List[PIL.Image]

            elif style == "필터" or style == "이미지 필터":
                buf = BytesIO()
                input_image.save(buf, format="PNG")
                buf.seek(0)
                filtered = await service_cartoon_image(buf.getvalue(), filter)  # PIL.Image
                origin_images = [filtered]

            else:
                origin_images = [input_image]

            # base64 리스트 변환
            for img in origin_images:
                buffer = BytesIO()
                img.save(buffer, format="PNG")
                buffer.seek(0)
                img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
                output_images.append(img_base64)
        else:
            raise HTTPException(status_code=400, detail="이미지 또는 이미지 URL이 제공되지 않았습니다.")

        # 인스타 문구 처리
        insta_copyright = ''
        detail_content = ''
        if channel in ["인스타그램", "인스타 게시물", "블로그", "네이버밴드", "X(트위터)"]:
            try:

                copyright_prompt = f'''
                    {store_name} 업체의 {channel}을 위한 광고 콘텐츠를 제작하려고 합니다. 
                    업종: {category}
                    세부정보: {custom_menu}
                    주소: {district_name}
                    
                    단! "대표 메뉴 앞에 아이콘만 넣고, 메뉴 이름 뒤에는 아이콘을 넣지 않는다." 
                    "위치는 📍로 표현한다."
                    "'\n'으로 문단을 나눠 표현한다."
                '''

                insta_role = f'''
                    1. '{copyright}' 를 100~150자까지 {channel} 인플루언서가 {custom_menu}을 소개하는 듯한 느낌으로 광고 문구 만들어줘. 
                    2. 광고 타겟들이 흥미를 갖을만한 내용의 키워드를 뽑아서 검색이 잘 될만한 SEO기반 해시태그도 최소 3개에서 6개까지 생성한다.
                    3. 핵심 고객인 {age}가 선호하는 문체로 작성하되 나이는 표현하지 않는다.
                '''

                insta_copyright = service_generate_content(
                    copyright_prompt,
                    insta_role,
                    detail_content
                )
            except Exception as e:
                print(f"Error occurred: {e}, 인스타 생성 오류")
        
        return JSONResponse(content={
                "copyright": copyright, "origin_image": output_images,
                "title": title, "channel":channel, "style": style, "core_f": age,
                "main": main, "temp" : temp, "detail_category_name" : category, 
                "register_tag": register_tag, "custom_menu": custom_menu,
                "store_name": store_name, "road_name": road_name, "district_name": district_name,
                "insta_copyright" : insta_copyright, "prompt" : bg_prompt, "filter_idx": filter,
                "event_title": event_title
            })

    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    

# 이벤트 마케팅 - 내 사진 사용 (메뉴 / 이벤트 내용 반영)
@router.post("/event/app/camera")
async def generate_template_event_camera(
    image: UploadFile = File(None),
    channel: str = Form(...),
    title: str = Form(...),
    age: str = Form(...),
    style: str = Form(...),
    bg_prompt: str = Form(None),
    filter: int = Form(None),
    customMenu: str = Form(None),
    customText:str = Form(None),
    category: str = Form(...),
    store_name: str = Form(...),
    store_business_number: str = Form(...),
    road_name: str = Form(...),
    district_name: str = Form(...),
    main: str = Form(...),
    temp: float = Form(...),
):
    try:
        # custom menu DB 수정
        try : 
            service_update_user_custom_menu(customMenu, store_business_number)
        except Exception as e:
            print(f"Error occurred: {e}, 유저 커스텀 메뉴 업데이트 오류")
        
        # 문구 생성
        try:
            event_title = ""
            detail_content = customText or ""
            copyright_role = '''
                당신은 인스타그램, 블로그 등 소셜미디어 광고 전문가입니다. 
                인스타그램과 블로그 광고의 노출 알고리즘을 잘 알고 있으며 광고 카피문구를 능숙하게 작성할 수 있고 
                마케팅에 대한 상당한 지식으로 지금까지 수 많은 소상공인 기업들의 마케팅에 도움을 주었습니다.  
            '''
            copyright_prompt = ""

            if detail_content != "" :
                copyright = detail_content
                copyright_prompt = f'''
                    {store_name} 매장의 {channel}를 위한 이벤트 문구를 제작하려고 합니다.
                    - 홍보 컨셉 : {customMenu}
                    - 이벤트 컨셉 : {customMenu}을 주제로 생성
                    - 핵심 고객 연령대 : {age} 
                    - 톤&스타일 : {channel} 스타일로 
                    - 작성요령 : {age} 고객관심사, 트랜드, 짧고 강렬함, CTA 명확(구매유도, 방문유도)
                    단, 연령대와 날씨, 년도, 해시태그를 이벤트 문구에 직접적으로 언급하지 말고 특수기호, 이모티콘도 제외해 주세요.
                    20자 이하로 작성해주세요
                '''
                event_title = service_generate_content(
                    copyright_prompt,
                    copyright_role,
                    detail_content
                )
            
            else : 
                copyright_prompt = f'''
                    {store_name} 매장의 {channel}를 위한 이벤트 문구를 제작하려고 합니다.
                    - 홍보 컨셉 : {customMenu}
                    - 이벤트 컨셉 : {customMenu}을 주제로 생성
                    - 핵심 고객 연령대 : {age} 
                    - 톤&스타일 : {channel} 스타일로 
                    - 작성요령 : {age} 고객관심사, 트랜드, 짧고 강렬함, CTA 명확(구매유도, 방문유도)
                    단, 연령대와 날씨, 년도, 해시태그를 이벤트 문구에 직접적으로 언급하지 말고 특수기호, 이모티콘도 제외해 주세요.
                    제목 :, 내용 : 형식으로 20자 이라호 작성해주세요.
                '''
                copyright = service_generate_content(
                    copyright_prompt,
                    copyright_role,
                    detail_content
                )
        except Exception as e:
            print(f"Error occurred: {e}, 문구 생성 오류")


        output_images = []

        # 이미지 처리 우선순위: bg_prompt > image
        if bg_prompt:
            content = image.file.read()
            origin_images = service_generate_vertex_bg(content, bg_prompt)
            output_images.extend(origin_images)

        elif image:
            input_image = Image.open(BytesIO(await image.read()))
            input_image = ImageOps.exif_transpose(input_image)  # ✅ 회전 보정

            # 스타일에 따라 분기
            if style == "배경만 제거" or style == "배경 제거":
                origin_images = service_generate_image_remove_bg(input_image)  # 리턴값이 List[Image]

            elif style == "필터" or style == "이미지 필터":
                buf = BytesIO()
                input_image.save(buf, format="PNG")
                buf.seek(0)
                filtered = await service_cartoon_image(buf.getvalue(), filter)
                origin_images = [filtered]

            else:
                origin_images = [input_image]

            # base64 리스트 변환
            for img in origin_images:
                buffer = BytesIO()
                img.save(buffer, format="PNG")
                buffer.seek(0)
                img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
                output_images.append(img_base64)
        else:
            raise HTTPException(status_code=400, detail="이미지 또는 이미지 URL이 제공되지 않았습니다.")


        # 인스타 문구 처리
        insta_copyright = ''
        detail_content = ''
        if channel == "인스타그램" or channel == "블로그" or channel == "네이버밴드" or channel == "X(트위터)":
            try:

                copyright_prompt = f'''
                    {store_name} 업체의 {channel}을 위한 광고 콘텐츠를 제작하려고 합니다. 
                    업종: {category}
                    세부정보: {customMenu}
                    주소: {district_name}
                    
                    단! "대표 메뉴 앞에 아이콘만 넣고, 메뉴 이름 뒤에는 아이콘을 넣지 않는다." 
                    "위치는 📍로 표현한다."
                    "'\n'으로 문단을 나눠 표현한다."
                '''

                insta_role = f'''
                    1. '{copyright}' 를 100~150자까지 {channel} 인플루언서가 {category}을 소개하는 듯한 느낌으로 광고 문구 만들어줘. 
                    2. 광고 타겟들이 흥미를 갖을만한 내용의 키워드를 뽑아서 검색이 잘 될만한 SEO기반 해시태그도 최소 3개에서 6개까지 생성한다.
                    3. 핵심 고객인 {age}가 선호하는 문체로 작성하되 나이는 표현하지 않는다.
                '''

                insta_copyright = service_generate_content(
                    copyright_prompt,
                    insta_role,
                    detail_content
                )
            except Exception as e:
                print(f"Error occurred: {e}, 인스타 생성 오류")
        

        return JSONResponse(content={
                "copyright": copyright, "origin_image": output_images,
                "title": title, "channel":channel, "style": style, "core_f": age,
                "main": main, "temp" : temp, "detail_category_name" : category,
                "store_name": store_name, "road_name": road_name, "district_name": district_name,
                "insta_copyright" : insta_copyright, "prompt": bg_prompt, "filter_idx": filter,
                "event_title": event_title
            })

    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    

@router.post("/loc/store/info")
def get_store_info(request: StoreInfo):
    try:
        store_info = service_get_store_info(request.store_business_number)
        return JSONResponse(content={
            "store_info": store_info
        })
    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


DB = {}

def ok(u:str)->bool:
    return u.startswith("https://map.naver.com/p/search/")

@router.post("/g")
async def create_short(req: Request):
    body = await req.json()
    long_url = body.get("url", "")
    if not ok(long_url):
        raise HTTPException(400, "Only Naver Map search URLs allowed")
    # https 단축링크 발급(중간지=cleanuri.com)
    async with httpx.AsyncClient(timeout=7) as c:
        r = await c.post(
            "https://cleanuri.com/api/v1/shorten",
            data={"url": long_url},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    short = r.json().get("result_url") if r.status_code == 200 else None
    if not short:
        raise HTTPException(502, "Shortening failed")
    return {"short": short}  # 예: https://cleanuri.com/XXXX