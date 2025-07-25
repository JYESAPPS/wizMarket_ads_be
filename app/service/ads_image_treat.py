from PIL import Image, ExifTags
import requests
import tempfile
import io 
from io import BytesIO
import os
import base64
from dotenv import load_dotenv
from google import genai
from google.genai import types
import torch
from torchvision import transforms, models 
from sklearn.metrics.pairwise import cosine_similarity

# .env 파일 로드
load_dotenv()






def generate_test_edit_image(image, find, change):
    try:
        API_KEY = os.getenv("STABILITY_CHANGE_API_KEY")
        # 업로드된 파일을 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            temp_file.write(image.file.read())
            temp_file_path = temp_file.name

        # Stability API 호출
        response = requests.post(
            "https://api.stability.ai/v2beta/stable-image/edit/search-and-replace",
            headers={
                "authorization": f"Bearer {API_KEY}",
                "accept": "image/*"
            },
            files={
                "image": open(temp_file_path, "rb")
            },
            data={
                "prompt": change,          # 바꾸고자 하는 내용
                "search_prompt": find,     # 찾을 대상
                "output_format": "webp"
            },
        )

        if response.status_code == 200:
            return BytesIO(response.content)  # 이걸 반환
        else:
            raise Exception(response.json())

    except Exception as e:
        raise e
    

def generate_test_change_person(image, style):
    try:
        # API 키 환경 변수로 가져오기
        API_KEY = os.getenv("AILABTOOLS_CHANGE_API_KEY")

        # 파일을 BytesIO로 읽어서 외부 API에 전달
        image_contents = image.file.read()  # 이미지 파일 내용
        response = requests.post(
            "https://www.ailabapi.com/api/portrait/effects/portrait-animation",
            headers={'ailabapi-api-key': API_KEY}, 
            files={'image': ('file', BytesIO(image_contents), 'application/octet-stream')},
            data={'type': style}
        )
        
        if response.status_code == 200:
            # 응답에서 이미지 URL 추출
            response_data = response.json()

            return response_data["data"]["image_url"]
        else:
            return None
    except Exception as e:
        print(f"Error during API call: {str(e)}")
        return None


def extend_bg(image, prompt):
    try:
        # API 키 환경 변수로 가져오기
        API_KEY = os.getenv("AILABTOOLS_CHANGE_API_KEY")

        payload = {
            'custom_prompt':prompt,
            'steps': '30',
            'strength': '0.8',
            'scale': '7',
            'seed': '0',
            'top': '0.5',
            'bottom': '0.5',
            'left': '0.5',
            'right': '0.5',
            'max_height': '1920',
            'max_width': '1920'
        }



        # 파일을 BytesIO로 읽어서 외부 API에 전달
        image_contents = image.file.read()  # 이미지 파일 내용
        response = requests.post(
            "https://www.ailabapi.com/api/image/editing/ai-image-extender",
            headers={'ailabapi-api-key': API_KEY},
            files={'image': ('image.png', BytesIO(image_contents), 'application/octet-stream')},
            data=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            # base64가 아니라 URL 방식으로 응답이 올 경우
            if "data" in result and "image_url" in result["data"]:
                return result["data"]["image_url"]
            elif "data" in result and "binary_data_base64" in result["data"]:
                # 혹시 base64로 오면 URL로 변환해 저장소에 업로드하거나 에러로 처리
                return "data:image/jpeg;base64," + result["data"]["binary_data_base64"][0]
            else:
                print("⚠️ 예상치 못한 응답 형식:", result)
                return None
        else:
            print("❌ 요청 실패:", response.status_code)
            print(response.text)
            return None
    except Exception as e:
        print(f"❌ 에러 발생: {str(e)}")
        return None


# 코사인 유사도 위해 이미지 벡터 추출 (ResNet-50 모델 사용)
def extract_feature_vector(img: Image.Image):
    # 전처리
    preprocess = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
        )
    ])

    input_tensor = preprocess(img).unsqueeze(0)  # [1, 3, 224, 224]
    model = models.resnet50(pretrained=True)
    model.eval()
    with torch.no_grad():
        features = model(input_tensor)
    return features.numpy()

# 코사인 유사도 비교 함수
def compute_cosine_similarity(vec1, vec2):
    return cosine_similarity(vec1, vec2)[0][0]


# 유사도 비교 엔드포인트
async def compare_face(image, prompt):
    # 1. Imagen3 API
    try:
        key = os.getenv("IMAGEN3_API_SECRET")
        client = genai.Client(api_key=key)

        # Prompt 전달 및 이미지 생성
        response = client.models.generate_images(
            model='imagen-3.0-generate-002',
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=4,
                aspect_ratio="9:16",  # 비율 유지
                output_mime_type='image/jpeg'
            )
        )

        # 업로드된 이미지 벡터화
        org_bytes = await image.read()  
        org_img = Image.open(io.BytesIO(org_bytes)).convert("RGB")
        org_vec = extract_feature_vector(org_img)

        # 결과 리스트 초기화
        cos_results = []

        # 각 이미지 별 코사인 유사도
        for gen_img in response.generated_images:
            # Base64 인코딩     
            new_image = Image.open(BytesIO(gen_img.image.image_bytes))
            buffer = BytesIO()
            new_image.save(buffer, format="PNG")
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

            gen_img_pil = new_image.convert("RGB")

            # 벡터 추출 및 유사도 계산
            gen_vec = extract_feature_vector(gen_img_pil)
            similarity = compute_cosine_similarity(org_vec, gen_vec)

            cos_results.append({
                "similarity": float(similarity),
                "image_base64": image_base64,
            })
        
        # 결과를 유사도 기준으로 정렬
        cos_results = sorted(cos_results, key=lambda x: x["similarity"], reverse=True)
        # print(f"유사도 결과: {cos_results}")
        return cos_results

    except Exception as e:
        return {"error": f"이미지 생성 중 오류 발생: {e}"}