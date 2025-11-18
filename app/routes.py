from fastapi import APIRouter, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from typing import Optional
from datetime import datetime

from .storage.json_storage import storage

def format_time(timestamp):
    """格式化时间显示"""
    if not timestamp:
        return ""
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp)
    return timestamp.strftime("%Y-%m-%d %H:%M")

# 创建路由
router = APIRouter()
templates = Jinja2Templates(directory="templates")
templates.env.globals.update(format_time=format_time)

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """首页"""
    # 获取预设列表
    presets = storage.get_presets()
    
    # 获取最近的对话
    conversations = storage.get_conversations(limit=5)
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "presets": presets,
        "recent_conversations": conversations
    })

@router.get("/chat/{conversation_id}", response_class=HTMLResponse)
async def chat_page(request: Request, conversation_id: str):
    """聊天页面"""
    # 获取对话信息
    conversation = storage.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    # 获取预设列表
    presets = storage.get_presets()
    
    # 获取当前预设
    current_preset = None
    if conversation.get("preset_id"):
        current_preset = storage.get_preset(conversation["preset_id"])
    
    # 获取对话消息
    messages = storage.get_messages(conversation_id)
    
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "conversation_id": conversation_id,
        "conversation_title": conversation["title"],
        "presets": presets,
        "current_preset": current_preset,
        "messages": messages
    })

@router.get("/new-chat", response_class=HTMLResponse)
async def new_chat(request: Request):
    """新建对话页面"""
    # 获取预设列表
    presets = storage.get_presets()
    
    return templates.TemplateResponse("new_chat.html", {
        "request": request,
        "presets": presets
    })

@router.get("/presets", response_class=HTMLResponse)
async def presets_page(request: Request):
    """预设管理页面"""
    # 获取所有预设
    presets = storage.get_presets()
    
    return templates.TemplateResponse("presets.html", {
        "request": request,
        "presets": presets
    })

@router.get("/conversations", response_class=HTMLResponse)
async def conversations_page(request: Request):
    """对话管理页面"""
    # 获取对话列表
    conversations = storage.get_conversations()
    
    return templates.TemplateResponse("conversations.html", {
        "request": request,
        "conversations": conversations
    })

@router.get("/api-docs", response_class=HTMLResponse)
async def api_docs_page(request: Request):
    """API文档页面"""
    return templates.TemplateResponse("api_docs.html", {
        "request": request
    })