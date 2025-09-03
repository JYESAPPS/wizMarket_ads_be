from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Body, UploadFile, File, Form
from app.schemas.help import HelpCreate, HelpOut, HelpStatusUpdate
from app.crud.help import (
    list_help as crud_list_help,
    get_help as crud_get_help,
    update_help_status as crud_update_help_status
)
from app.service.help import create_help as service_create_help

router = APIRouter()

# 목록
@router.get("/", response_model=List[HelpOut])
def get_help_list(
    status: Optional[str] = Query(None, pattern="^(pending|answered|closed)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    return crud_list_help(status=status, limit=limit, offset=offset)

# 상세
@router.get("/{help_id}", response_model=HelpOut)
def get_help_detail(help_id: int):
    row = crud_get_help(help_id)
    if not row:
        raise HTTPException(status_code=404, detail="not found")
    return row

# 상태 변경
@router.patch("/{help_id}/status", response_model=HelpOut)
def patch_help_status(help_id: int, payload: HelpStatusUpdate = Body(...)):
    answer = (payload.answer or "").strip()
    status = "answered" if answer else payload.status
    if status not in ("pending", "answered", "closed"):
        raise HTTPException(status_code=400, detail="invalid status")
    row = crud_update_help_status(help_id, status, answer)
    if not row:
        raise HTTPException(status_code=404, detail="not found")
    return row

# 생성 (프론트 "등록하기"에서 호출)
@router.post("/", response_model=HelpOut)
async def create_help(
    user_id: Optional[int] = Form(None),
    name: str = Form(...),
    email: str = Form(...),
    phone: Optional[str] = Form(None),
    category: str = Form(...),
    content: str = Form(...),
    consent_personal: bool = Form(...),
    file1: Optional[UploadFile] = File(None),
    file2: Optional[UploadFile] = File(None),
    file3: Optional[UploadFile] = File(None),
):
    payload = HelpCreate(
        user_id=user_id, name=name, email=email, phone=phone,
        category=category, content=content, consent_personal=consent_personal
    )
    return await service_create_help(payload=payload, file1=file1, file2=file2, file3=file3)
