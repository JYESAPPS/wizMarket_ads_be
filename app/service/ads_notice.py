from app.crud.ads_notice import (
    get_notice as crud_get_notice,
    create_notice as crud_create_notice,
    get_notice_read as crud_get_notice_read,
    insert_notice_read as crud_insert_notice_read
)

from fastapi import HTTPException
import logging
import os
from dotenv import load_dotenv
import requests
from openai import OpenAI
import os

def get_notice():
    notice = crud_get_notice()
    return notice

def create_notice(notice_title, notice_content):
    try:
        crud_create_notice(notice_title, notice_content)
        return {"success": True, "message": "공지사항이 등록되었습니다."}
    except Exception as e:
        
        return {"success": False, "message": "서버 오류가 발생했습니다."}

def get_notice_read(user_id):
    data = crud_get_notice_read(user_id)
    return data

def insert_notice_read(user_id, notice_no):
    try:
        crud_insert_notice_read(user_id, notice_no)
        return True
    except Exception as e:
        print(f"서비스 오류: {e}")
        return False