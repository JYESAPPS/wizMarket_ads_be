from app.db.connect import (
    get_db_connection, commit, close_connection, rollback, close_cursor, get_re_db_connection
)
from fastapi import HTTPException
from app.schemas.ads_faq import AdsFaqList, AdsTagList
from typing import List
import pymysql
import logging

logger = logging.getLogger(__name__)


# 도로명 정규화
import re
import unicodedata

# utils/address_normalize.py
import re
import unicodedata

# 축약/변형 → 정식 명칭 매핑
_ALIAS_TO_CANON = {
    # 특별/광역시
    "서울": "서울특별시", "서울시": "서울특별시",
    "부산": "부산광역시", "부산시": "부산광역시",
    "대구": "대구광역시", "대구시": "대구광역시",
    "인천": "인천광역시", "인천시": "인천광역시",
    "광주": "광주광역시", "광주시": "광주광역시",
    "대전": "대전광역시", "대전시": "대전광역시",
    "울산": "울산광역시", "울산시": "울산광역시",
    "세종": "세종특별자치시", "세종시": "세종특별자치시", "세종특별시": "세종특별자치시",

    # 도(광역자치단체)
    "경기": "경기도", "경기도": "경기도",
    "강원": "강원특별자치도", "강원도": "강원특별자치도", "강원특별자치도": "강원특별자치도",
    "충북": "충청북도", "충청북도": "충청북도",
    "충남": "충청남도", "충청남도": "충청남도",
    "전북": "전라북도", "전라북도": "전라북도",
    "전남": "전라남도", "전라남도": "전라남도",
    "경북": "경상북도", "경상북도": "경상북도",
    "경남": "경상남도", "경상남도": "경상남도",
    "제주": "제주특별자치도", "제주도": "제주특별자치도", "제주특별자치도": "제주특별자치도",
}

def normalize_addr_full(addr: str) -> str:
    """
    예)
      '부산 동구 고관로 85-1'  → '부산광역시 동구 고관로 85-1'
      '서울시 강남구 역삼로'    → '서울특별시 강남구 역삼로'
      '경기 성남시 분당구 ...'  → '경기도 성남시 분당구 ...'
      '강원도 춘천시 ...'       → '강원특별자치도 춘천시 ...'
    """
    if not addr:
        return ""

    # 1) 유니코드 정규화 + 공백/구두점 정리
    s = unicodedata.normalize("NFKC", addr).strip()
    # 괄호, 쉼표 등 최소 정리
    s = re.sub(r"[(),]", " ", s)
    # '대한민국 ' 같은 선행 국가명 제거
    s = re.sub(r"^대한민국\s+", "", s)
    # 다중 공백 축약
    s = re.sub(r"\s+", " ", s)

    # 2) 첫 토큰(시/도 단위 추정)만 정식 명칭으로 교체
    parts = s.split(" ", 1)  # ['부산', '동구 고관로 85-1']
    head = parts[0]
    tail = parts[1] if len(parts) > 1 else ""

    # head 후보에서 불필요 접미사 제거 후 매핑 확인 (예: '부산시' → '부산')
    head_base = head
    for suf in ("특별자치도", "특별시", "광역시", "자치시", "도", "시"):
        if head_base.endswith(suf):
            head_base = head_base[: -len(suf)]
            break

    # 우선 순위: 완전일치 → 베이스 치환 → 원형 보정
    canonical = (
        _ALIAS_TO_CANON.get(head) or
        _ALIAS_TO_CANON.get(head_base) or
        head  # 매핑 없으면 원본 유지
    )

    normalized = canonical if not tail else f"{canonical} {tail}"
    # 마무리 공백 정리
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized



def is_concierge(request):
    connection = get_re_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    store_name = request.store_name
    road_name = request.road_address
    norm_road = normalize_addr_full(road_name)

    try:
        if not connection.open:
            raise HTTPException(status_code=500, detail="DB 연결이 열려있지 않습니다.")

        # 별칭을 써서 키를 확정
        sql = """
            SELECT COUNT(*) AS cnt
            FROM REPORT
            WHERE STORE_NAME = %s
              AND ROAD_NAME = %s
              AND IS_CONCIERGE = 1
        """
        cursor.execute(sql, (store_name, norm_road))
        row = cursor.fetchone() or {"cnt": 0}
        exists = (row.get("cnt", 0) > 0)

        # 존재하면 이미 등록 → False, 아니면 신규 가능 → True
        return not exists

    except pymysql.MySQLError as e:
        logger.error(f"MySQL Error: {e}")
        raise HTTPException(status_code=500, detail="데이터베이스 오류가 발생했습니다.")
    except Exception as e:
        logger.error(f"Unexpected Error in is_concierge: {e}")
        raise HTTPException(status_code=500, detail="알 수 없는 오류가 발생했습니다.")
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            connection.close()
        except Exception:
            pass
