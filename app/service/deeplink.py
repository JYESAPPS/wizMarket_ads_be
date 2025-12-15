import requests

FN_BASE = "https://asia-northeast1-wizad-b69ee.cloudfunctions.net"

def send_push(token: str):
    route = "/manual/marketing/ai"
    url = f"{FN_BASE}/sendPush"
    payload = {
        "token": token,
        "title": "NAV TEST",
        "body": f"Go to {route}",
        "data": { "route": route, "action": "navigate" }
    }
    r = requests.post(url, json=payload, timeout=60)
    try:
        print(r.status_code, r.json())
    except:
        print(r.status_code, r.text)

if __name__ == "__main__":
    token = input("device_token: ").strip()
    send_push(token)
