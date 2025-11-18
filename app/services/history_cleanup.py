import logging
from datetime import datetime, timedelta
from typing import Optional

from ..config import settings
from ..storage.json_storage import storage

# 配置日志
logger = logging.getLogger(__name__)

async def cleanup_old_conversations(days: Optional[int] = None) -> int:
    """
    清理旧对话记录
    
    Args:
        days: 保留天数，如果为None则使用配置中的默认值
        
    Returns:
        删除的对话数量
    """
    if days is None:
        days = settings.max_conversation_age_days
    
    try:
        deleted_count = storage.cleanup_old_conversations(days)
        logger.info(f"已删除 {deleted_count} 个旧对话及其消息记录")
        return deleted_count
    except Exception as e:
        logger.error(f"清理历史记录时出错: {e}")
        return 0

async def delete_conversation(conversation_id: str) -> bool:
    """
    删除指定对话及其所有消息
    
    Args:
        conversation_id: 对话ID
        
    Returns:
        是否成功删除
    """
    try:
        success = storage.delete_conversation(conversation_id)
        if success:
            logger.info(f"已删除对话 {conversation_id}")
        return success
    except Exception as e:
        logger.error(f"删除对话 {conversation_id} 时出错: {e}")
        return False

async def update_conversation_title(conversation_id: str, title: str) -> bool:
    """
    更新对话标题
    
    Args:
        conversation_id: 对话ID
        title: 新标题
        
    Returns:
        是否成功更新
    """
    try:
        success = storage.update_conversation(conversation_id, {"title": title})
        if success:
            logger.info(f"已更新对话 {conversation_id} 的标题为 {title}")
        return success
    except Exception as e:
        logger.error(f"更新对话标题 {conversation_id} 时出错: {e}")
        return False

async def get_conversation_statistics() -> dict:
    """
    获取对话统计信息
    
    Returns:
        包含统计信息的字典
    """
    try:
        return storage.get_statistics()
    except Exception as e:
        logger.error(f"获取对话统计信息时出错: {e}")
        return {}