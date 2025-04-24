from fastapi import (
    APIRouter, UploadFile, File, Form, HTTPException
)
from app.schemas.ads import (
    AdsGenerateContentOutPut, AdsContentRequest,
    AdsDeleteRequest, AdsContentNewRequest,
    AdsDrawingModelTest,  
    MusicGet, Story, 
)
from app.service.ads_generate import (
    generate_new_content as service_generate_new_content,
    generate_old_content as service_generate_old_content,
    generate_claude_content as service_generate_claude_content,
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

from app.service.ads_get_outer_info import (
    get_insta_info as service_get_insta_info,
    get_reel_info as service_get_reel_info,
    get_naver_info as service_get_naver_info
)

from app.service.ads_image_treat import (
    generate_test_edit_image as service_generate_test_edit_image,
    generate_test_change_person as service_generate_test_change_person
)

from fastapi.responses import StreamingResponse
from fastapi import Request, Body
from PIL import Image
import logging
import io
import requests
import redis
from pathlib import Path
import os
import json
import random
import string
from fastapi.responses import JSONResponse

router = APIRouter()
logger = logging.getLogger(__name__)

ROOT_PATH = Path(os.getenv("ROOT_PATH"))
IMAGE_DIR = Path(os.getenv("IMAGE_DIR"))
VIDEO_DIR = Path(os.getenv("VIDEO_PATH"))
FULL_PATH = ROOT_PATH / IMAGE_DIR.relative_to("/") / "ads"
FULL_PATH.mkdir(parents=True, exist_ok=True)


redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

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

# 릴스 정보
@router.post("/test/get/reel")
def generate_test_get_reel(request: AdsDrawingModelTest):
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


# 이미지 편집 테스트
@router.post("/test/edit/image")
async def generate_test_edit_image(
    image: UploadFile = File(...),
    find: str = Form(...),
    change: str = Form(...)
):
    try:
        # 이미지 변환 처리
        img_stream = service_generate_test_edit_image(image, find, change)
        
        if not img_stream:
            raise HTTPException(status_code=500, detail="Failed to generate img")
        return StreamingResponse(img_stream, media_type="image/png")  # MIME 타입 맞게
    
    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    

# 이미지 인물 바꾸기 테스트
@router.post("/test/change/person")
async def generate_test_change_person(
    image: UploadFile = File(...),
    style: str = Form(...),
):
    try:
        # 이미지 변환 처리
        image_url = service_generate_test_change_person(image, style)
        
        if not image_url:
            raise HTTPException(status_code=500, detail="Failed to generate img")
        print(image_url)
        return JSONResponse(content={"image_url": image_url})
    
    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


