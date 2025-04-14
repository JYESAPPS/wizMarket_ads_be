from fastapi import (
    APIRouter, UploadFile, File, Form, HTTPException, status
)
from app.schemas.ads import (
    AdsList, AdsInitInfoOutPut,
    AdsGenerateContentOutPut, AdsContentRequest,
    AdsGenerateImageOutPut, AdsImageRequest,
    AdsDeleteRequest, AdsContentNewRequest, AuthCallbackRequest,
    AdsTestRequest, AdsSuggestChannelRequest, AdsImageTestFront, AdsUploadVideoInsta,
    AdsDrawingModelTest, AdsTemplateRequest, KaKaoTempInsert, KaKaoTempGet, AdsTemplateSeedImage,
    MusicGet, Story, 
)
from fastapi import Request, Body
from PIL import Image, ImageOps
import logging
import base64
import io
from typing import List
import requests
from google_auth_oauthlib.flow import Flow
from app.service.ads import (
    select_ads_init_info as service_select_ads_init_info,
    insert_ads as service_insert_ads,
    delete_status as service_delete_status,
    update_ads as service_update_ads,
)
from app.service.ads_generate import (
    generate_content as service_generate_content,
    generate_image as service_generate_image,
    generate_video as service_generate_video,
    generate_new_content as service_generate_new_content,
    generate_old_content as service_generate_old_content,
    generate_claude_content as service_generate_claude_content,
    generate_image_mid as service_generate_image_mid,
    generate_add_text_to_video as service_generate_add_text_to_video,
    generate_image_imagen3  as service_generate_image_imagen3,
    generate_image_imagen3_template as service_generate_image_imagen3_template,
    generate_image_vision as service_generate_image_vision
)
from app.service.ads_upload import (
    upload_story_ads as service_upload_story_ads,
    upload_feed_ads as service_upload_feed_ads,
    upload_mms_ads as service_upload_mms_ads,
    upload_youtube_ads as service_upload_youtube_ads,
    upload_get_auth_url as service_upload_get_auth_url,
    upload_insta_info_ads as service_upload_insta_info_ads,
    upload_story_video_ads as service_upload_story_video_ads,
    upload_feed_video_ads as service_upload_feed_video_ads,
    upload_reels_video_ads as service_upload_reels_video_ads,
)
from app.service.ads_generate_by_title import (
    combine_ads_1_1 as service_combine_ads_1_1,
    combine_ads_4_7 as service_combine_ads_4_7,
    combine_ads_7_4 as service_combine_ads_7_4,
)
# from app.service.ads_upload_naver import upload_naver_ads as service_upload_naver_ads
from app.service.ads_generate_test import (
    generate_image_stable as service_generate_image_stable, 
    generate_image_dalle as service_generate_image_dalle,
    generate_image_mid_test as service_generate_image_mid_test,
    generate_image_imagen_test as service_generate_image_imagen_test,
    generate_image_remove_bg as service_generate_image_remove_bg,
    generate_image_remove_bg_free as service_generate_image_remove_bg_free,
    generate_test_generate_video as service_generate_test_generate_video,
    generate_test_generate_bg as service_generate_test_generate_bg,
    generate_test_generate_music as service_generate_test_generate_music,
    generate_test_generate_lyrics as service_generate_test_generate_lyrics,
    generate_test_generate_story as service_generate_test_generate_story,
    send_mail as service_send_mail,
)
from app.service.ads_image_treat import (
    trat_image_turn as service_trat_image_turn
)

from app.service.ads_get_outer_info import (
    get_insta_info as service_get_insta_info,
    get_naver_info as service_get_naver_info
)


import redis
import traceback
from fastapi.responses import JSONResponse
from pathlib import Path
import shutil
from typing import Optional
from dotenv import load_dotenv
from datetime import datetime
import os
import uuid
import json
from io import BytesIO
from rembg import remove
import random
import string


router = APIRouter()
logger = logging.getLogger(__name__)

ROOT_PATH = Path(os.getenv("ROOT_PATH"))
IMAGE_DIR = Path(os.getenv("IMAGE_DIR"))
VIDEO_DIR = Path(os.getenv("VIDEO_PATH"))
FULL_PATH = ROOT_PATH / IMAGE_DIR.relative_to("/") / "ads"
FULL_PATH.mkdir(parents=True, exist_ok=True)


redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)


# 매장 리스트에서 모달창 띄우기
@router.post("/select/init/info", response_model=AdsInitInfoOutPut)
def select_ads_init_info(store_business_number: str, request: Request):
    # 쿼리 매개변수로 전달된 store_business_number 값 수신
    try:
        # 요청 정보 출력
        # logger.info(f"Request received from {request.client.host}:{request.client.port}")
        # logger.info(f"Request headers: {request.headers}")
        # logger.info(f"Request path: {request.url.path}")
        return service_select_ads_init_info(store_business_number)
    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    

# 광고 채널 추천
@router.post("/suggest/channel")
def select_suggest_channel(request: AdsSuggestChannelRequest):
    # 쿼리 매개변수로 전달된 store_business_number 값 수신
    try:
        gpt_role = '''
            당신은 온라인 광고 전문가 입니다. 
            오프라인 점포를 하는 매장에서 다음과 같은 내용으로 홍보 콘텐츠를 제작하여 포스팅하려고 합니다. 
            이 매장에서 가장 좋은 홍보 방법 무엇이 좋겠습니까? 
            제시된 상황에 따라 채널과  디자인 스타일 중에 하나를 선택해주고 그 이유와 홍보전략을 200자 내외로 작성해주세요.
        '''

        prompt = f'''
            매장명 : {request.store_name}
            주소 : {request.road_name}
            업종 : {request.tag}
            주 고객층 : {request.male_base}, {request.female_base}
            홍보 주제 : {request.title}
            홍보채널 : 문자메시지, 인스타그램 스토리, 인스타그램 피드, 네이버 블로그, 
                        카카오톡, 자사 홈페이지, 페이스북, 디스코드, 트위터, 미디엄, 네이버 밴드, 캐치테이블, 배달의 민족
            디자인 스타일 : 3D 일러스트(3d, 클레이메이션, 픽셀디자인, 레고스타일, 닌텐도 스타일, paper craft, 디오라마, isometric), 
                            실사 사진, 캐릭터.만화, 레트로 감성, AI로 생성한 남녀모델, 예술(르노와르, 피카소, 고흐 등) 
        '''
        detail_contet = ""

        channel = service_generate_content(
            prompt,
            gpt_role,
            detail_contet
        )
        return {"chan": channel}
    except Exception as e:
        print(f"Error occurred: {e}, 문구 생성 오류")

# 프론트에서 이미지 처리 테스트
# @router.post("/generate/exist/image/test")
# def generate_image_with_test(request: AdsImageTestFront):
#     try:
#         # 문구 생성
#         try:
#             today = datetime.now()
#             formattedToday = today.strftime('%Y-%m-%d (%A) %H:%M')

#             copyright_prompt = f'''
#                 매장명 : {request.store_name}
#                 주소 : {request.road_name}
#                 업종 : {request.tag}
#                 날짜 : {formattedToday}
#                 날씨 : {request.weather}, {request.temp}℃
#                 매출이 가장 높은 남성 연령대 : {request.male_base}
#                 매출이 가장 높은 여성 연령대 : {request.female_base}
#             '''
#             copyright = service_generate_content(
#                 copyright_prompt,
#                 request.gpt_role,
#                 request.detail_content
#             )
#         except Exception as e:
#             print(f"Error occurred: {e}, 문구 생성 오류")

#         # 문구 반환
#         return JSONResponse(content={"copyright": copyright})

#     except HTTPException as http_ex:
#         logger.error(f"HTTP error occurred: {http_ex.detail}")
#         raise http_ex
#     except Exception as e:
#         error_msg = f"Unexpected error while processing request: {str(e)}"
#         logger.error(error_msg)
#         raise HTTPException(status_code=500, detail=error_msg)



# 업로드 된 이미지 처리
@router.post("/generate/exist/image")
def generate_image_with_text(
        store_name: str = Form(...),
        road_name: str = Form(...),
        tag: str = Form(...),
        weather: str = Form(...),
        temp: float = Form(...),
        male_base: str = Form(...),
        female_base: str = Form(...),
        gpt_role: str = Form(...),
        detail_content: str = Form(...),
        use_option: str = Form(...),
        title: str = Form(...),
        image: UploadFile = File(...)
    ):
    images_list = []
    try:
        # 문구 생성
        try:
            today = datetime.now()
            formattedToday = today.strftime('%Y-%m-%d (%A) %H:%M')

            copyright_prompt = f'''
                매장명 : {store_name}
                주소 : {road_name}
                업종 : {tag}
                날짜 : {formattedToday}
                날씨 : {weather}, {temp}℃
                매출이 가장 높은 남성 연령대 : {male_base}
                매출이 가장 높은 여성 연령대 : {female_base}
            '''
            copyright = service_generate_content(
                copyright_prompt,
                gpt_role,
                detail_content
            )
        except Exception as e:
            print(f"Error occurred: {e}, 문구 생성 오류")

        # 이미지와 문구 합성
        try:
            pil_image = Image.open(image.file)
            pil_image = ImageOps.exif_transpose(pil_image)
            image_width, image_height = pil_image.size
            if use_option == '인스타그램 피드':
                if title == '이벤트':
                    # 서비스 레이어 호출 (Base64 이미지 반환)
                    image1, image2 = service_combine_ads_1_1(store_name, road_name, copyright, title, image_width, image_height, pil_image)
                    images_list.extend([image1, image2])
                elif title == '매장 소개':
                    # 서비스 레이어 호출 (Base64 이미지 반환)
                    image1 = service_combine_ads_1_1(store_name, road_name, copyright, title, image_width, image_height, pil_image)
                    images_list.append(image1)
            elif use_option == '인스타그램 스토리' or use_option == '문자메시지' or use_option == '카카오톡' or use_option == '네이버 블로그':
                if title == '이벤트':
                    # 서비스 레이어 호출 (Base64 이미지 반환)
                    image1, image2, image3 = service_combine_ads_4_7(store_name, road_name, copyright, title, image_width, image_height, pil_image, weather, tag)
                    images_list.extend([image1, image2, image3])
                elif title == '매장 소개':
                    # 서비스 레이어 호출 (Base64 이미지 반환)
                    image1, image2, image3 = service_combine_ads_4_7(store_name, road_name, copyright, title, image_width, image_height, pil_image, weather, tag)
                    images_list.extend([image1, image2, image3])
                elif title == '상품소개':
                    # 서비스 레이어 호출 (Base64 이미지 반환)
                    image1 = service_combine_ads_4_7(store_name, road_name, copyright, title, image_width, image_height, pil_image, weather, tag)
                    images_list.append(image1)

        except Exception as e:
            print(f"Error occurred: {e}, 이미지 합성 오류")
        # 문구와 합성된 이미지 반환
        return JSONResponse(content={"copyright": copyright, "images": images_list})

    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


# 업로드 된 이미지 처리 + 배경 제거
@router.post("/generate/exist/image/remove/background")
def generate_image_with_text_remove_background(
        store_name: str = Form(...),
        road_name: str = Form(...),
        tag: str = Form(...),
        weather: str = Form(...),
        temp: float = Form(...),
        male_base: str = Form(...),
        female_base: str = Form(...),
        gpt_role: str = Form(...),
        detail_content: str = Form(...),
        use_option: str = Form(...),
        title: str = Form(...),
        image: UploadFile = File(...)
    ):
    images_list = []
    try:
        # 문구 생성
        try:
            today = datetime.now()
            formattedToday = today.strftime('%Y-%m-%d (%A) %H:%M')
            if title == '이벤트':
                copyright_prompt = f'''
                    {store_name} 업체의 {use_option} 위한 광고 컨텐츠를 제작하려고 합니다.
                    {tag}, {formattedToday}, {weather}, {temp}℃, {detail_content}
                    핵심 고객 연령대 : {male_base}, {female_base} 제목 :, 내용 : 형식으로 작성해주세요
                '''
            else:
                copyright_prompt = f'''
                    {store_name} 업체의 {use_option} 위한 광고 컨텐츠를 제작하려고 합니다.
                    {tag}, {formattedToday}, {weather}, {temp}℃, {detail_content}
                    핵심 고객 연령대 : {male_base}, {female_base} 내용 15자 이내로 작성해주세요
            '''

            copyright = service_generate_content(
                copyright_prompt,
                gpt_role,
                detail_content
            )
        except Exception as e:
            print(f"Error occurred: {e}, 문구 생성 오류")


        # 이미지 배경 제거
        try:
            pil_image = Image.open(image.file)

            # EXIF 데이터 확인 및 회전 보정
            pil_image = service_trat_image_turn(pil_image)

            # PIL 이미지를 바이트로 변환하여 rembg에 전달
            image_bytes = BytesIO()
            pil_image.save(image_bytes, format='PNG')  # 이미지 포맷을 PNG로 저장
            image_bytes.seek(0)
            
            # 배경 제거
            output_bytes = remove(image_bytes.getvalue())  # remove 함수에 바이트 데이터 전달
            
            # 배경이 제거된 이미지를 다시 PIL 객체로 변환
            pil_image_no_bg = Image.open(BytesIO(output_bytes))

            output_images = []
            for image in pil_image:  # 리스트의 각 이미지를 순회
                buffer = BytesIO()
                image.save(buffer, format="PNG")  # 이미지 저장
                buffer.seek(0)
                
                # Base64 인코딩 후 리스트에 추가
                output_images.append(base64.b64encode(buffer.getvalue()).decode("utf-8"))

        except Exception as e:
            print(f"Error occurred: {e}, 이미지 합성 오류")

        

        # 이미지와 문구 합성
        try:
            # pil_image = Image.open(image.file)
            # pil_image = ImageOps.exif_transpose(pil_image)
            # image_width, image_height = pil_image.size
            pil_image = ImageOps.exif_transpose(pil_image_no_bg)
            image_width, image_height = pil_image.size
            if use_option == '인스타그램 피드':
                if title == '이벤트':
                    # 서비스 레이어 호출 (Base64 이미지 반환)
                    image1, image2, image3 = service_combine_ads_1_1(store_name, road_name, copyright, title, image_width, image_height, pil_image, weather, tag)
                    images_list.extend([image1, image2, image3])
                elif title == '매장 소개':
                    # 서비스 레이어 호출 (Base64 이미지 반환)
                    image1, image2, image3 = service_combine_ads_1_1(store_name, road_name, copyright, title, image_width, image_height, pil_image, weather, tag)
                    images_list.extend([image1, image2, image3])
            elif use_option == '인스타그램 스토리' or use_option == '문자메시지' or use_option == '카카오톡' or use_option == '네이버 블로그':
                if title == '이벤트':
                    # 서비스 레이어 호출 (Base64 이미지 반환)
                    image1, image2, image3, image4, image5 = service_combine_ads_4_7(store_name, road_name, copyright, title, image_width, image_height, pil_image, weather, tag)
                    images_list.extend([image1, image2, image3, image4, image5])
                elif title == '매장 소개':
                    # 서비스 레이어 호출 (Base64 이미지 반환)
                    image1, image2, image4, image5, image6, image7 = service_combine_ads_4_7(store_name, road_name, copyright, title, image_width, image_height, pil_image, weather, tag)
                    images_list.extend([image1, image2, image4, image5, image6, image7])
                elif title == '상품소개':
                    # 서비스 레이어 호출 (Base64 이미지 반환)
                    image1 = service_combine_ads_4_7(store_name, road_name, copyright, title, image_width, image_height, pil_image, weather, tag)
                    images_list.append(image1)

        except Exception as e:
            print(f"Error occurred: {e}, 이미지 합성 오류")



        try:
            insta_copyright = ''
            
            if use_option == '인스타그램 피드':
                today = datetime.now()
                formattedToday = today.strftime('%Y-%m-%d (%A) %H:%M')

                copyright_prompt = f'''
                    {store_name} 업체의 {title}를 위한 광고 콘텐츠를 제작하려고 합니다. 
                    업종: {tag}
                    세부정보 : {detail_content}
                    일시 : {formattedToday}
                    오늘날씨 : {weather}, {temp}℃
                    핵심고객: 
                    매출이 가장 높은 남성 연령대 : 남자 {male_base}
                    매출이 가장 높은 여성 연령대 : 여자 {female_base}


                    주소: {road_name}
                    
                    단! "대표 메뉴 앞에 아이콘만 넣고, 메뉴 이름 뒤에는 아이콘을 넣지 않는다." "위치는 📍로, 영업시간은 🕒로 표현한다. 
                    '\n'으로 문단을 나눠 표현한다
                '''

                insta_role = '''
                    1. '{copyright}' 를 100~150자까지 {request.title} 인플루언서가 $대분류$ 을 소개하는 듯한 느낌으로 광고 문구 만들어줘 
                    {request.title}에 광고할 타겟은 핵심 연령층으로 {request.title}에 어울리는 내용을 생성한다. 
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
        return JSONResponse(content={"copyright": copyright, "images": images_list, "insta_copyright" : insta_copyright})

    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)





# AI 생성용 이미지 처리
@router.post("/upload/content")
def generate_upload(request: AdsTestRequest):
    try:
        # 문구 생성
        try:
            today = datetime.now()
            formattedToday = today.strftime('%Y-%m-%d (%A) %H:%M')

            copyright_prompt = f'''
                매장명 : {request.store_name}
                주소 : {request.road_name}
                업종 : {request.tag}
                날짜 : {formattedToday}
                날씨 : {request.weather}, {request.temp}℃
                매출이 가장 높은 남성 연령대 : {request.male_base}
                매출이 가장 높은 여성 연령대 : {request.female_base}
            '''

            copyright = service_generate_content(
                copyright_prompt,
                request.gpt_role,
                request.detail_content
            )
        except Exception as e:
            print(f"Error occurred: {e}, 문구 생성 오류")
        
        # 스토리 생성
        try:
            korean_story_prompt = f"""
                - 세부업종 : {request.tag}
                - 날짜 : {formattedToday}
                - 날씨 : {request.weather}, {request.temp}℃
                - 매출이 가장 높은 남성 연령대 : {request.male_base}
                - 매출이 가장 높은 여성 연령대 : {request.female_base}
                - 장소 : {request.road_name}
                - 추가정보 내용 : {request.detail_content}
                - 홍보채널 : {request.use_option}
                - 홍보채널에 포스팅되는 이미지나 동영상의 특징을 살려서 매장의 특성과 브랜드를 잘 느낄 수 있을것. 
                - 주요고객이 오늘의 날씨와 환경, 날짜, 장소의 특징을 감안하여 매장에 대한 호감도를 느낄 수 있는 스토리를 작성할 것
                - 매장의 세부업종에 따른 이미지 컨셉을 도출하여 스토리에 접목시킬 것
            """
            korean_story_gpt_role = f'''
                당신은 광고를 제작하는 크리에이티브 디자이너 입니다. 
                멋진 온라인 광고 콘텐츠를 제작하기 위해 당신이 고려해야할 것은 
                클라이언트 사업의 업종, 매장위치, 핵심고객, 오늘의 날씨, 홍보주제, 온라인 홍보채널 등을 고려하여 
                멋지고 창의적이고 때로는 엉뚱한 상상력을 발휘할 수 있는 스토리를 한 장의 이미지로 나타내려고 합니다. 
                
                핵심고객의 나이가 20대, 30대라면 동물을 테마로 한 엉뚱한 상상력을 발휘해도 좋고 40대라면 일상에서 일어나는 일들을 테마로 하고, 
                50대면 가족과의 화합을 테마로하고, 60대 이상은 과거의 추억을 떠올릴 수 있는 테마로 잡으면 좋겠습니다. 
                주 고객층에서 남성은 재치있는 유머를 보여주고 여성은 아기자기하고 귀여운 느낌으로 작성해주세요. 
                아래의 클라이언트가 의뢰하는 내용으로 스토리를 만들어주세요.
            '''

            detail_content = "값 없음"

            korean_story = service_generate_content(
                korean_story_prompt,
                korean_story_gpt_role,
                detail_content
            )
        except Exception as e:
            print(f"Error occurred: {e}, 스토리 생성 오류")

        # 스토리를 바탕으로 한 이미지 프롬프트 생성
        try:
            korean_image_gpt_role = f'''
                - 이 스토리로 dalle AI를 통해 {request.use_option}에 업로드할 이미지를 생성하기 위한 프롬프트를 작성해주세요. 
                - 프롬프트를 작성할때 스토리에 어울리는 이미지 스타일, 구도, 방식, 남성 핵심 고객층인 {request.male_base}과 여성 핵심 고객층인 {request.female_base}의 
                감성에 어울리는 이미지를 생성할 수 있도록 작성해주세요.

                이미지 스타일 사례
                - 3D 그래픽, 2D그래픽, 일러스트레이션, 페이퍼 크라프트, 일본 애니메이션, 만화책, 사진, 디오라마, 아이소메트릭, 광고포스터, 판타지, 타이포그라피 등
            '''

            detail_content = "값 없음"

            korean_image_prompt = service_generate_content(
                korean_story,
                korean_image_gpt_role,
                detail_content
            )
        except Exception as e:
            print(f"Error occurred: {e}, 이미지 생성 오류")

        # 이미지 생성
        try:
            if request.ai_model_option == 'midJouney':
                origin_image = service_generate_image_mid(
                    request.use_option,
                    korean_image_prompt
                )
            elif request.ai_model_option == "imagen3":
                origin_image = service_generate_image_imagen3(
                    request.use_option,
                    korean_image_prompt
                )
            else:
                origin_image = service_generate_image(
                    request.use_option,
                    korean_image_prompt
                )
        except Exception as e:
            print(f"Error occurred: {e}, 이미지 생성 오류")

        # 사이즈 조정 및 합성
        images_list = []
        try:
            for i, img in enumerate(origin_image):
                image_width, image_height = img.size  # 이미지 크기 가져오기
                print(f"Image {i + 1}: Width = {image_width}, Height = {image_height}")

                if request.use_option == '인스타그램 피드':
                    if request.title == '이벤트':
                        # 서비스 레이어 호출 (Base64 이미지 반환)
                        image1, image2 = service_combine_ads_1_1(request.store_name, request.road_name, copyright, request.title, image_width, image_height, img)
                        images_list.extend([image1, image2])
                    elif request.title == '매장 소개':
                        # 서비스 레이어 호출 (Base64 이미지 반환)
                        image1 = service_combine_ads_1_1(request.store_name, request.road_name, copyright, request.title, image_width, image_height, img)
                        images_list.append(image1)
                elif request.use_option == '인스타그램 스토리' or request.use_option == '문자메시지' or request.use_option == '카카오톡':
                    if request.title == '이벤트':
                        # 서비스 레이어 호출 (Base64 이미지 반환)
                        
                        image1, image2, image3, image4 = service_combine_ads_4_7(
                            request.store_name, request.road_name, copyright, request.title, image_width, image_height, img, request.weather, request.tag
                        )
                        
                        images_list.extend([image1, image2, image3, image4])
                    elif request.title == '매장 소개':
                        # 서비스 레이어 호출 (Base64 이미지 반환)
                        image1, image2, image3 = service_combine_ads_4_7(
                            request.store_name, request.road_name, copyright, request.title, image_width, image_height, img, request.weather, request.tag
                        )
                        images_list.extend([image1, image2, image3])
                    elif request.title == '상품소개':
                        # 서비스 레이어 호출 (Base64 이미지 반환)
                        image1 = service_combine_ads_4_7(
                            request.store_name, request.road_name, copyright, request.title, image_width, image_height, img, request.weather, request.tag
                        )
                        images_list.append(image1)
        except Exception as e:
            print(f"Error occurred: {e}, 이미지 합성 오류")
        
        # 문구와 합성된 이미지 반환
        return JSONResponse(content={"copyright": copyright, "images": images_list})

    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


# AI 생성용 템플릿 버전 이미지 처리
@router.post("/generate/template")
def generate_template(request: AdsTemplateRequest):
    try:
        # 문구 생성
        try:
            today = datetime.now()
            formattedToday = today.strftime('%Y-%m-%d (%A) %H:%M')
            if request.title == '이벤트':
                copyright_prompt = f'''
                    {request.store_name} 업체의 {request.use_option} 위한 광고 컨텐츠를 제작하려고 합니다.
                    {request.tag}, {formattedToday}, {request.weather}, {request.temp}℃, {request.detail_content}
                    핵심 고객 연령대 : {request.male_base}, {request.female_base} 제목 :, 내용 : 형식으로 작성해주세요
                '''
            else:
                copyright_prompt = f'''
                    {request.store_name} 업체의 {request.use_option} 위한 광고 컨텐츠를 제작하려고 합니다.
                    {request.tag}, {formattedToday}, {request.weather}, {request.temp}℃, {request.detail_content}
                    핵심 고객 연령대 : {request.male_base}, {request.female_base} 내용 15자 이내로 작성해주세요
            '''

            copyright = service_generate_content(
                copyright_prompt,
                request.gpt_role,
                request.detail_content
            )
        except Exception as e:
            print(f"Error occurred: {e}, 문구 생성 오류")
        
        # 전달받은 선택한 템플릿의 시드 프롬프트 gpt 로 소분류 바꾸기
        seed_image_prompt = request.seed_prompt

        # 이미지 생성
        try:
            if request.ai_model_option == 'midJouney':
                origin_image = service_generate_image_mid(
                    request.use_option,
                    seed_image_prompt
                )
            elif request.ai_model_option == "imagen3":
                origin_image = service_generate_image_imagen3_template(
                    request.use_option,
                    copyright,
                    request.tag,
                    seed_image_prompt
                )
            else:
                origin_image = service_generate_image(
                    request.use_option,
                    seed_image_prompt
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

        # 사이즈 조정 및 합성
        images_list = []
        try:
            for i, img in enumerate(origin_image):
                image_width, image_height = img.size  # 이미지 크기 가져오기
                print(f"Image {i + 1}: Width = {image_width}, Height = {image_height}")

                if request.use_option == '인스타그램 피드':
                    if request.title == '이벤트':
                        # 서비스 레이어 호출 (Base64 이미지 반환)
                        image1, image2, image3 = service_combine_ads_1_1(
                            request.store_name, request.road_name, copyright, request.title, image_width, image_height, img, request.weather, request.tag
                        )
                        images_list.extend([image1, image2, image3])
                    elif request.title == '매장 소개':
                        # 서비스 레이어 호출 (Base64 이미지 반환)
                        image1, image2, image3 = service_combine_ads_1_1(
                            request.store_name, request.road_name, copyright, request.title, image_width, image_height, img, request.weather, request.tag
                        )
                        images_list.extend([image1, image2, image3])
                elif request.use_option == '인스타그램 스토리' or request.use_option == '문자메시지' or request.use_option == '카카오톡':
                    if request.title == '이벤트':
                        # 서비스 레이어 호출 (Base64 이미지 반환)
                        image1, image2, image3, image4, image5 = service_combine_ads_4_7(
                            request.store_name, request.road_name, copyright, request.title, image_width, image_height, img, request.weather, request.tag
                        )
                        images_list.extend([image1, image2, image3, image4, image5])
                    elif request.title == '매장 소개':
                        # 서비스 레이어 호출 (Base64 이미지 반환)
                        image1, image2, image4, image5, image6, image7 = service_combine_ads_4_7(
                            request.store_name, request.road_name, copyright, request.title, image_width, image_height, img, request.weather, request.tag
                        )
                        images_list.extend([image1, image2, image4, image5, image6, image7])
                    elif request.title == '상품소개':
                        # 서비스 레이어 호출 (Base64 이미지 반환)
                        image1 = service_combine_ads_4_7(
                            request.store_name, request.road_name, copyright, request.title, image_width, image_height, img, request.weather, request.tag
                        )
                        images_list.append(image1)
        except Exception as e:
            print(f"Error occurred: {e}, 이미지 합성 오류")

        # 인스타 문구 테스트
        try:
            insta_copyright = ''
            
            if request.use_option == '인스타그램 피드':
                today = datetime.now()
                formattedToday = today.strftime('%Y-%m-%d (%A) %H:%M')

                copyright_prompt = f'''
                    {request.store_name} 업체의 {request.title}를 위한 광고 콘텐츠를 제작하려고 합니다. 
                    업종: {request.tag}
                    세부정보 : {request.detail_content}
                    일시 : {formattedToday}
                    오늘날씨 : {request.weather}, {request.temp}℃
                    핵심고객: 
                    매출이 가장 높은 남성 연령대 : 남자 {request.male_base}
                    매출이 가장 높은 여성 연령대 : 여자 {request.female_base}


                    주소: {request.road_name}
                    
                    단! "대표 메뉴 앞에 아이콘만 넣고, 메뉴 이름 뒤에는 아이콘을 넣지 않는다." "위치는 📍로, 영업시간은 🕒로 표현한다. 
                    '\n'으로 문단을 나눠 표현한다
                '''

                insta_role = '''
                    1. '{copyright}' 를 100~150자까지 {request.title} 인플루언서가 $대분류$ 을 소개하는 듯한 느낌으로 광고 문구 만들어줘 
                    {request.title}에 광고할 타겟은 핵심 연령층으로 {request.title}에 어울리는 내용을 생성한다. 
                    2.광고 타겟들이 흥미를 갖을만한 내용의 키워드를 뽑아서 검색이 잘 될만한 해시태그도 최소 3개에서 6개까지 생성한다
                '''

                insta_copyright = service_generate_content(
                    copyright_prompt,
                    insta_role,
                    request.detail_content
                )

        except Exception as e:
            print(f"Error occurred: {e}, 인스타 생성 오류")
        
        # 문구와 합성된 이미지 반환
        return JSONResponse(content={"copyright": copyright, "origin_image": output_images, "images": images_list, "insta_copyright" : insta_copyright})

    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


# ver2 AI 생성
@router.post("/generate/template2")
def generate_template(request: AdsTemplateSeedImage):
    try:
        # 문구 생성
        try:
            # print(request.example_image)
            today = datetime.now()
            formattedToday = today.strftime('%Y-%m-%d (%A) %H:%M')
            if request.title == '이벤트':
                copyright_prompt = f'''
                    {request.store_name} 업체의 {request.use_option} 위한 광고 컨텐츠를 제작하려고 합니다.
                    {request.tag}, {formattedToday}, {request.weather}, {request.temp}℃, {request.detail_content}
                    핵심 고객 연령대 : {request.male_base}, {request.female_base} 제목 :, 내용 : 형식으로 작성해주세요
                '''
            else:
                copyright_prompt = f'''
                    {request.store_name} 업체의 {request.use_option} 위한 광고 컨텐츠를 제작하려고 합니다.
                    {request.tag}, {formattedToday}, {request.weather}, {request.temp}℃, {request.detail_content}
                    핵심 고객 연령대 : {request.male_base}, {request.female_base} 내용 15자 이내로 작성해주세요
            '''

            copyright = service_generate_content(
                copyright_prompt,
                request.gpt_role,
                request.detail_content
            )
        except Exception as e:
            print(f"Error occurred: {e}, 문구 생성 오류")
        
        # 전달받은 선택한 템플릿의 시드 프롬프트 gpt로 소분류에 맞게 바꾸기
        seed_image_prompt = request.seed_prompt

        # 전달받은 선택한 템플릿의 시드 이미지 gpt로 이미지 분석
        seed_image_vision = service_generate_image_vision(request.example_image)

        # 이미지 생성
        try:
            if request.ai_model_option == 'midJouney':
                origin_image = service_generate_image_mid(
                    request.use_option,
                    seed_image_prompt
                )
            elif request.ai_model_option == "imagen3":
                origin_image = service_generate_image_imagen3_template(
                    request.use_option,
                    copyright,
                    request.tag,
                    seed_image_prompt,
                    seed_image_vision
                )
            else:
                origin_image = service_generate_image(
                    request.use_option,
                    seed_image_prompt
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
            
            if request.use_option == '인스타그램 피드':
                today = datetime.now()
                formattedToday = today.strftime('%Y-%m-%d (%A) %H:%M')

                copyright_prompt = f'''
                    {request.store_name} 업체의 {request.title}를 위한 광고 콘텐츠를 제작하려고 합니다. 
                    업종: {request.tag}
                    세부정보 : {request.detail_content}
                    일시 : {formattedToday}
                    오늘날씨 : {request.weather}, {request.temp}℃
                    핵심고객: 
                    매출이 가장 높은 남성 연령대 : 남자 {request.male_base}
                    매출이 가장 높은 여성 연령대 : 여자 {request.female_base}


                    주소: {request.road_name}
                    
                    단! "대표 메뉴 앞에 아이콘만 넣고, 메뉴 이름 뒤에는 아이콘을 넣지 않는다." "위치는 📍로, 영업시간은 🕒로 표현한다. 
                    '\n'으로 문단을 나눠 표현한다
                '''

                insta_role = '''
                    1. '{copyright}' 를 100~150자까지 {request.title} 인플루언서가 $대분류$ 을 소개하는 듯한 느낌으로 광고 문구 만들어줘 
                    
                    2.광고 타겟들이 흥미를 갖을만한 내용의 키워드를 뽑아서 검색이 잘 될만한 해시태그도 최소 3개에서 6개까지 생성한다
                '''

                insta_copyright = service_generate_content(
                    copyright_prompt,
                    insta_role,
                    request.detail_content
                )

        except Exception as e:
            print(f"Error occurred: {e}, 인스타 생성 오류")
        
        # 문구와 합성된 이미지 반환
        return JSONResponse(content={"copyright": copyright, "origin_image": output_images, "insta_copyright" : insta_copyright})

    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


# ver2 파일 업로드
@router.post("/generate/exist/image/template2")
def generate_image_with_text_template2(
        store_name: str = Form(...),
        road_name: str = Form(...),
        tag: str = Form(...),
        weather: str = Form(...),
        temp: float = Form(...),
        male_base: str = Form(...),
        female_base: str = Form(...),
        gpt_role: str = Form(...),
        detail_content: str = Form(...),
        use_option: str = Form(...),
        title: str = Form(...),
    ):

    try:
        # 문구 생성
        try:
            today = datetime.now()
            formattedToday = today.strftime('%Y-%m-%d (%A) %H:%M')

            copyright_prompt = f'''
                매장명 : {store_name}
                주소 : {road_name}
                업종 : {tag}
                날짜 : {formattedToday}
                날씨 : {weather}, {temp}℃
                매출이 가장 높은 남성 연령대 : {male_base}
                매출이 가장 높은 여성 연령대 : {female_base}
            '''
            copyright = service_generate_content(
                copyright_prompt,
                gpt_role,
                detail_content
            )
        except Exception as e:
            print(f"Error occurred: {e}, 문구 생성 오류")

    # 인스타 문구 테스트
        try:
            insta_copyright = ''
            
            if use_option == '인스타그램 피드':
                today = datetime.now()
                formattedToday = today.strftime('%Y-%m-%d (%A) %H:%M')

                copyright_prompt = f'''
                    {store_name} 업체의 {title}를 위한 광고 콘텐츠를 제작하려고 합니다. 
                    업종: {tag}
                    세부정보 : {detail_content}
                    일시 : {formattedToday}
                    오늘날씨 : {weather}, {temp}℃
                    핵심고객: 
                    매출이 가장 높은 남성 연령대 : 남자 {male_base}
                    매출이 가장 높은 여성 연령대 : 여자 {female_base}


                    주소: {road_name}
                    
                    단! "대표 메뉴 앞에 아이콘만 넣고, 메뉴 이름 뒤에는 아이콘을 넣지 않는다." "위치는 📍로, 영업시간은 🕒로 표현한다. 
                    '\n'으로 문단을 나눠 표현한다
                '''

                insta_role = '''
                    1. '{copyright}' 를 100~150자까지 {request.title} 인플루언서가 $대분류$ 을 소개하는 듯한 느낌으로 광고 문구 만들어줘 
                    {request.title}에 광고할 타겟은 핵심 연령층으로 {request.title}에 어울리는 내용을 생성한다. 
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
        return JSONResponse(content={"copyright": copyright, "insta_copyright" : insta_copyright})

    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)





# 문구 생성
@router.post("/generate/content", response_model=AdsGenerateContentOutPut)
def generate_content(request: AdsContentRequest):
    try:
        # print('깃허브 푸시용 테스트')
        # 서비스 레이어 호출: 요청의 데이터 필드를 unpack
        data = service_generate_content(
            request.prompt,
            request.gpt_role,
            request.detail_content
        )
        return {"content": data}  
    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


# 모달창에서 이미지 생성하기
@router.post("/generate/image")
def generate_image(request: AdsImageRequest):
    try:
        if request.ai_model_option == 'midJouney':
            image = service_generate_image_mid(
                request.use_option,
                request.ai_mid_prompt,
            )
            return image
        else:
            # 서비스 레이어 호출: 요청의 데이터 필드를 unpack
            image = service_generate_image(
                request.use_option,
                request.ai_prompt,
            )
            base64_images = []
            for img in image:
                if isinstance(img, dict):  # 🔹 dict이면 이미지 객체가 아니라 직렬화된 데이터이므로 처리 불필요
                    base64_images.append(img)  # 이미 변환된 데이터라면 그대로 추가
                else:
                    buffered = io.BytesIO()
                    img.save(buffered, format="PNG")
                    base64_img = base64.b64encode(buffered.getvalue()).decode("utf-8")
                    base64_images.append(base64_img)

            return base64_images  # 🔹 리스트 자체를 반환 (FastAPI 자동 직렬화 방지)
    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        print(f"HTTPException 발생: {http_ex.detail}")  # 추가 디버깅 출력
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        print(f"Exception 발생: {error_msg}")  # 추가 디버깅 출력
        raise HTTPException(status_code=500, detail=error_msg)

# ADS 텍스트, 이미지 합성
@router.post("/combine/image/text")
def combine_ads(
        store_name: str = Form(...),
        road_name: str = Form(...),
        content: str = Form(...),
        use_option: str = Form(...),
        title: str = Form(...),
        image_width: int = Form(...),
        image_height: int = Form(...),
        image: UploadFile = File(...)
    ):
    try:
        pil_image = Image.open(image.file)
    except Exception as e:
        return {"error": f"Failed to open image: {str(e)}"}
    
    if use_option == '인스타그램 피드':
        if title == '이벤트':
            # 서비스 레이어 호출 (Base64 이미지 반환)
            image1, image2 = service_combine_ads_1_1(store_name, road_name, content, title, image_width, image_height, pil_image)
            return JSONResponse(content={"images": [image1, image2]})
        elif title == '매장 소개':
            # 서비스 레이어 호출 (Base64 이미지 반환)
            image1 = service_combine_ads_1_1(store_name, road_name, content, title, image_width, image_height, pil_image)
            return JSONResponse(content={"images": [image1]})
    elif use_option == '인스타그램 스토리' or use_option == '문자메시지':
        if title == '이벤트':
            # 서비스 레이어 호출 (Base64 이미지 반환)
            image1, image2 = service_combine_ads_4_7(store_name, road_name, content, title, image_width, image_height, pil_image)
            return JSONResponse(content={"images": [image1, image2]})
        elif title == '매장 소개':
            # 서비스 레이어 호출 (Base64 이미지 반환)
            image1 = service_combine_ads_4_7(store_name, road_name, content, title, image_width, image_height, pil_image)
            return JSONResponse(content={"images": [image1]})


# ADS DB에 저장
@router.post("/insert")
def insert_ads(
        store_business_number: str = Form(...),
        use_option: str = Form(...),
        title: str = Form(...),
        detail_title: Optional[str] = Form(None),  # 선택적 필드
        content: str = Form(...),
        image: UploadFile = File(None),
        final_image: UploadFile = File(None)  # 단일 이미지 파일
    ):
    # 이미지 파일 처리
    image_url = None
    if image:
        try:
            # 고유 이미지 명 생성
            filename, ext = os.path.splitext(image.filename)
            today = datetime.now().strftime("%Y%m%d")
            unique_filename = f"{filename}_jyes_ads_{today}_{uuid.uuid4()}{ext}"

            # 파일 저장 경로 지정
            file_path = os.path.join(FULL_PATH, unique_filename)

            # 파일 저장
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)

            # 이미지 URL 생성
            image_url = f"/static/images/ads/{unique_filename}"
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error saving image file: {str(e)}"
            )

    # 파이널 이미지 파일 처리
    final_image_url = None
    if final_image:
        try:
            # 고유 이미지 명 생성
            filename, ext = os.path.splitext(final_image.filename)
            today = datetime.now().strftime("%Y%m%d")
            unique_filename = f"{filename}_jyes_ads_final_{today}_{uuid.uuid4()}{ext}"

            # 파일 저장 경로 지정
            file_path = os.path.join(FULL_PATH, unique_filename)

            # 파일 저장
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(final_image.file, buffer)

            # 파이널 이미지 URL 생성
            final_image_url = f"/static/images/ads/{unique_filename}"
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error saving final_image file: {str(e)}"
            )

    # 데이터 저장 호출
    try:
        ads_pk = service_insert_ads(
            store_business_number, 
            use_option, 
            title, 
            detail_title, 
            content, 
            image_url, 
            final_image_url
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inserting ad data: {str(e)}"
        )

    # 성공 응답 반환
    return ads_pk

# ADS 삭제처리
@router.post("/delete/status")
def delete_status(request: AdsDeleteRequest):
    try:
        # 서비스 레이어를 통해 업데이트 작업 수행
        success = service_delete_status(
            request.ads_id,
        )
        if success:
            return success
    except Exception as e:
        # 예외 처리
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    

# ADS DB에 수정
@router.post("/update")
def update_ads(
        store_business_number: str = Form(...),
        use_option: str = Form(...),
        title: str = Form(...),
        detail_title: Optional[str] = Form(None),  # 선택적 필드
        content: str = Form(...),
        image: UploadFile = File(None),
        final_image: UploadFile = File(None)  # 단일 이미지 파일
    ):
    
    # 이미지 파일 처리
    image_url = None
    if image:
        try:
            # 고유 이미지 명 생성
            filename, ext = os.path.splitext(image.filename)
            today = datetime.now().strftime("%Y%m%d")
            unique_filename = f"{filename}_jyes_ads_{today}_{uuid.uuid4()}{ext}"

            # 파일 저장 경로 지정
            file_path = os.path.join(FULL_PATH, unique_filename)

            # 파일 저장
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)

            # 이미지 URL 생성
            image_url = f"/static/images/ads/{unique_filename}"
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error saving image file: {str(e)}"
            )

    # 파이널 이미지 파일 처리
    final_image_url = None
    if final_image:
        try:
            # 고유 이미지 명 생성
            filename, ext = os.path.splitext(final_image.filename)
            today = datetime.now().strftime("%Y%m%d")
            unique_filename = f"{filename}_jyes_ads_final_{today}_{uuid.uuid4()}{ext}"

            # 파일 저장 경로 지정
            file_path = os.path.join(FULL_PATH, unique_filename)

            # 파일 저장
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(final_image.file, buffer)

            # 파이널 이미지 URL 생성
            final_image_url = f"/static/images/ads/{unique_filename}"
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error saving final_image file: {str(e)}"
            )

    # 데이터 저장 호출
    try:
        service_update_ads(
            store_business_number, 
            use_option, 
            title, 
            detail_title, 
            content, 
            image_url, 
            final_image_url
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating ad data: {str(e)}"
        )

    # 성공 응답 반환
    return {
        "store_business_number": store_business_number,
        "use_option": use_option,
        "title": title,
        "detail_title": detail_title,
        "content": content,
        "image_url": image_url,
        "final_image_url": final_image_url
    }


# 업로드
@router.post("/upload")
async def upload_ads(
        use_option: str = Form(...), 
        content: str = Form(...), 
        store_name: str = Form(...), 
        tag: str = Form(...), 
        insta_copyright: str = Form(None),
        upload_images: List[UploadFile] = File(...),
    ):
    """
    광고 업로드 엔드포인트
    """
    final_image_url = None

    # 1. 파이널 이미지 파일 처리
    if upload_images and len(upload_images) > 0:  # 배열이 비어있지 않은지 확인
        try:
            # 배열에서 첫 번째 이미지 가져오기
            upload_image = upload_images[0]

            # 파일명 및 확장자 생성
            filename, ext = os.path.splitext(upload_image.filename)
            today = datetime.now().strftime("%Y%m%d")
            unique_filename = f"{filename}_jyes_ads_final_{today}_{uuid.uuid4()}{ext}"
            file_path = os.path.join(FULL_PATH, unique_filename)

            # 파일 저장
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(upload_image.file, buffer)

            # 파이널 이미지 URL 생성
            final_image_url = f"/static/images/ads/{unique_filename}"

        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": f"Error saving final_image file: {str(e)}",
                    "traceback": traceback.format_exc()
                }
            )

    # # 2. 유튜브 썸네일 처리
    # if use_option == "유튜브 썸네일":
    #     # 토큰이 없는 경우 인증 URL 반환
    #     if not access_token:
    #         state = json.dumps({
    #             "content": content,
    #             "store_name": store_name,
    #             "tag": tag,
    #             "file_path": file_path,
    #         })

    #         auth_url = service_upload_get_auth_url(state=state)
    #         return {"auth_url": auth_url["auth_url"]}

    # 3. 다른 업로드 옵션 처리
    try:
        if use_option == "인스타그램 스토리":
            insta_name, follower_count, media_count = service_upload_story_ads(content, file_path)
            return insta_name, follower_count, media_count
        elif use_option == "인스타그램 피드":
            insta_name, follower_count, media_count = service_upload_feed_ads(content, file_path, upload_images, insta_copyright)
            return insta_name, follower_count, media_count
        elif use_option == "문자메시지":
            await service_upload_mms_ads(content, file_path)
        elif use_option == '유튜브 썸네일':
            service_upload_youtube_ads(content, store_name, tag, file_path)
        # elif use_option == '네이버 블로그':
        #     service_upload_naver_ads(content, store_name, tag, file_path)
    except Exception as e:
        print(f"Error occurred: {e}, 업로드 오류")

    # 4. 성공 응답 반환
    return {
        "content": content,
        "final_image_url": final_image_url
    }

# 카카오톡 업로드
@router.post("/temp/insert")
def generate_share_uuid(data: KaKaoTempInsert):
    unique_id = str(uuid.uuid4())[:8]  # 8자리 UUID 생성

    # 🔹 Redis에 JSON 데이터 저장 (유효기간 7일)
    redis_client.setex(unique_id, 86400 * 7, json.dumps(data.dict()))  

    return {"shortUrl": f"{unique_id}"}


@router.post("/temp/get")
def get_share_data(request: KaKaoTempGet):
    stored_data = redis_client.get(request.share_id)

    if not stored_data:
        raise HTTPException(status_code=404, detail="공유 데이터 없음")

    return json.loads(stored_data)


ROOT_PATH = os.getenv("ROOT_PATH")
AUTH_PATH = os.getenv("AUTH_PATH")

@router.post("/auth/callback")
def youtube_auth_callback(request: AuthCallbackRequest):
    CLIENT_SECRETS_FILE = os.path.join(ROOT_PATH, AUTH_PATH.lstrip("/"), "google_auth_wiz.json")
    SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
    REDIRECT_URI = "http://localhost:3002/ads/auth/callback"

    code = request.code
    try:
        # Google OAuth Flow 초기화
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            SCOPES,
            redirect_uri=REDIRECT_URI,
        )

        # 인증 코드로 액세스 토큰 교환
        flow.fetch_token(code=code)
        credentials = flow.credentials

        # 반환된 액세스 토큰
        access_token = credentials.token
        return {"access_token": access_token}
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": f"Error exchanging auth code: {str(e)}"},
        )



# 유튜브 업로드 영상
@router.post("/upload/youtube")
async def upload_youtube_ads(
        content: str = Form(...), 
        store_name: str = Form(...), 
        tag: str = Form(...), 
        file_path: str = Form(None),
        access_token: str = Form(None),
    ):
    try:
        response = service_upload_youtube_ads(content, store_name, tag, file_path, access_token)
        return {"youtube_response": response}
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"Error uploading to YouTube: {str(e)}"},
        )


# Ads 영상 만들기
@router.post("/generate/video")
def generate_video(
        title: str = Form(...),
        final_image: UploadFile = File(None)  # 단일 이미지 파일
    ):
    
    # 파이널 이미지 파일 처리
    if final_image:
        try:
            # 고유 이미지 명 생성
            filename, ext = os.path.splitext(final_image.filename)
            today = datetime.now().strftime("%Y%m%d")
            unique_filename = f"{filename}_jyes_ads_final_{today}_{uuid.uuid4()}{ext}"
            file_path = os.path.join(FULL_PATH, unique_filename)
            # 파일 저장
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(final_image.file, buffer)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error saving final_image file: {str(e)}"
            )
    
    # 데이터 저장 호출
    try:
        result_url= service_generate_video(file_path)
        return {"result_url" : result_url}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inserting ad data: {str(e)}"
        )


# 업로드 된 이미지로 영상 만들기
@router.post("/generate/video/image")
def generate_video_with_text(
        store_name: str = Form(...),
        road_name: str = Form(...),
        tag: str = Form(...),
        weather: str = Form(...),
        temp: float = Form(...),
        male_base: str = Form(...),
        female_base: str = Form(...),
        gpt_role: str = Form(...),
        detail_content: str = Form(...),
        image: UploadFile = File(...)
    ):

    try:
        # 문구 생성
        try:
            today = datetime.now()
            formattedToday = today.strftime('%Y-%m-%d (%A) %H:%M')

            copyright_prompt = f'''
                매장명 : {store_name}
                주소 : {road_name}
                업종 : {tag}
                날짜 : {formattedToday}
                날씨 : {weather}, {temp}℃
                매출이 가장 높은 남성 연령대 : {male_base}
                매출이 가장 높은 여성 연령대 : {female_base}
            '''
            copyright = service_generate_content(
                copyright_prompt,
                gpt_role,
                detail_content
            )
        except Exception as e:
            print(f"Error occurred: {e}, 문구 생성 오류")

        # 영상 생성
        if image:
            try:
                # 고유 이미지 명 생성
                filename, ext = os.path.splitext(image.filename)
                today = datetime.now().strftime("%Y%m%d")
                unique_filename = f"{filename}_jyes_ads_final_{today}_{uuid.uuid4()}{ext}"
                file_path = os.path.join(FULL_PATH, unique_filename)
                # 파일 저장
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(image.file, buffer)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error saving final_image file: {str(e)}"
                )
        try:
            result_path= service_generate_video(file_path)
        except Exception as e:
            print(f"Error occurred: {e}, 영상 생성 오류")

        # 문구와 영상 합성
        try:
            video_path = service_generate_add_text_to_video(result_path, copyright)
        except Exception as e:
            print(f"Error occurred: {e}, 영상 합성 오류")
        return {"copyright": copyright, "result_url": video_path["result_url"]}

    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


# 영상 업로드 (인스타)
@router.post("/upload/video")
def upload_video_insta(request: AdsUploadVideoInsta):
    try:
        video_path = request.video_path
        content = request.content

        video_path = os.path.normpath(os.path.join(ROOT_PATH, video_path.lstrip("/")))

        # video_path = "/static/~"
        insta_name, follower_count, media_count = service_upload_feed_video_ads(content, video_path)
        return insta_name, follower_count, media_count
    except Exception as e:
        print(f"Error occurred: {e}, 업로드 오류")


# 새 모델 테스트
@router.post("/generate/test/new/content", response_model=AdsGenerateContentOutPut)
def generate_new_content(request: AdsContentNewRequest):
    try:
        # 서비스 레이어 호출: 요청의 데이터 필드를 unpack
        content = service_generate_new_content(
            request.prompt
        )
        return {'content': content}
    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    

# 구 모델 테스트
@router.post("/generate/test/old/content", response_model=AdsGenerateContentOutPut)
def generate_old_content(request: AdsContentNewRequest):
    try:
        # 서비스 레이어 호출: 요청의 데이터 필드를 unpack
        content = service_generate_old_content(
            request.prompt
        )
        return {'content': content}
    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    

# 디퓨전 모델 테스트
@router.post("/generate/image/claude/content", response_model=AdsGenerateContentOutPut)
def generate_claude_content(request: AdsContentNewRequest):
    try:
        # 서비스 레이어 호출: 요청의 데이터 필드를 unpack
        content = service_generate_claude_content(
            request.prompt
        )
        return {'content': content}
    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    
# 이미지 테스트 - 스테이블 디퓨전
@router.post("/generate/image/stable")
def generate_image_stable(request: AdsContentNewRequest):
    try:
        # 서비스 레이어 호출: 요청의 데이터 필드를 unpack
        data = service_generate_image_stable(
            request.prompt,
        )
        return data
    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        print(f"HTTPException 발생: {http_ex.detail}")  # 추가 디버깅 출력
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        print(f"Exception 발생: {error_msg}")  # 추가 디버깅 출력
        raise HTTPException(status_code=500, detail=error_msg)
    
# 이미지 테스트 - 달리
@router.post("/generate/image/dalle")
def generate_image_dalle(request: AdsDrawingModelTest):
    try:
        # 서비스 레이어 호출: 요청의 데이터 필드를 unpack
        data = service_generate_image_dalle(
            request.prompt,
            request.ratio
        )
        return data
    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        print(f"HTTPException 발생: {http_ex.detail}")  # 추가 디버깅 출력
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        print(f"Exception 발생: {error_msg}")  # 추가 디버깅 출력
        raise HTTPException(status_code=500, detail=error_msg)
    
# 이미지 테스트 - 미드저니
@router.post("/generate/image/mid/test")
def generate_image_mid(request: AdsDrawingModelTest):
    try:
        data = service_generate_image_mid_test(
            request.prompt,
            request.ratio
        )
        return data

    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        print(f"HTTPException 발생: {http_ex.detail}")  # 추가 디버깅 출력
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        print(f"Exception 발생: {error_msg}")  # 추가 디버깅 출력
        raise HTTPException(status_code=500, detail=error_msg)
    

# 이미지 테스트 - 이메진3
@router.post("/generate/image/imagen")
def generate_image_imagen_test(request: AdsDrawingModelTest):
    try:
        data = service_generate_image_imagen_test(
            request.prompt,
            request.ratio
        )
        return data

    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        print(f"HTTPException 발생: {http_ex.detail}")  # 추가 디버깅 출력
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        print(f"Exception 발생: {error_msg}")  # 추가 디버깅 출력
        raise HTTPException(status_code=500, detail=error_msg)
    

# 배경 제거 테스트 - API
@router.post("/remove/background")
def generate_image_remove_bg(
    image: UploadFile = File(...)
):
    try:
        new_image = service_generate_image_remove_bg(image)
        return new_image
    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    

# 배경 제거 테스트 - 파이썬 모듈
@router.post("/remove/background/free")
async def generate_image_remove_bg_free(
    image: UploadFile = File(...)
):
    try:
        input_image = Image.open(io.BytesIO(await image.read()))
        free_image = service_generate_image_remove_bg_free(input_image)
        return free_image
    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    

# 영상 생성
@router.post("/test/generate/video")
async def generate_test_generate_video(
    image: UploadFile = File(...),
    prompt: str = Form(...),
):
    try:
        # 이미지 업로드 처리 (PIL Image 변환)
        input_image = Image.open(io.BytesIO(await image.read()))
        
        # 비디오 생성 서비스 호출
        video_url = service_generate_test_generate_video(input_image, prompt)
        
        if not video_url:
            raise HTTPException(status_code=500, detail="Failed to generate video")

        return {"video_url": video_url}
    
    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    

# 배경 생성
@router.post("/test/generate/bg")
def generate_test_generate_bg(request : AdsContentRequest):
    try:       
        # 비디오 생성 서비스 호출
        image = service_generate_test_generate_bg(request.prompt, request.gpt_role, request.detail_content)
        
        if not image:
            raise HTTPException(status_code=500, detail="Failed to generate video")

        return {"image": image}
    
    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)






##### 음악 생성 로직 #####


# 1. 가사 생성
@router.post("/test/generate/lyrics")
def generate_test_generate_lyrics(request : AdsDrawingModelTest):
    try:       
        # 비디오 생성 서비스 호출
        lyrics = service_generate_test_generate_lyrics(request.prompt, request.ratio)
        if not lyrics:
            raise HTTPException(status_code=500, detail="Failed to generate video")
        return {"lyrics": lyrics}
    
    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

# 2. 음악 생성
@router.post("/test/generate/music")
def generate_test_generate_music(request : AdsContentRequest):
    try:       
        # 비디오 생성 서비스 호출
        task_id = service_generate_test_generate_music(request.prompt, request.gpt_role, request.detail_content)
        if not task_id:
            raise HTTPException(status_code=500, detail="Failed to generate video")
        return {"task_id": task_id}
    
    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

# 3. 콜백으로 생성된 taskID 레디스 저장 후 리턴
@router.post("/test/callback")
async def callback(request: Request):
    data = await request.json()
    # print("data: ", data)
    task_id = data["data"]["task_id"]
    # print("task_id: ", task_id)
    audio_urls = [item["audio_url"] for item in data["data"]["data"]]  # 여러 개 가능
    # print("audio_urls : ", audio_urls)

    # Redis에 저장 (JSON 형식으로)
    redis_client.set(task_id, json.dumps(audio_urls))
    
    # print(f"✅ 저장 완료: {task_id} -> {audio_urls}")
    return {"status": "received"}

# 4. taskID 로 레디스 조회 후 음악 url 리턴
@router.post("/test/check/music")
async def check_music(request: MusicGet):
    # Redis에서 taskId로 저장된 데이터 가져오기
    taskId = request.taskId  
    music_data = redis_client.get(taskId)

    if music_data:
        # Redis에 저장된 음악 데이터를 JSON 형태로 파싱
        music_info = json.loads(music_data)

        # 음악 정보 반환
        return {"music": music_info}  # 음악 URL 및 관련 정보 반환
    else:
        # 데이터가 없는 경우 에러 처리
        raise HTTPException(status_code=404, detail="Music not found or generation is still in progress.")
    




# 이미지 스토리 생성
@router.post("/test/generate/story")
async def generate_test_generate_story(request: Story):
    try:
        # 스토리 생성
        story = service_generate_test_generate_story(request.story_role, request.example_image)
        
        if not story:
            raise HTTPException(status_code=500, detail="Failed to generate story")

        return {"story": story}
    
    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

# 생성된 스토리로 유사 이미지 생성
@router.post("/test/generate/story/image")  
def generate_test_generate_story_image(request: AdsContentNewRequest):
    try:
        ratio = "9:16"
        data = service_generate_image_imagen_test(
            request.prompt,
            ratio
        )
        return data

    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

# 사업자 상태 조회
@router.post("/test/confirm/store")
def generate_test_confirm_store(request: AdsDeleteRequest):
    try:
        if not request.ads_id:
            raise HTTPException(status_code=400, detail="사업자등록번호를 입력해주세요.")
        
        ads_id = str(request.ads_id)

        SERVICE_KEY = os.getenv("CONFIRM_KEY")
        url = f"https://api.odcloud.kr/api/nts-businessman/v1/status?serviceKey={SERVICE_KEY}"
        
        payload = {"b_no": [ads_id]}

        headers = {"Content-Type": "application/json"}

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="외부 API 요청 실패")

        data = response.json()

        return data
    
    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    
# 인증 메일 발송
@router.post("/test/send/mail")
def generate_test_send_mail(request: AdsContentNewRequest):
    try:
        # 고유한 인증 코드 생성
        length = 6  # 인증 코드 길이
        characters = string.ascii_letters + string.digits  # 대소문자 + 숫자 조합
        word = ''.join(random.choices(characters, k=length))

        # 메일 발송
        mail = str(request.prompt)
        success = service_send_mail(mail, word)

        if len(word) != 6:
            data = "인증 코드 길이가 6이 아닙니다."
        elif not mail:
            data = "메일 주소가 없습니다."
        elif not success:
            data = "메일 발송에 실패했습니다."  # 추가!
        else:
            redis_client.setex(f"verify:{mail}", 300, word)
            data = "성공적으로 메일이 발송 되었습니다."

        return {"message": data}
    
    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    
# 인증 메일 확인
@router.post("/test/confirm/mail")
def generate_test_confirm_mail(request: AdsDrawingModelTest):
    try:
        mail = request.prompt
        word = request.ratio
        stored_data = redis_client.get(f"verify:{mail}")

        if not stored_data:
            return {"success": False, "message": "인증 시간이 만료되었거나 존재하지 않는 메일입니다."}
        elif stored_data != word:
            return {"success": False, "message": "인증 코드가 일치하지 않습니다."}
        else:
            redis_client.delete(f"verify:{mail}")
            return {"success": True, "message": "인증 코드가 일치합니다."}
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {"success": False, "message": "서버 오류가 발생했습니다."}

# 인스타 정보 가져오기
@router.post("/test/get/insta")
def generate_test_get_insta(request: AdsDrawingModelTest):
    try:
        user = request.prompt
        post = request.ratio
        
        # 인스타그램 정보 가져오기
        like_count, comment_count = service_get_insta_info(user, post)

        return {
            "like_count": like_count,
            "comment_count": comment_count
        }

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {"success": False, "message": "서버 오류가 발생했습니다."}
    
  
# 네이버 정보 가져오기
@router.post("/test/get/naver")
def generate_test_get_naver(request: AdsDrawingModelTest):
    try:
        user = request.prompt
        post = request.ratio
        
        # 인스타그램 정보 가져오기
        like, comment = service_get_naver_info(user, post)

        # JSON 형태로 반환
        return {
            "like": like,
            "comment": comment
        }


    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {"success": False, "message": "서버 오류가 발생했습니다."}
