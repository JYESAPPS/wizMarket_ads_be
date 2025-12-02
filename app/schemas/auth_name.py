# app/schemas/kcb.py
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict

class StartReq(BaseModel):
    return_url: HttpUrl


class StartRes(BaseModel):
    rsp_cd: str
    rsp_msg: Optional[str] = None
    idcf_mbr_com_cd: Optional[str] = None
    svc_tkn: Optional[str] = None
    rqst_svc_tx_seqno: Optional[str] = None
    # 개발 편의(운영 전 제거)
    enc_key: Optional[str] = None
    enc_algo_cd: Optional[str] = None
    enc_iv: Optional[str] = None


# app/schemas/kcb.py  (추가)
class DecryptReq(BaseModel):
    svc_tkn: str         # return_url로 받은 것
    enc_key: str         # popup-start에서 받은 enc_key(암호문)
    # 옵션(기본 서버 설정 사용)
    enc_algo_cd: Optional[str] = None
    enc_iv: Optional[str] = None
    user_id : int

class DecryptRes(BaseModel):
    rsp_cd: str
    rsp_msg: Optional[str] = None
    user: Optional[Dict] = None     # 평문화 결과
    raw: Optional[Dict] = None      # 원문(개발 확인용)
