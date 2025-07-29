from fastapi import (
    APIRouter, UploadFile, File, Form, HTTPException, status
)
from app.schemas.ads_app import (
    AutoAppMain,
    AutoApp, AutoAppRegen, AutoAppSave, UserRecoUpdate, AutoGenCopy,
    ManualGenCopy, ManualImageListAIReco, ManualApp,
    UserInfo, UserInfoUpdate, UserRecentRecord, UserRecoDelete,
    ImageList, ImageUploadRequest, StoreInfo, EventGenCopy
)
import io
from fastapi import Request, Body
from PIL import ImageOps
from fastapi.responses import JSONResponse
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
from io import BytesIO
import base64
from PIL import Image
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
    get_store_info as service_get_store_info
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
    female_text = ""
    options = ""
    try:
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
            title, channel, _= parts
        else : 
            title, channel, female_text, _ = parts

 
        detail_content = ""
        # 문구 생성
        try:
            copyright_role = ""
            copyright_prompt = ""
            # print(request.example_image)
            today = datetime.now()
            formattedToday = today.strftime('%Y-%m-%d')

            if title == 3 or "3":
                copyright_role = f'''
                    you are professional writer.
                    - 제목 : 10자 내외 간결하고 호기심을 유발할 수 있는 문구
                    - 내용 : 20자 내외 간결하고 함축적인 내용
                    - 특수기호, 이모티콘은 제외할 것
                '''

                copyright_prompt = f'''
                    {request.store_name} 업체를 위한 광고 컨텐츠를 제작하려고 합니다.
                    {request.detail_category_name}, {formattedToday}, {request.main}, {request.temp}℃
                    주요 고객층: {female_text} 제목 :, 내용 : 형식으로 작성해주세요
                '''
            else:
                copyright_role = f'''
                    you are professional writer.
                    10자 내외 간결하고 호기심을 유발할 수 있는 문구
                '''

                copyright_prompt = f'''
                    {request.store_name} 업체를 위한 문구.
                    {request.detail_category_name}, {formattedToday}, {request.main}, {request.temp}℃
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
        seed_prompt = request.prompt
        style = request.designId
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
                    주요 고객층:  {female_text}

                    주소: {request.road_name}
                    
                    단! "대표 메뉴 앞에 아이콘만 넣고, 메뉴 이름 뒤에는 아이콘을 넣지 않는다." "위치는 📍로 표현한다. 
                    '\n'으로 문단을 나눠 표현한다
                '''

                insta_role = f'''
                    1. '{copyright}' 를 100~150자까지 인플루언서가 {request.detail_category_name} 을 소개하는 듯한 느낌으로 광고 문구 만들어줘 
                    
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
            "title": title, "channel":channel, "style": style, "core_f": female_text,
            "main": request.main, "temp" : request.temp, "detail_category_name" : request.detail_category_name,
            "store_name": request.store_name, "road_name": request.road_name, "store_business_number":request.store_business_number, "prompt" : seed_prompt
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

            if title == 3 or "3":
                copyright_role = f'''
                    you are professional writer.
                    - 제목 : 10자 내외 간결하고 호기심을 유발할 수 있는 문구
                    - 내용 : 20자 내외 간결하고 함축적인 내용
                    - 특수기호, 이모티콘은 제외할 것
                '''

                copyright_prompt = f'''
                    {request.store_name} 업체를 위한 광고 컨텐츠를 제작하려고 합니다.
                    {request.detail_category_name}, {formattedToday}, {request.main}, {request.temp}℃
                    주요 고객층: {female_text} 제목 :, 내용 : 형식으로 작성해주세요
                '''
            else:
                copyright_role = f'''
                    you are professional writer.
                    10자 내외 간결하고 호기심을 유발할 수 있는 문구
                '''

                copyright_prompt = f'''
                    {request.store_name} 업체를 위한 문구.
                    {request.detail_category_name}, {formattedToday}, {request.main}, {request.temp}℃
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
                    주요 고객층: {female_text}

                    주소: {request.road_name}
                    
                    단! "대표 메뉴 앞에 아이콘만 넣고, 메뉴 이름 뒤에는 아이콘을 넣지 않는다." "위치는 📍로 표현한다. 
                    '\n'으로 문단을 나눠 표현한다
                '''

                insta_role = f'''
                    1. '{copyright}' 를 100~150자까지 인플루언서가 {request.detail_category_name} 을 소개하는 듯한 느낌으로 광고 문구 만들어줘 
                    
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
            "main": request.main, "temp" : request.temp, "detail_category_name" : request.detail_category_name,
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
        
        female_text = f"{age}대"
        channel_text = ""

        if channel == "1" : 
            channel_text = "카카오톡"
        elif channel == "2":
            channel_text = "인스타 스토리"
        else :
            channel_text = "인스타 피드"


        detail_content = getattr(request, "ad_text", "") or ""
        # 문구 생성
        try:
            copyright_role = ""
            copyright_prompt = ""
            today = datetime.now()
            formattedToday = today.strftime('%Y-%m-%d')
            if title == 3 or "3":
                copyright_role = f'''
                    you are professional writer.
                    - 제목 : 10자 내외 간결하고 호기심을 유발할 수 있는 문구
                    - 내용 : 20자 내외 간결하고 함축적인 내용
                    - 특수기호, 이모티콘은 제외할 것
                '''

                copyright_prompt = f'''
                    {store_name} 업체를 위한 광고 컨텐츠를 제작하려고 합니다.
                    {detail_category_name}, {formattedToday}, {main}, 주요 고객층: {female_text} 
                    을 바탕으로 제목 :, 내용 : 형식으로 작성해주세요
                '''
            else:
                copyright_role = f'''
                    you are professional writer.
                    10자 내외 간결하고 호기심을 유발할 수 있는 문구
                '''

                copyright_prompt = f'''
                    {store_name} 업체를 위한 문구.
                    {detail_category_name}, {formattedToday}, {main}, 주요 고객층: {female_text}
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
                    주요 고객층: {female_text}

                    주소: {road_name}
                    
                    단! "대표 메뉴 앞에 아이콘만 넣고, 메뉴 이름 뒤에는 아이콘을 넣지 않는다." "위치는 📍로 표현한다. 
                    '\n'으로 문단을 나눠 표현한다
                '''

                insta_role = f'''
                    1. '{copyright}' 를 100~150자까지 인플루언서가 {detail_category_name} 을 소개하는 듯한 느낌으로 광고 문구 만들어줘 
                    
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
            "title": title, "channel":channel, "style": style, "core_f": female_text,
            "main": main, "temp" : temp, "detail_category_name" : detail_category_name,
            "store_name": store_name, "road_name": road_name, "store_business_number": store_business_number, "prompt":prompt, "ad_text" : request.ad_text
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
            today = datetime.now()
            formattedToday = today.strftime('%Y-%m-%d')
            
            
            if channel == "인스타": 
                copyright_prompt = f'''
                    {store_name} 업체를 위한 {subChannel} 에 포스팅할 홍보 내용을 작성해주세요.
                    주소는 {road_name} 이고 홍보할 주제는 {theme} 입니다.
                    {category} 업종의 {formattedToday}, {main}, 
                    주요 고객층: {female_text}을 바탕으로 100자 이내로 작성해주세요.
                    나이는 표현하지 않는다.
                    ex) 오늘 방문하신 고객에게 테이블 당 소주 1병 서비스
                    ex2) 마라 칼국수 신메뉴! 얼얼하게 매운 맛!
                    ex3) 7월 대 오픈! 시원한 냉면 드시러 오세요~
                '''
            else :
                copyright_prompt = f'''
                    {store_name} 업체를 위한 {channel} 에 포스팅할 홍보 내용을 작성해주세요.
                    주소는 {road_name} 이고 홍보할 주제는 {theme} 입니다.
                    {category} 업종의 {formattedToday}, {main}, 
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
        weather= request.weather
        # temp = request.temp
        road_name = request.road_name
        # female_text = f"{age}대"

        detail_content = ""
        copyright_role = f'''
            you are a marketing expert
        '''
        # 문구 생성
        try:
            today = datetime.now()
            formattedToday = today.strftime('%Y-%m-%d')
            
            
            copyright_prompt = f'''
                    {store_name} 업체의 단기 이벤트 내용을 작성해주세요.
                    주소는 {road_name} 이고 이벤트 상품은 {category} 입니다.
                    주소, 이벤트 상품, 오늘({formattedToday})의 날씨({weather})를 바탕으로 100자 이내로 작성해주세요.
                    날씨, 주소는 표현하지 않도록 합니다.
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
        detail_category_name= request.detail_category_name
        prompt = request.prompt
        channel = request.channel
        channel_text = ""

        menu = request.category

        if request.category == '' : 
            menu = request.customMenu

        if channel =="카카오톡":
            channel_text = "1"
            sub_channel = ""
        elif sub_channel == "스토리":
            channel_text = "2"
        else:
            channel_text = "3"

        detail_content = getattr(request, "customText", "") or ""
        # 문구 생성
        try:
            copyright_role = ""
            copyright_prompt = ""

            today = datetime.now()
            formattedToday = today.strftime('%Y-%m-%d')
            if theme == "이벤트":
                copyright_role = f'''
                    you are professional writer.
                    - 제목 : 10자 내외 간결하고 호기심을 유발할 수 있는 문구
                    - 내용 : 20자 내외 간결하고 함축적인 내용
                    - 특수기호, 이모티콘은 제외할 것
                '''

                copyright_prompt = f'''
                    {store_name} 업체를 위한 광고 컨텐츠를 제작하려고 합니다.
                    {menu}, {formattedToday}, {main}, 주요 고객층: {female_text} 
                    을 바탕으로 제목 :, 내용 : 형식으로 작성해주세요
                '''
            else:
                copyright_role = f'''
                    you are professional writer.
                    10자 내외 간결하고 호기심을 유발할 수 있는 문구
                '''

                copyright_prompt = f'''
                    {store_name} 업체를 위한 문구.
                    {menu}, {formattedToday}, {main}, 주요 고객층: {female_text}
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
                    주요 고객층: {female_text}

                    주소: {road_name}
                    
                    단! "대표 메뉴 앞에 아이콘만 넣고, 메뉴 이름 뒤에는 아이콘을 넣지 않는다." "위치는 📍로 표현한다. 
                    '\n'으로 문단을 나눠 표현한다
                '''

                insta_role = f'''
                    1. '{copyright}' 를 100~150자까지 인플루언서가 {menu} 을 소개하는 듯한 느낌으로 광고 문구 만들어줘 
                    
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
            "main": main, "temp" : temp, "menu" : menu, "detail_category_name" : detail_category_name,
            "store_name": store_name, "road_name": road_name, "store_business_number": store_business_number, "prompt" : prompt, "customText" : request.customText
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
        detail_category_name= request.detail_category_name
        prompt = request.prompt
        channel = request.channel
        channel_text = ""

        menu = request.category

        if request.category == '' : 
            menu = request.customMenu

        if channel =="카카오톡":
            channel_text = "1"
            sub_channel = ""
        elif sub_channel == "스토리":
            channel_text = "2"
        else:
            channel_text = "3"

        detail_content = getattr(request, "customText", "") or ""
        # 문구 생성
        try:
            copyright_role = ""
            copyright_prompt = ""

            today = datetime.now()
            formattedToday = today.strftime('%Y-%m-%d')

            copyright_role = f'''
                    당신은 인스타그램, 유투브 등 소셜미디어 광고 전문가입니다. 
                    광고 카피문구와 디자인, 영상등을 능숙하게 다루며 마케팅에 대한 상당한 지식으로 
                    지금까지 수 많은 소상공인 기업들의 마케팅에 도움을 주었습니다.  
                '''

            copyright_prompt = f'''
                    {store_name} 매장의 {channel}를 위한 이벤트 문구를 제작하려고 합니다.
                        - 이벤트 컨셉 : {detail_content} --> 입력이 없다면 자동으로 생성
                        - 주소 : {road_name} 
                        - 날짜 : {formattedToday}
                        - 계절 : 오늘 계절
                        - 핵심 고객 연령대 : {female_text} 
                    이벤트 컨셉에 대한 문구를 작성하되 계절의 특성, 지역(읍, 면, 동)의 특성을 살려서 
                    핵심고객 연령대의 카피문구 선호 스타일을 기반으로 20자 내외의 제목과 30자 내외의 
                    호기심을 유발할 수 있는 {channel} {sub_channel}에 업로드할 이벤트 문구 제목: 내용: 형식으로 작성해주세요.
                    단, 고객의 연령대와 날씨는 직접 언급하지 마세요.
                    
                    ex)
                    제목: 대동로 경동모텔, 8월 평일 할인!
                    내용: 무더위 피한 조용한 휴식처, 주중 20% 혜택 놓치지 마세요.
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
                    주요 고객층: {female_text}

                    주소: {road_name}
                    
                    단! "대표 메뉴 앞에 아이콘만 넣고, 메뉴 이름 뒤에는 아이콘을 넣지 않는다." "위치는 📍로 표현한다. 
                    '\n'으로 문단을 나눠 표현한다
                '''

                insta_role = f'''
                    1. '{copyright}' 를 100~150자까지 인플루언서가 {menu} 을 소개하는 듯한 느낌으로 광고 문구 만들어줘 
                    
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
            "main": main, "temp" : temp, "menu" : menu, "detail_category_name" : detail_category_name,
            "store_name": store_name, "road_name": road_name, "store_business_number": store_business_number, "prompt" : prompt, "customText" : request.customText
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
    try:
        user_id = int(request.user_id)

        exists = service_get_user_profile(user_id)

        if exists:
            success = service_update_user_info(user_id, request)
        else:
            success = service_insert_user_info(user_id, request)

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
    image_url : str = File(None),
    channel: str = Form(...),
    title: str = Form(...),
    age: str = Form(...),
    style: str = Form(...),
    category: str = Form(...),
    store_name: str = Form(...),
    road_name: str = Form(...),
    main: str = Form(...),
    temp: float = Form(...),
):
    try:
        # 문구 생성
        try:
            detail_content = ""
            copyright_role = ""
            copyright_prompt = ""

            today = datetime.now()
            formattedToday = today.strftime('%Y-%m-%d')
            if title == "이벤트" : 
                copyright_role = f'''
                    you are professional writer.
                    - 제목 : 10자 내외 간결하고 호기심을 유발할 수 있는 문구
                    - 내용 : 20자 내외 간결하고 함축적인 내용
                    - 특수기호, 이모티콘은 제외할 것
                '''

                copyright_prompt = f'''
                    {store_name} 업체를 위한 광고 컨텐츠를 제작하려고 합니다.
                    {category}, {formattedToday}, {main}, 주요 고객층: {age} 
                    을 바탕으로 제목 :, 내용 : 형식으로 작성해주세요
                '''
            else:
                copyright_role = f'''
                    you are professional writer.
                    10자 내외 간결하고 호기심을 유발할 수 있는 문구
                '''

                copyright_prompt = f'''
                    {store_name} 업체를 위한 문구.
                    {category}, {formattedToday}, {main}, 주요 고객층: {age}
                    을 바탕으로 15자 이내로 작성해주세요
                '''

            copyright = service_generate_content(
                copyright_prompt,
                copyright_role,
                detail_content
            )

        except Exception as e:
            print(f"Error occurred: {e}, 문구 생성 오류")

        # 이미지 처리 우선순위: image_url > image
        if image_url:
            origin_images = service_generate_bg(image_url)

        elif image:
            input_image = Image.open(BytesIO(await image.read()))
            input_image = ImageOps.exif_transpose(input_image)  # ✅ 회전 보정

            # 예: 스타일에 따라 분기
            if style == "배경만 제거":
                origin_images = service_generate_image_remove_bg(input_image)  # 리턴값이 List[Image]
            else:
                origin_images = [input_image]
        else:
            raise HTTPException(status_code=400, detail="이미지 또는 이미지 URL이 제공되지 않았습니다.")


        # base64 리스트 변환
        output_images = []
        for img in origin_images:
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)
            img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
            output_images.append(img_base64)

        # 인스타 문구 처리
        insta_copyright = ''
        detail_content = ''
        if channel == "인스타그램":
            try:
                today = datetime.now()
                formattedToday = today.strftime('%Y-%m-%d')

                copyright_prompt = f'''
                    {store_name} 업체의 {channel}를 위한 광고 콘텐츠를 제작하려고 합니다. 
                    업종: {category}
                    일시 : {formattedToday}
                    주요 고객층: {age}

                    주소: {road_name}
                    
                    단! "대표 메뉴 앞에 아이콘만 넣고, 메뉴 이름 뒤에는 아이콘을 넣지 않는다." "위치는 📍로 표현한다. 
                    '\n'으로 문단을 나눠 표현한다
                '''

                insta_role = f'''
                    1. '{copyright}' 를 100~150자까지 인플루언서가 {category} 을 소개하는 듯한 느낌으로 광고 문구 만들어줘 
                    
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
        
        return JSONResponse(content={
                "copyright": copyright, "origin_image": output_images,
                "title": title, "channel":channel, "style": style, "core_f": age,
                "main": main, "temp" : temp, "detail_category_name" : category,
                "store_name": store_name, "road_name": road_name, "insta_copyright" : insta_copyright,
            })

    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    

# 이벤트 마케팅 - 내 사진 사용 (이벤트 내용 반영)
@router.post("/event/app/camera")
async def generate_template_event_camera(
    image: UploadFile = File(None),
    image_url : str = File(None),
    channel: str = Form(...),
    title: str = Form(...),
    age: str = Form(...),
    style: str = Form(...),
    customText:str = Form(...),
    category: str = Form(...),
    store_name: str = Form(...),
    road_name: str = Form(...),
    main: str = Form(...),
    temp: float = Form(...),
):
    try:
        # 문구 생성
        try:
            detail_content = customText or ""
            copyright_role = ""
            copyright_prompt = ""

            today = datetime.now()
            formattedToday = today.strftime('%Y-%m-%d')

            copyright_role = f'''
                    당신은 인스타그램, 유투브 등 소셜미디어 광고 전문가입니다. 
                    광고 카피문구와 디자인, 영상등을 능숙하게 다루며 마케팅에 대한 상당한 지식으로 
                    지금까지 수 많은 소상공인 기업들의 마케팅에 도움을 주었습니다.  
                '''

            copyright_prompt = f'''
                    {store_name} 매장의 {channel}를 위한 이벤트 문구를 제작하려고 합니다.
                        - 이벤트 컨셉 : {detail_content} --> 입력이 없다면 자동으로 생성
                        - 주소 : {road_name} 
                        - 날짜 : {formattedToday}
                        - 계절 : 오늘 계절
                        - 핵심 고객 연령대 : {age} 
                    이벤트 컨셉에 대한 문구를 작성하되 계절의 특성, 지역(읍, 면, 동)의 특성을 살려서 
                    핵심고객 연령대의 카피문구 선호 스타일을 기반으로 20자 내외의 제목과 30자 내외의 
                    호기심을 유발할 수 있는 {channel}에 업로드할 이벤트 문구 제목: 내용: 형식으로 작성해주세요.

                    ex)
                    제목: 대동로 경동모텔, 8월 평일 할인!
                    내용: 무더위 피한 조용한 휴식처, 주중 20% 혜택 놓치지 마세요.
                '''

            copyright = service_generate_content(
                copyright_prompt,
                copyright_role,
                detail_content
            )
        except Exception as e:
            print(f"Error occurred: {e}, 문구 생성 오류")

        # 이미지 처리 우선순위: image_url > image
        if image_url:
            origin_images = service_generate_bg(image_url)

        elif image:
            input_image = Image.open(BytesIO(await image.read()))
            input_image = ImageOps.exif_transpose(input_image)  # ✅ 회전 보정

            # 예: 스타일에 따라 분기
            if style == "배경만 제거":
                origin_images = service_generate_image_remove_bg(input_image)  # 리턴값이 List[Image]
            else:
                origin_images = [input_image]
        else:
            raise HTTPException(status_code=400, detail="이미지 또는 이미지 URL이 제공되지 않았습니다.")


        # base64 리스트 변환
        output_images = []
        for img in origin_images:
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)
            img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
            output_images.append(img_base64)

        # 인스타 문구 처리
        insta_copyright = ''
        detail_content = ''
        if channel == "인스타그램":
            try:
                today = datetime.now()
                formattedToday = today.strftime('%Y-%m-%d')

                copyright_prompt = f'''
                    {store_name} 업체의 {channel}를 위한 광고 콘텐츠를 제작하려고 합니다. 
                    업종: {category}
                    일시 : {formattedToday}
                    주요 고객층: {age}

                    주소: {road_name}
                    
                    단! "대표 메뉴 앞에 아이콘만 넣고, 메뉴 이름 뒤에는 아이콘을 넣지 않는다." "위치는 📍로 표현한다. 
                    '\n'으로 문단을 나눠 표현한다
                '''

                insta_role = f'''
                    1. '{copyright}' 를 100~150자까지 인플루언서가 {category} 을 소개하는 듯한 느낌으로 광고 문구 만들어줘 
                    
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
        
        return JSONResponse(content={
                "copyright": copyright, "origin_image": output_images,
                "title": title, "channel":channel, "style": style, "core_f": age,
                "main": main, "temp" : temp, "detail_category_name" : category,
                "store_name": store_name, "road_name": road_name, "insta_copyright" : insta_copyright,
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
