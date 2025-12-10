from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from typing import List
import logging
from app.schemas.ads_ticket import (
    InsertPayRequest,
)

from app.service.ads_ticket import (
    update_subscription_info as service_update_subscription_info,
)

from app.service.ads_token_purchase import (
    insert_purchase as service_insert_purchase,
)

from app.service.play_store import (
    verify_play_store_purchase as service_verify_play_store_purchase
)


router = APIRouter()
logger = logging.getLogger(__name__)


# 결제
@router.post("/purchase")
def insert_payment(request: InsertPayRequest):  

    # 확인용
    # print(request)

    # 1) 스토어 검증 수행 여부 결정
    if request.type == "fail":
        verify = {
            "success": False,
            "message": f"client reported fail: {getattr(request, 'error_code', None)}",
        }

    else:
        # 구글 플레이스토어 검증
        if request.platform == "android":
            verify = service_verify_play_store_purchase(request)

        # ios 앱 스토어 검증 X
        elif request.platform == "ios":
            verify = {"success": True, "message": "iOS verify skipped (stub)"}
        else:
            verify = {
                "success": False,  
                "message": f"client reported fail: {getattr(request, 'error_code', None)}"
                }

        # 스토어 검증 실패 → 결제 실패로 다운그레이드
        if not verify.get("success"):
            request.type = "fail"


    # 2) DB 기록 (항상 한 번만)
    try:
        service_insert_purchase(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"결제 로그 저장 과정에서 문제가 발생했습니다 : {str(e)}",
        )

    # 3) 응답 분기
    if verify.get("success") and request.type != "fail":
        # 스토어 검증까지 통과한 진짜 성공 케이스
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "결제가 성공적으로 처리되었습니다.",
                "count": request.qty,
            },
        )
    else:
        # 클라이언트 기준 실패(type=fail) 또는 스토어 검증 실패
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "message": verify.get("message") or "결제 처리 실패",
                "count": request.qty,
            },
        )