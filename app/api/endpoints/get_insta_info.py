import requests
import os
from dotenv import load_dotenv


# ==== .env 로드 ====
load_dotenv()
ACCESS_TOKEN = os.getenv("INSTAGRAM_TOKEN")
MEDIA_ID = "17933445138121421"

url = f"https://graph.facebook.com/v18.0/{MEDIA_ID}"
params = {
    "fields": "id,caption,media_type,media_url,permalink,thumbnail_url,timestamp,like_count,comments_count,owner",
    "access_token": ACCESS_TOKEN,
}

resp = requests.get(url, params=params)
resp.raise_for_status()
data = resp.json()
print(data)
