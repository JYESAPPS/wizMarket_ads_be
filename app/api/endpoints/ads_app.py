from fastapi import (
    APIRouter, UploadFile, File, Form, HTTPException, status
)
from app.schemas.ads_app import (
    AutoApp, AutoAppRegen, AutoAppSave,
    ManualGenCopy, ManualImageListAIReco, ManualApp,
    UserInfo, UserInfoUpdate
)
from fastapi import Request, Body
from fastapi.responses import JSONResponse
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
from io import BytesIO
import base64
import logging
import re
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
    update_user_info as service_update_user_info
)

router = APIRouter()
logger = logging.getLogger(__name__)

# AI 생성 자동
@router.post("/auto/app")
def generate_template(request: AutoApp):
    try:
        # GPT 로 옵션 값 자동 생성
        try:
            options = service_generate_option(
                request
            )
        except Exception as e:
            print(f"Error occurred: {e}, 문구 생성 오류")

        raw = options.replace(",", "-").replace(" ", "")  # "3-1-4"
        parts = raw.split("-")  # ["3", "1", "4"]

        title, channel, style = parts

        male_text = service_parse_age_gender_info(request.commercial_district_max_sales_m_age)
        female_text = service_parse_age_gender_info(request.commercial_district_max_sales_f_age)

        detail_content = ""
        # 문구 생성
        try:
            copyright_role = ""
            copyright_prompt = ""
            # print(request.example_image)
            today = datetime.now()
            formattedToday = today.strftime('%Y-%m-%d')
            if title == 3 or "3":
                copyright_role : f'''
                    you are professional writer.
                    - 제목 : 10자 내외 간결하고 호기심을 유발할 수 있는 문구
                    - 내용 : 20자 내외 간결하고 함축적인 내용
                    - 특수기호, 이모티콘은 제외할 것
                '''

                copyright_prompt = f'''
                    {request.store_name} 업체를 위한 광고 컨텐츠를 제작하려고 합니다.
                    {request.detail_category_name}, {formattedToday}, {request.main}, {request.temp}℃
                    주요 고객층: {male_text}, {female_text} 제목 :, 내용 : 형식으로 작성해주세요
                '''
            else:
                copyright_role : f'''
                    you are professional writer.
                    10자 내외 간결하고 호기심을 유발할 수 있는 문구
                '''

                copyright_prompt = f'''
                    {request.store_name} 업체를 위한 문구.
                    {request.detail_category_name}, {formattedToday}, {request.main}, {request.temp}℃
                    주요 고객층: {male_text}, {female_text}을 바탕으로 15자 이내로 작성해주세요
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
                seed_prompt
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
                    일시 : {formattedToday}
                    오늘날씨 : {request.main}, {request.temp}℃
                    주요 고객층: {male_text}, {female_text}

                    주소: {request.road_name}
                    
                    단! "대표 메뉴 앞에 아이콘만 넣고, 메뉴 이름 뒤에는 아이콘을 넣지 않는다." "위치는 📍로 표현한다. 
                    '\n'으로 문단을 나눠 표현한다
                '''

                insta_role = f'''
                    1. '{copyright}' 를 100~150자까지 인플루언서가 {request.detail_category_name} 을 소개하는 듯한 느낌으로 광고 문구 만들어줘 
                    
                    2.광고 타겟들이 흥미를 갖을만한 내용의 키워드를 뽑아서 검색이 잘 될만한 해시태그도 최소 3개에서 6개까지 생성한다
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
            "title": title, "channel":channel, "style": style, "core_m": male_text, "core_f": female_text,
            "main": request.main, "temp" : request.temp, "detail_category_name" : request.detail_category_name,
            "store_name": request.store_name, "road_name": request.road_name, "store_business_number":request.store_business_number
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
def get_style_image():
    image_list = service_get_style_image()

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
        
        female_text = f"여성 {age}대"
        channel_text = ""

        if channel == "1" : 
            channel_text = "카카오톡"
        elif channel == "2":
            channel_text = "인스타 스토리"
        else :
            channel_text = "인스타 피드"


        detail_content = ""
        # 문구 생성
        try:
            copyright_role = ""
            copyright_prompt = ""

            today = datetime.now()
            formattedToday = today.strftime('%Y-%m-%d')
            if channel == 3 or "3":
                copyright_role : f'''
                    you are professional writer.
                    - 제목 : 10자 내외 간결하고 호기심을 유발할 수 있는 문구
                    - 내용 : 20자 내외 간결하고 함축적인 내용
                    - 특수기호, 이모티콘은 제외할 것
                '''

                copyright_prompt = f'''
                    {store_name} 업체를 위한 광고 컨텐츠를 제작하려고 합니다.
                    {detail_category_name}, {formattedToday}, {main}, {temp}℃, 주요 고객층: {female_text} 
                    을 바탕으로 제목 :, 내용 : 형식으로 작성해주세요
                '''
            else:
                copyright_role : f'''
                    you are professional writer.
                    10자 내외 간결하고 호기심을 유발할 수 있는 문구
                '''

                copyright_prompt = f'''
                    {store_name} 업체를 위한 문구.
                    {detail_category_name}, {formattedToday}, {main}, {temp}℃, 주요 고객층: {female_text}
                    을 바탕으로 15자 이내로 작성해주세요
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
                channel,
                copyright,
                detail_category_name,
                prompt
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
                    {store_name} 업체의 {channel_text}를 위한 광고 콘텐츠를 제작하려고 합니다. 
                    업종: {detail_category_name}
                    일시 : {formattedToday}
                    오늘날씨 : {main}, {temp}℃
                    주요 고객층: {female_text}

                    주소: {road_name}
                    
                    단! "대표 메뉴 앞에 아이콘만 넣고, 메뉴 이름 뒤에는 아이콘을 넣지 않는다." "위치는 📍로 표현한다. 
                    '\n'으로 문단을 나눠 표현한다
                '''

                insta_role = f'''
                    1. '{copyright}' 를 100~150자까지 인플루언서가 {detail_category_name} 을 소개하는 듯한 느낌으로 광고 문구 만들어줘 
                    
                    2.광고 타겟들이 흥미를 갖을만한 내용의 키워드를 뽑아서 검색이 잘 될만한 해시태그도 최소 3개에서 6개까지 생성한다
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
            "title": title, "channel":channel, "style": style, "core_f": female_text,
            "main": main, "temp" : temp, "detail_category_name" : detail_category_name,
            "store_name": store_name, "road_name": road_name, "store_business_number": store_business_number
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
def insert_upload_record(request: AutoAppSave):
    try:
        success = service_insert_upload_record(request)
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




# AI 생성 수동 - 초기 값 가져오기
@router.post("/manual/ai/reco")
def manual_ai_reco(request : AutoApp):
    try:
        options = service_generate_option(
            request
        )
    except Exception as e:
        print(f"Error occurred: {e}, 문구 생성 오류")

    raw = options.replace(",", "-").replace(" ", "")  # "3-1-4"
    parts = raw.split("-")  # ["3", "1", "4"]

    title, channel, _ = parts

    female_text = service_parse_age_gender_info(request.commercial_district_max_sales_f_age)

    return JSONResponse(content={
        "title" : title, 
        "channel" : channel, 
        "female_text" : female_text
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
        female_text = f"여성 {age}대"

        detail_content = ""
        copyright_role = f'''
            you are a marketing expert
        '''
        # 문구 생성
        try:
            today = datetime.now()
            formattedToday = today.strftime('%Y-%m-%d')
            
            
            if channel == "인스타": 
                copyright_prompt = f'''
                    {store_name} 업체를 위한 {subChannel} 에 포스팅할 홍보 내용을 작성해주세요.
                    주소는 {road_name} 이고 홍보할 주제는 {theme} 입니다.
                    {category} 업종의 {formattedToday}, {main}, {temp}℃, 
                    주요 고객층: {female_text}을 바탕으로 100자 이내로 작성해주세요.
                    ex) 오늘 방문하신 고객에게 테이블 당 소주 1병 서비스
                    ex2) 마라 칼국수 신메뉴! 얼얼하게 매운 맛!
                    ex3) 7월 대 오픈! 시원한 냉면 드시러 오세요~
                '''
            else :
                copyright_prompt = f'''
                    {store_name} 업체를 위한 {channel} 에 포스팅할 홍보 내용을 작성해주세요.
                    주소는 {road_name} 이고 홍보할 주제는 {theme} 입니다.
                    {category} 업종의 {formattedToday}, {main}, {temp}℃, 
                    주요 고객층: {female_text}을 바탕으로 100자 이내로 작성해주세요.
                    ex) 오늘 방문하신 고객에게 테이블 당 소주 1병 서비스
                    ex2) 마라 칼국수 신메뉴! 얼얼하게 매운 맛!
                    ex3) 7월 대 오픈! 시원한 냉면 드시러 오세요~
                '''

            copyright = service_generate_content(
                copyright_prompt,
                copyright_role,
                detail_content
            )
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

# AI 생성 수동 - 이미지 리스트와 추천 스타일 가져오기
@router.post("/manual/style/image")
def get_style_image_ai_reco(request: ManualImageListAIReco):
    image_list = service_get_style_image()
    raw_ai_style = sercvice_get_style_image_ai_reco(request)

    # 숫자만 추출
    match = re.match(r"(\d+)", str(raw_ai_style))
    ai_style = int(match.group(1)) if match else None

    return JSONResponse(content={
        "image_list": image_list,
        "ai_style": ai_style
    })

# AI 생서 수동 - 선택 한 값들로 이미지 생성
@router.post("/manual/app")
def generate_template_manual(request : ManualApp):
    try:
        store_business_number= request.store_business_number
        main= request.main
        temp= request.temp
        style=request.style
        age= request.age
        sub_channel= request.subChannel
        theme= request.theme
        store_name= request.store_name
        road_name= request.road_name
        detail_category_name= request.detail_category_name
        prompt = request.prompt
        
        female_text = f"여성 {age}대"
        channel_text = ""

        menu = request.category

        if request.category == '' : 
            menu = request.customMenu

        if not sub_channel:
            channel_text = "1"
        elif sub_channel == "스토리":
            channel_text = "2"
        else:
            channel_text = "3"

        detail_content = ""
        # 문구 생성
        try:
            copyright_role = ""
            copyright_prompt = ""

            today = datetime.now()
            formattedToday = today.strftime('%Y-%m-%d')
            if channel_text == 3 or "3":
                copyright_role : f'''
                    you are professional writer.
                    - 제목 : 10자 내외 간결하고 호기심을 유발할 수 있는 문구
                    - 내용 : 20자 내외 간결하고 함축적인 내용
                    - 특수기호, 이모티콘은 제외할 것
                '''

                copyright_prompt = f'''
                    {store_name} 업체를 위한 광고 컨텐츠를 제작하려고 합니다.
                    {menu}, {formattedToday}, {main}, {temp}℃, 주요 고객층: {female_text} 
                    을 바탕으로 제목 :, 내용 : 형식으로 작성해주세요
                '''
            else:
                copyright_role : f'''
                    you are professional writer.
                    10자 내외 간결하고 호기심을 유발할 수 있는 문구
                '''

                copyright_prompt = f'''
                    {store_name} 업체를 위한 문구.
                    {menu}, {formattedToday}, {main}, {temp}℃, 주요 고객층: {female_text}
                    을 바탕으로 15자 이내로 작성해주세요
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
                menu,
                prompt
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
            
            if channel_text == "3":
                today = datetime.now()
                formattedToday = today.strftime('%Y-%m-%d')

                copyright_prompt = f'''
                    {store_name} 업체의 인스타그램 피드를 위한 광고 콘텐츠를 제작하려고 합니다. 
                    업종: {menu}
                    일시 : {formattedToday}
                    오늘날씨 : {main}, {temp}℃
                    주요 고객층: {female_text}

                    주소: {road_name}
                    
                    단! "대표 메뉴 앞에 아이콘만 넣고, 메뉴 이름 뒤에는 아이콘을 넣지 않는다." "위치는 📍로 표현한다. 
                    '\n'으로 문단을 나눠 표현한다
                '''

                insta_role = f'''
                    1. '{copyright}' 를 100~150자까지 인플루언서가 {menu} 을 소개하는 듯한 느낌으로 광고 문구 만들어줘 
                    
                    2.광고 타겟들이 흥미를 갖을만한 내용의 키워드를 뽑아서 검색이 잘 될만한 해시태그도 최소 3개에서 6개까지 생성한다
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
        
        style = str(style)

        # 문구와 합성된 이미지 반환
        return JSONResponse(content={
            "copyright": copyright, "origin_image": output_images, "insta_copyright" : insta_copyright,
            "title": title, "channel":channel_text, "style": style, "core_f": female_text,
            "main": main, "temp" : temp, "detail_category_name" : menu,
            "store_name": store_name, "road_name": road_name, "store_business_number": store_business_number
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
        info, record = service_get_user_info(user_id)

        return JSONResponse(content={
            "info": info,
            "record": record
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
    try:
        user_id = int(request.user_id)
        success = service_update_user_info(user_id, request)

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