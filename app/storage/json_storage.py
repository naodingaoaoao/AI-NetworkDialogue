import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import uuid

# 配置日志
logger = logging.getLogger(__name__)

class JSONStorage:
    """JSON文件存储管理器"""
    
    def __init__(self, storage_dir: str = "data"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        # 数据文件路径
        self.conversations_file = self.storage_dir / "conversations.json"
        self.messages_file = self.storage_dir / "messages.json"
        self.presets_file = self.storage_dir / "presets.json"
        
        # 初始化数据文件
        self._init_storage_files()
    
    def _init_storage_files(self):
        """初始化数据文件"""
        if not self.conversations_file.exists():
            self._save_json(self.conversations_file, {})
        
        if not self.messages_file.exists():
            self._save_json(self.messages_file, {})
            
        if not self.presets_file.exists():
            self._save_json(self.presets_file, {})
    
    def _save_json(self, file_path: Path, data: Dict[str, Any]):
        """保存数据到JSON文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存文件 {file_path} 失败: {e}")
            raise
    
    def _load_json(self, file_path: Path) -> Dict[str, Any]:
        """从JSON文件加载数据"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"加载文件 {file_path} 失败: {e}")
            return {}
    
    # ===== 对话管理 =====
    def get_conversations(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """获取对话列表"""
        conversations = self._load_json(self.conversations_file)
        
        # 转换为列表并按更新时间排序
        conv_list = []
        for conv_id, conv_data in conversations.items():
            conv_list.append({
                "id": conv_id,
                **conv_data
            })
        
        # 排序
        conv_list.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        
        # 分页
        return conv_list[offset:offset + limit]
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """获取特定对话"""
        conversations = self._load_json(self.conversations_file)
        
        if conversation_id in conversations:
            return {
                "id": conversation_id,
                **conversations[conversation_id]
            }
        return None
    
    def create_conversation(self, title: str = "新建对话", preset_id: Optional[int] = None) -> str:
        """创建新对话"""
        conversations = self._load_json(self.conversations_file)
        
        new_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        conversations[new_id] = {
            "title": title,
            "preset_id": preset_id,
            "created_at": now,
            "updated_at": now
        }
        
        self._save_json(self.conversations_file, conversations)
        return new_id
    
    def update_conversation(self, conversation_id: str, data: Dict[str, Any]) -> bool:
        """更新对话"""
        conversations = self._load_json(self.conversations_file)
        
        if conversation_id not in conversations:
            return False
        
        conversations[conversation_id].update(data)
        conversations[conversation_id]["updated_at"] = datetime.now().isoformat()
        
        self._save_json(self.conversations_file, conversations)
        return True
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """删除对话"""
        conversations = self._load_json(self.conversations_file)
        messages = self._load_json(self.messages_file)
        
        if conversation_id not in conversations:
            return False
        
        # 删除对话
        del conversations[conversation_id]
        self._save_json(self.conversations_file, conversations)
        
        # 删除相关消息
        if conversation_id in messages:
            del messages[conversation_id]
            self._save_json(self.messages_file, messages)
        
        return True
    
    # ===== 消息管理 =====
    def get_messages(self, conversation_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取对话消息"""
        messages = self._load_json(self.messages_file)
        
        if conversation_id not in messages:
            return []
        
        msg_list = messages[conversation_id]
        
        # 按时间排序
        msg_list.sort(key=lambda x: x.get("created_at", ""))
        
        # 限制数量
        if limit:
            msg_list = msg_list[-limit:]
        
        return msg_list
    
    def add_message(self, conversation_id: str, sender: str, content: str) -> bool:
        """添加消息"""
        messages = self._load_json(self.messages_file)
        conversations = self._load_json(self.conversations_file)
        
        # 确保对话存在
        if conversation_id not in conversations:
            return False
        
        # 初始化消息列表
        if conversation_id not in messages:
            messages[conversation_id] = []
        
        # 添加消息
        new_message = {
            "id": len(messages[conversation_id]) + 1,
            "sender": sender,
            "content": content,
            "created_at": datetime.now().isoformat()
        }
        
        messages[conversation_id].append(new_message)
        
        # 更新对话时间戳
        conversations[conversation_id]["updated_at"] = new_message["created_at"]
        
        # 保存数据
        self._save_json(self.messages_file, messages)
        self._save_json(self.conversations_file, conversations)
        
        return True
    
    # ===== 预设管理 =====
    def get_presets(self) -> List[Dict[str, Any]]:
        """获取所有预设"""
        presets = self._load_json(self.presets_file)
        
        preset_list = []
        for preset_id, preset_data in presets.items():
            preset_list.append({
                "id": int(preset_id),
                **preset_data
            })
        
        # 按创建时间排序
        preset_list.sort(key=lambda x: x.get("created_at", ""))
        return preset_list
    
    def get_preset(self, preset_id: int) -> Optional[Dict[str, Any]]:
        """获取特定预设"""
        presets = self._load_json(self.presets_file)
        
        preset_id_str = str(preset_id)
        if preset_id_str in presets:
            return {
                "id": preset_id,
                **presets[preset_id_str]
            }
        return None
    
    def create_preset(self, name: str, description: str, system_prompt: str, 
                    is_active: bool = True, parameters: Optional[Dict[str, Any]] = None) -> int:
        """创建新预设"""
        presets = self._load_json(self.presets_file)
        
        # 生成新ID
        existing_ids = [int(pid) for pid in presets.keys() if pid.isdigit()]
        new_id = max(existing_ids, default=0) + 1
        
        now = datetime.now().isoformat()
        
        presets[str(new_id)] = {
            "name": name,
            "description": description,
            "system_prompt": system_prompt,
            "is_active": is_active,
            "parameters": parameters or {},
            "created_at": now,
            "updated_at": now
        }
        
        self._save_json(self.presets_file, presets)
        return new_id
    
    def update_preset(self, preset_id: int, data: Dict[str, Any]) -> bool:
        """更新预设"""
        presets = self._load_json(self.presets_file)
        
        preset_id_str = str(preset_id)
        if preset_id_str not in presets:
            return False
        
        presets[preset_id_str].update(data)
        presets[preset_id_str]["updated_at"] = datetime.now().isoformat()
        
        self._save_json(self.presets_file, presets)
        return True
    
    def delete_preset(self, preset_id: int) -> bool:
        """删除预设"""
        presets = self._load_json(self.presets_file)
        
        preset_id_str = str(preset_id)
        if preset_id_str not in presets:
            return False
        
        del presets[preset_id_str]
        self._save_json(self.presets_file, presets)
        return True
    
    def get_preset_usage(self, preset_id: int) -> Dict[str, Any]:
        """获取预设使用统计"""
        conversations = self._load_json(self.conversations_file)
        
        count = 0
        for conv in conversations.values():
            if conv.get("preset_id") == preset_id:
                count += 1
        
        preset = self.get_preset(preset_id)
        
        return {
            "preset_id": preset_id,
            "preset_name": preset.get("name", "") if preset else "",
            "conversation_count": count,
            "is_active": preset.get("is_active", False) if preset else False
        }
    
    # ===== 统计信息 =====
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        conversations = self._load_json(self.conversations_file)
        messages = self._load_json(self.messages_file)
        
        total_conversations = len(conversations)
        
        # 计算总消息数
        total_messages = 0
        for msg_list in messages.values():
            total_messages += len(msg_list)
        
        # 最近7天的对话数
        seven_days_ago = (datetime.now().replace(microsecond=0) - 
                         timedelta(days=7)).isoformat()
        
        recent_conversations = 0
        oldest_date = None
        
        for conv in conversations.values():
            created_at = conv.get("created_at", "")
            
            if not oldest_date or created_at < oldest_date:
                oldest_date = created_at
            
            if created_at >= seven_days_ago:
                recent_conversations += 1
        
        return {
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "recent_conversations_7_days": recent_conversations,
            "oldest_conversation_date": oldest_date,
            "max_age_days": 30  # 默认保留30天
        }
    
    # ===== 历史清理 =====
    def cleanup_old_conversations(self, days: int = 30) -> int:
        """清理旧对话"""
        conversations = self._load_json(self.conversations_file)
        messages = self._load_json(self.messages_file)
        
        cutoff_date = (datetime.now().replace(microsecond=0) - 
                      timedelta(days=days)).isoformat()
        
        # 找出需要删除的对话
        to_delete = []
        for conv_id, conv_data in conversations.items():
            if conv_data.get("updated_at", "") < cutoff_date:
                to_delete.append(conv_id)
        
        # 删除对话和消息
        for conv_id in to_delete:
            del conversations[conv_id]
            if conv_id in messages:
                del messages[conv_id]
        
        # 保存数据
        self._save_json(self.conversations_file, conversations)
        self._save_json(self.messages_file, messages)
        
        return len(to_delete)

# 全局存储实例
storage = JSONStorage()