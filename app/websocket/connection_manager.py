import json
import logging
from typing import Dict, List
from fastapi import WebSocket

# 配置日志
logger = logging.getLogger(__name__)

class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 存储活跃连接 {conversation_id: [websocket1, websocket2, ...]}
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, conversation_id: str):
        """接受连接并添加到活跃连接列表"""
        await websocket.accept()
        if conversation_id not in self.active_connections:
            self.active_connections[conversation_id] = []
        self.active_connections[conversation_id].append(websocket)
        logger.info(f"WebSocket连接已建立: conversation_id={conversation_id}")
    
    def disconnect(self, websocket: WebSocket, conversation_id: str):
        """断开连接并从活跃连接列表中移除"""
        if conversation_id in self.active_connections:
            if websocket in self.active_connections[conversation_id]:
                self.active_connections[conversation_id].remove(websocket)
            
            # 如果该会话没有活跃连接了，则删除该会话记录
            if not self.active_connections[conversation_id]:
                del self.active_connections[conversation_id]
        
        logger.info(f"WebSocket连接已断开: conversation_id={conversation_id}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """向特定连接发送消息"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"发送个人消息时出错: {e}")
    
    async def broadcast_to_conversation(self, conversation_id: str, message: dict):
        """向特定会话的所有连接广播消息"""
        if conversation_id in self.active_connections:
            disconnected_connections = []
            
            for connection in self.active_connections[conversation_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"广播消息时出错: {e}")
                    disconnected_connections.append(connection)
            
            # 清理断开的连接
            for connection in disconnected_connections:
                self.disconnect(connection, conversation_id)
    
    def get_active_connections_count(self, conversation_id: str = None) -> int:
        """获取活跃连接数量"""
        if conversation_id:
            return len(self.active_connections.get(conversation_id, []))
        else:
            # 返回所有会话的总连接数
            total = 0
            for connections in self.active_connections.values():
                total += len(connections)
            return total
    
    def get_active_conversations(self) -> List[str]:
        """获取所有活跃会话ID"""
        return list(self.active_connections.keys())