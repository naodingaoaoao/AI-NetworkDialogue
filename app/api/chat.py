import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from datetime import datetime

from ..storage.json_storage import storage
from ..services.lm_studio_client import LMStudioClient
from ..websocket.connection_manager import ConnectionManager

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由
chat_router = APIRouter()

# 全局变量
lm_client = LMStudioClient()
connection_manager = ConnectionManager()

# 请求/响应模型
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    preset_id: Optional[int] = None
    stream: bool = False

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    timestamp: str

class ModelInfo(BaseModel):
    id: str
    name: str

class ModelsResponse(BaseModel):
    models: list[ModelInfo]

@chat_router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):

    try:
        # 获取或创建对话
        conversation = await lm_client._get_or_create_conversation(
            request.conversation_id, 
            request.preset_id
        )
        
        # 获取AI回复
        response = await lm_client.get_response(
            message=request.message,
            conversation_id=conversation["id"],
            preset_id=request.preset_id
        )
        
        return ChatResponse(
            response=response,
            conversation_id=conversation["id"],
            timestamp=str(datetime.utcnow())
        )
        
    except Exception as e:
        logger.error(f"聊天请求处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"处理聊天请求时出错: {str(e)}")

@chat_router.get("/models", response_model=ModelsResponse)
async def get_models():

    try:
        model_ids = await lm_client.get_available_models()
        models = [ModelInfo(id=model_id, name=model_id) for model_id in model_ids]
        return ModelsResponse(models=models)
        
    except Exception as e:
        logger.error(f"获取模型列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取模型列表失败: {str(e)}")

@chat_router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: str):
    try:
        # 验证对话是否存在
        conversation = storage.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")
        
        # 获取消息列表
        messages = storage.get_messages(conversation_id)
        
        return {
            "conversation_id": conversation_id,
            "title": conversation["title"],
            "messages": [
                {
                    "content": message["content"],
                    "sender": message["sender"],
                    "timestamp": message["created_at"]
                }
                for message in messages
            ]
        }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取对话消息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取对话消息失败: {str(e)}")

@chat_router.post("/conversations")
async def create_conversation(title: str = "新建对话", preset_id: Optional[int] = None):
    try:
        new_id = storage.create_conversation(title, preset_id)
        conversation = storage.get_conversation(new_id)
            
        return {
            "id": conversation["id"],
            "title": conversation["title"],
            "created_at": conversation["created_at"]
        }
            
    except Exception as e:
        logger.error(f"创建对话失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建对话失败: {str(e)}")

@chat_router.get("/conversations")
async def get_conversations(limit: int = 50, offset: int = 0):
    try:
        # 获取对话列表
        conversations = storage.get_conversations(limit, offset)
        
        # 获取总数
        all_conversations = storage.get_conversations()
        total_count = len(all_conversations)
        
        return {
            "conversations": [
                {
                    "id": conv["id"],
                    "title": conv["title"],
                    "created_at": conv["created_at"],
                    "updated_at": conv["updated_at"]
                }
                for conv in conversations
            ],
            "total": total_count,
            "limit": limit,
            "offset": offset
        }
            
    except Exception as e:
        logger.error(f"获取对话列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取对话列表失败: {str(e)}")

@chat_router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    try:
        from ..services.history_cleanup import delete_conversation
        success = await delete_conversation(conversation_id)
        
        if success:
            return {"message": "对话删除成功"}
        else:
            raise HTTPException(status_code=404, detail="对话不存在")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除对话失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除对话失败: {str(e)}")

@chat_router.put("/conversations/{conversation_id}")
async def update_conversation(conversation_id: str, title: str):
    try:
        from ..services.history_cleanup import update_conversation_title
        success = await update_conversation_title(conversation_id, title)
        
        if success:
            return {"message": "对话标题更新成功"}
        else:
            raise HTTPException(status_code=404, detail="对话不存在")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新对话标题失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新对话标题失败: {str(e)}")