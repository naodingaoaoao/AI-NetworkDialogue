import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException

from ..storage.json_storage import storage
from ..services.history_cleanup import get_conversation_statistics, cleanup_old_conversations

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由
conversation_router = APIRouter()

@conversation_router.get("/statistics")
async def get_statistics():
    """
    获取对话统计信息
    """
    try:
        stats = await get_conversation_statistics()
        return stats
        
    except Exception as e:
        logger.error(f"获取对话统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取对话统计信息失败: {str(e)}")

@conversation_router.post("/cleanup")
async def manual_cleanup(days: int = 30):
    """
    手动清理历史记录
    
    Args:
        days: 保留天数
        
    Returns:
        清理结果
    """
    try:
        deleted_count = await cleanup_old_conversations(days)
        
        return {
            "message": f"清理完成，删除了 {deleted_count} 个旧对话",
            "deleted_count": deleted_count,
            "retention_days": days
        }
        
    except Exception as e:
        logger.error(f"手动清理历史记录失败: {e}")
        raise HTTPException(status_code=500, detail=f"清理历史记录失败: {str(e)}")

@conversation_router.get("/{conversation_id}/export")
async def export_conversation(conversation_id: str):
    """
    导出对话记录
    
    Args:
        conversation_id: 对话ID
        
    Returns:
        对话记录的JSON格式数据
    """
    try:
        # 验证对话是否存在
        conversation = storage.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")
        
        # 获取预设信息
        preset = None
        if conversation.get("preset_id"):
            preset = storage.get_preset(conversation["preset_id"])
        
        # 获取消息列表
        messages = storage.get_messages(conversation_id)
        
        return {
            "conversation": {
                "id": conversation["id"],
                "title": conversation["title"],
                "created_at": conversation["created_at"],
                "updated_at": conversation["updated_at"],
                "preset": {
                    "id": preset["id"],
                    "name": preset["name"],
                    "description": preset.get("description", "")
                } if preset else None
            },
            "messages": [
                {
                    "content": message["content"],
                    "sender": message["sender"],
                    "timestamp": message["created_at"],
                    "model_name": message.get("model_name", "")
                }
                for message in messages
            ]
        }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出对话记录失败: {e}")
        raise HTTPException(status_code=500, detail=f"导出对话记录失败: {str(e)}")

@conversation_router.post("/{conversation_id}/duplicate")
async def duplicate_conversation(conversation_id: str, new_title: Optional[str] = None):
    """
    复制对话
    
    Args:
        conversation_id: 原对话ID
        new_title: 新对话标题
        
    Returns:
        新对话信息
    """
    try:
        # 验证原对话是否存在
        original_conversation = storage.get_conversation(conversation_id)
        if not original_conversation:
            raise HTTPException(status_code=404, detail="对话不存在")
        
        # 创建新对话
        new_id = storage.create_conversation(
            new_title or f"{original_conversation['title']} (副本)",
            original_conversation.get("preset_id")
        )
        
        # 获取原对话的消息
        messages = storage.get_messages(conversation_id)
        
        # 复制消息记录
        for message in messages:
            storage.add_message(
                new_id,
                message["sender"],
                message["content"]
            )
        
        new_conversation = storage.get_conversation(new_id)
        
        return {
            "id": new_conversation["id"],
            "title": new_conversation["title"],
            "message_count": len(messages),
            "created_at": new_conversation["created_at"]
        }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"复制对话失败: {e}")
        raise HTTPException(status_code=500, detail=f"复制对话失败: {str(e)}")