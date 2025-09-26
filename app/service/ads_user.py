import os
import base64
import requests
from fastapi import HTTPException
import re
from typing import Optional, Dict, Any, List
from app.crud.ads_user import (
    check_user_id as crud_check_user_id,
    register_user as crud_register_user,
    get_store as crud_get_store,
    insert_business_info as crud_insert_business_info,
    update_user as crud_update_user,

)

from app.crud.ads_app import (
    update_register_tag as crud_update_register_tag,
    update_user_status_only as crud_update_user_status_only,
    upsert_user_info_accounts as crud_upsert_user_info_accounts,
    delete_user as crud_delete_user,
)



def check_user_id(user_id):
    exists = crud_check_user_id(user_id)
    return exists

def register_user(user_id, password):
    crud_register_user(user_id, password)

# 매장 조회
def get_store(store_name, road_name):
    return crud_get_store(store_name, road_name)

# 기존 매장 관련 정보 등록
def register_store_info(request):
    user_id = request.user_id

    # 사업자 정보 (번호, 대표자)는 business_verification
    success1 = crud_insert_business_info(user_id, request.business_name, request.business_number)

    # store_business_number를 userTB에 업데이트
    success2 = crud_update_user(user_id, request.store_business_number, request.status)

    # register_tag를 user_info TB에 업데이트
    success3 = crud_update_register_tag(user_id, request.register_tag)

    return success1 and success2 and success3



def register_sns(req):
    user_id = req.user_id
    status = (req.status or "").strip().lower()

    # 1) 유저 상태 업데이트
    ok = crud_update_user_status_only(user_id=user_id, status=status)
    if not ok:
        raise HTTPException(status_code=500, detail="유저 상태 업데이트 실패")

    # 2) 계정이 있으면 UPSERT (없으면 스킵)
    # 2) user_info에 SNS 계정 업서트 (있을 때만)
    accounts = req.accounts or []
    clean: List[Dict[str, str]] = []
    for a in accounts:
        ch = (a.channel or "").strip()
        acc = (a.account or "").strip()
        if ch and acc:
            clean.append({"channel": ch, "account": acc})

    if clean:
        crud_upsert_user_info_accounts(user_id=user_id, accounts=clean)

    return {"success": True}


def delete_user(user_id: str):
    # 탈퇴 로직 구현 (예: DB에서 사용자 삭제)
    success = crud_delete_user(user_id)

    # success = True  # 실제로는 탈퇴 성공 여부에 따라 설정

    return success




# OCR 파일 타입 체크
def _suffix(filename: str) -> str:
    fn = (filename or "").lower()
    for s in {".png", ".jpg", ".jpeg", ".webp", ".pdf"}:
        if fn.endswith(s):
            return s
    return ""

# OCR 결과값 교정 및 표준화
def _fuzzy(label: str) -> str:
    # '사업장 소재지' → '사\s*업\s*장\s*\s*소\s*재\s*지'
    return r"\s*".join(map(re.escape, label.strip()))

def _single_line_after_labels(text: str, labels: List[str]) -> Optional[str]:
    pat = re.compile(
        r"(?:" + "|".join(_fuzzy(l) for l in labels) + r")\s*[:：]?\s*(.+)",
        flags=re.MULTILINE
    )
    m = pat.search(text)
    if not m:
        return None
    return re.sub(r"\s+", " ", m.group(1).strip())

def _format_regno_from_fragment(s: str) -> Optional[str]:
    if not s: return None
    s2 = re.sub(r"[^0-9\- ]+", "", s)
    digits = re.sub(r"\D+", "", s2)
    if len(digits) == 10:
        return f"{digits[:3]}-{digits[3:5]}-{digits[5:]}"
    m = re.search(r"\b\d{3}-\d{2}-\d{5}\b", s2)
    return m.group(0) if m else None

# OCR 결과에서 라벨 기반 정보 추출
def _extract_biz_fields(ocr_text: str) -> Dict[str, Optional[str]]:
    """라벨 기반 + 패턴 폴백으로 4개 필드 반환"""

    TRANS_TABLE = str.maketrans({
        "—": "-", "–": "-", "−": "-",
        "O": "0", "o": "0",
        "I": "1", "l": "1", "ㅣ": "1",
    })
    t = (ocr_text or "").replace("\u200b", "").translate(TRANS_TABLE)

    # 1) 등록번호: 패턴 우선 → 라벨 폴백
    m = re.search(r"\b\d{3}-\d{2}-\d{5}\b", t)
    regno = m.group(0) if m else None
    if not regno:
        line = _single_line_after_labels(t, ["사업자등록번호", "등록번호"])
        regno = _format_regno_from_fragment(line) if line else None

    # 2) 상호(법인명)
    biz = _single_line_after_labels(t, ["상호(법인명)", "법인명(단체명)", "상호", "법인명"])

    # 3) 대표자
    rep = _single_line_after_labels(t, ["성명(대표자)", "대표자", "성명"])
    if rep:
        m_name = re.match(r"[가-힣·‧ㆍ\s]{2,30}", rep)
        if m_name:
            rep = re.sub(r"\s+", " ", m_name.group(0).strip())

    # 4) 소재지
    addr = _single_line_after_labels(t, ["사업장소재지", "사업장 소재지", "소재지", "본점소재지", "본점 소재지"])

    return {
        "business_number": regno or None,
        "store_name": (biz or None),
        "address": (addr or None),
        "business_name": (rep or None),
    }


# google cloud vision api: OCR 실행
def read_ocr(file_bytes: bytes, filename: str, api_key: str) -> str:
    """
    이미지: images:annotate / PDF: files:annotate + pages=[1]
    반환: 전체 텍스트(문자열)
    """
    if not api_key:
        raise RuntimeError("Missing GCV_API_KEY")

    VISION_BASE = "https://vision.googleapis.com/v1"

    if _suffix(filename) == ".pdf":
        url = f"{VISION_BASE}/files:annotate?key={api_key}"
        req: Dict[str, Any] = {
            "requests": [{
                "inputConfig": {"mimeType": "application/pdf", "content": base64.b64encode(file_bytes).decode()},
                "features": [{"type": "DOCUMENT_TEXT_DETECTION"}],
                "pages": [1],
            }]
        }
        req["requests"][0]["imageContext"] = {"languageHints": ["ko"]}
        r = requests.post(url, json=req, timeout=120)
        r.raise_for_status()
        data = r.json()

        chunks: List[str] = []
        top = (data.get("responses") or [{}])[0]
        for img_resp in top.get("responses", []):
            txt = img_resp.get("fullTextAnnotation", {}).get("text", "")
            if not txt and img_resp.get("textAnnotations"):
                txt = img_resp["textAnnotations"][0].get("description", "")
            if txt:
                chunks.append(txt)
        return "\n".join(chunks)
    else:
        # 이미지류
        url = f"{VISION_BASE}/images:annotate?key={api_key}"
        req: Dict[str, Any] = {
            "requests": [{
                "image": {"content": base64.b64encode(file_bytes).decode()},
                "features": [{"type": "DOCUMENT_TEXT_DETECTION"}],
            }]
        }
        req["requests"][0]["imageContext"] = {"languageHints": ["ko"]}
        r = requests.post(url, json=req, timeout=60)
        r.raise_for_status()
        data = r.json()
        resp = (data.get("responses") or [{}])[0]
        text = resp.get("fullTextAnnotation", {}).get("text", "")
        if not text and resp.get("textAnnotations"):
            text = resp["textAnnotations"][0].get("description", "")
        return text or ""
