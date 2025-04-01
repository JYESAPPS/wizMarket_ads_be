import logging
import io
import os
from dotenv import load_dotenv
import requests
from openai import OpenAI
from PIL import Image
from io import BytesIO
import base64
import time
from runwayml import RunwayML
from moviepy import *
from rembg import remove
from fastapi.responses import StreamingResponse
from google import genai
from google.genai import types
import json
import http.client

logger = logging.getLogger(__name__)
load_dotenv()

# OpenAI API 키 설정
api_key = os.getenv("GPT_KEY")
client = OpenAI(api_key=api_key)


def generate_image_stable(prompt: str,):
    token = os.getenv("FACE_KEY")


    API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-3.5-large"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"inputs": prompt}
    # API 요청 보내기
    try:
        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status()  # 에러 발생 시 예외 처리

        image = Image.open(BytesIO(response.content))
        # 이미지를 Base64로 인코딩
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return {"image": f"data:image/png;base64,{base64_image}"}

    except requests.exceptions.RequestException as e:
        print(f"Failed to generate image: {e}")
        return {"error": str(e)}


# 달리 이미지 생성
def generate_image_dalle(prompt: str, ratio: str):
    try:
        size_mapping = {
            "1:1": "1024x1024",
            "9:16": "1024x1792",
            "16:9": "1792x1024"
        }
        size = size_mapping.get(ratio, "1024x1024")
        # Prompt 전달 및 이미지 생성
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality="hd", 
            n=1
        )
        image_url = response.data[0].url
        # print(image_url)
        # 이미지 다운로드
        image_response = requests.get(image_url)
        image_response.raise_for_status()
        # 이미지 열기
        image = Image.open(io.BytesIO(image_response.content))

        # 이미지를 Base64로 인코딩
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return {"image": f"data:image/png;base64,{base64_image}"}
        
    except Exception as e:
        return {"error": f"이미지 생성 중 오류 발생: {e}"}
    

# 미드저니 이미지 생성
def generate_image_mid_test(prompt: str, ratio: str):
    try:
        prompt = f"{prompt}--ar {ratio}"
        USE_API_TOKEN = os.getenv("USE_API_TOKEN")
        DIS_USE_TOKEN = os.getenv("DIS_USE_TOKEN")
        DIS_SER_ID = os.getenv("DIS_SER_ID")
        DIS_CHA_ID = os.getenv("DIS_CHA_ID")

        if not (USE_API_TOKEN and DIS_USE_TOKEN and DIS_SER_ID and DIS_CHA_ID):
            raise ValueError("One or more required environment variables are missing.")

        apiUrl = "https://api.useapi.net/v2/jobs/imagine"
        token = USE_API_TOKEN
        discord = DIS_USE_TOKEN
        server = DIS_SER_ID
        channel = DIS_CHA_ID

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        body = {
            "prompt": f"{prompt}",
            "discord": f"{discord}",
            "server": f"{server}",
            "channel": f"{channel}"
        }

        # Step 1: Job creation
        response = requests.post(apiUrl, headers=headers, json=body)
        print(response)
        response.raise_for_status()  # HTTP 오류 발생 시 예외 발생
        job_id = response.json().get("jobid")
        if not job_id:
            raise ValueError("No job ID returned from API")

        # Step 2: Polling to check job status
        apiUrl = f"https://api.useapi.net/v2/jobs/?jobid={job_id}"
        timeout_seconds = 180  # 최대 120초 동안 대기
        start_time = time.time()

        while True:
            response = requests.get(apiUrl, headers=headers)
            response.raise_for_status()  # HTTP 오류 발생 시 예외 발생

            data = response.json()
            status = data.get("status")

            if status == "completed":
                break  # 작업 완료
            elif status in ["failed", "canceled"]:
                raise RuntimeError(f"Job failed or canceled with status: {status}")

            # 작업이 완료되지 않은 경우 대기 후 재요청
            elapsed_time = time.time() - start_time
            if elapsed_time >= timeout_seconds:
                raise TimeoutError(f"Job polling exceeded maximum timeout of {timeout_seconds} seconds.")

            print(f"Job not ready yet, retrying in 5 seconds... (Elapsed time: {int(elapsed_time)}s/{timeout_seconds}s)")
            time.sleep(5)

        link = data.get("attachments")
        if not link or len(link) == 0:
            raise ValueError("No attachments found in job response")

        # Step 3: Image download
        url = link[0]['proxy_url']
        image_response = requests.get(url)
        image_response.raise_for_status()  # HTTP 오류 발생 시 예외 발생

        image = Image.open(BytesIO(image_response.content))
        width, height = image.size

        # 자를 좌표 설정
        coordinates = [
            (0, 0, width // 2, height // 2),       # 왼쪽 상단
            (width // 2, 0, width, height // 2),   # 오른쪽 상단
            (0, height // 2, width // 2, height),  # 왼쪽 하단
            (width // 2, height // 2, width, height)  # 오른쪽 하단
        ]

        # 잘린 이미지를 Base64로 변환하여 리스트 생성
        base64_images = []
        for coord in coordinates:
            cropped_image = image.crop(coord)  # 자른 이미지

            # 이미지 Base64 변환
            buffer = BytesIO()
            cropped_image.save(buffer, format="PNG")
            buffer.seek(0)
            base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
            base64_images.append(f"data:image/png;base64,{base64_image}")

        # Base64 이미지 리스트 반환
        return {"images": base64_images}

    except requests.exceptions.RequestException as e:
        return {"error": f"HTTP 요청 중 오류 발생: {e}"}
    except ValueError as e:
        return {"error": f"값 오류 발생: {e}"}
    except RuntimeError as e:
        return {"error": f"실행 오류 발생: {e}"}
    except Exception as e:
        return {"error": f"알 수 없는 오류 발생: {e}"}

# IMAGEN3 이미지 생성
def generate_image_imagen_test(prompt: str, ratio: str):
    try:
        try:
            key = os.getenv("IMAGEN3_API_SECRET")
            client = genai.Client(api_key=key)

            # Prompt 전달 및 이미지 생성
            response = client.models.generate_images(
                model='imagen-3.0-generate-002',
                prompt=prompt,
                
                config=types.GenerateImagesConfig(
                    number_of_images=4,
                    aspect_ratio=ratio,
                    output_mime_type='image/jpeg'
                )
            )
            
            base64_images = []
        except Exception as e:
            error_msg = f"Unexpected error while processing request: {str(e)}"
            print(error_msg)
        
        for generated_image in response.generated_images:
            image = Image.open(BytesIO(generated_image.image.image_bytes))
            # 이미지를 Base64로 인코딩
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            buffer.seek(0)
            base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

            base64_images.append(f"data:image/png;base64,{base64_image}")

        return {"images": base64_images}

    except Exception as e:
        return {"error": f"이미지 생성 중 오류 발생: {e}"}

# 배경 제거1
def generate_image_remove_bg(image):
    try:
        # Pixian API에 파일 직접 전송
        response = requests.post(
            'https://api.pixian.ai/api/v2/remove-background',
            files={"image": (image.filename, image.file, image.content_type)},
            data={
                'test': 'true'  # TODO: Remove for production
            },
            auth=('pxjrefqwqgdapzl', 'on8deo8fidgmljosuae5h6nb8l39s5iiv043v9nke6rtdklhj4ea')
        )

        # 요청이 성공하면 Pixian에서 반환된 이미지 저장
        if response.status_code == requests.codes.ok:
            return StreamingResponse(io.BytesIO(response.content), media_type="image/png")
        else:
            return {"error": f"Pixian API 오류: {response.status_code} - {response.text}"}

    except Exception as e:
        return {"error": str(e)}
    
# 배경 제거 2
def generate_image_remove_bg_free(image):

    output_image = remove(image)

    # 메모리에서 바로 반환 (저장 X)
    img_io = io.BytesIO()
    output_image.save(img_io, format="PNG")
    img_io.seek(0)  # 스트림의 시작 위치로 이동

    return StreamingResponse(img_io, media_type="image/png")



    
# 영상 생성
def generate_test_generate_video(image: Image.Image, prompt: str):
    """업로드된 이미지를 저장 후, RunwayML을 호출하여 비디오 생성 후 원본 이미지 삭제"""
    
    # API 키 가져오기
    api_key = os.getenv("RUNWAYML_API_SECRET")
    if not api_key:
        raise ValueError("API key not found. Please check your .env file.")

    # 이미지 저장 경로 설정
    image_dir = "temp_images"
    os.makedirs(image_dir, exist_ok=True)  # 폴더가 없으면 생성

    image_path = os.path.join(image_dir, "uploaded_image.png")

    # 이미지 저장
    image.save(image_path, format="PNG")

    try:
        # RunwayML 클라이언트 초기화
        client = RunwayML(api_key=api_key)

        # 이미지 파일을 Base64로 인코딩
        with open(image_path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode("utf-8")

        # RunwayML API 호출
        task = client.image_to_video.create(
            model='gen3a_turbo',
            prompt_image=f"data:image/png;base64,{base64_image}",
            prompt_text=prompt,
        )

        task_id = task.id
        print("Task created. Polling for status...")

        # 상태 확인 (비디오 생성이 완료될 때까지 대기)
        while True:
            task = client.tasks.retrieve(task_id)
            if task.status in ['SUCCEEDED', 'FAILED']:
                break
            print(f"Task status: {task.status}. Retrying in 10 seconds...")
            time.sleep(10)

        # 최종 결과 확인
        if task.status == 'SUCCEEDED':
            print("Task succeeded!")
            result_url = task.output[0]  # 결과 URL 반환
        else:
            print("Task failed.")
            result_url = None

    finally:
        # 사용이 끝난 이미지 삭제
        if os.path.exists(image_path):
            os.remove(image_path)
            print(f"Deleted temp image: {image_path}")

    return result_url

# 배경 생성
def generate_test_generate_bg(url, type, prompt):
    api_url = "https://api.developer.pixelcut.ai/v1/generate-background"

    payload_data = {
        "image_url": url,
        "image_transform": {
            "scale": 1,
            "x_center": 0.5,
            "y_center": 0.5
        }
    }

    if type == "style":
        payload_data["scene"] = prompt  # 스타일 모드일 때 scene 사용
    else:
        p_prompt, n_prompt = map(str.strip, prompt.split("|"))
        payload_data["prompt"] = p_prompt
        payload_data["negative_prompt"] = n_prompt

    payload = json.dumps(payload_data)
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-API-KEY': os.getenv("PIXEL_API_KEY")  # 환경 변수에서 API 키 가져오기
    }

    return requests.post(api_url, headers=headers, data=json.dumps(payload_data)).json().get("result_url")



#### 음악 생성 ####
# 1. 가사 생성
def generate_test_generate_lyrics(style, title):
    # gpt 영역
    gpt_content = "You are a famous lyricist"
    content = f'''
        제목 : {title}
        스타일 : {style}
        이거에 맞게 영문으로 작사해줘. 가사만 3000자 이내로 딱 작성해줘 부가 요소 없이.
    '''
    client = OpenAI(api_key=os.getenv("GPT_KEY"))
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": gpt_content},
            {"role": "user", "content": content},
        ],
    )
    report = completion.choices[0].message.content
    return report


def generate_test_generate_music(lyrics, style, title):
    suno_api_key = os.getenv("SUNO_API_KEY")
    conn = http.client.HTTPSConnection("apibox.erweima.ai")
    
    payload = json.dumps({
        "prompt": lyrics,
        "style": style,
        "title": title,
        "customMode": True,
        "instrumental": False,
        "model": "V3_5",
        "negativeTags": "",
        "callBackUrl": "http://221.151.48.225:58002/ads/test/callback"
    })
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {suno_api_key}'
    }
    
    # API 요청 보내기
    conn.request("POST", "/api/v1/generate", payload, headers)
    res = conn.getresponse()
    
    # 응답 데이터 읽기
    data = res.read()
    
    # 응답을 JSON 형식으로 변환
    response = json.loads(data.decode("utf-8"))
    print(response)
    # task_id 추출
    task_id = response['data']['taskId']
    
    return task_id