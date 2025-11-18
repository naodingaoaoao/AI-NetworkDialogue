import aiohttp
import json
import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..config import settings
from ..storage.json_storage import storage

# 配置日志
logger = logging.getLogger(__name__)

class LMStudioClient:
    """LM Studio API客户端 - JSON存储版"""
    
    def __init__(self):
        self.base_url = settings.lm_studio_base_url
        self.default_model = None  # 将在首次调用时获取
    
    async def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/v1/models") as response:
                    if response.status == 200:
                        data = await response.json()
                        return [model["id"] for model in data.get("data", [])]
                    else:
                        logger.error(f"获取模型列表失败: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"获取模型列表时出错: {e}")
            return []
    
    async def get_default_model(self) -> Optional[str]:
        """获取默认模型"""
        if self.default_model:
            return self.default_model
            
        models = await self.get_available_models()
        if models:
            self.default_model = models[0]
            return self.default_model
        return None
    
    async def get_response(
        self, 
        message: str, 
        conversation_id: Optional[str] = None, 
        preset_id: Optional[int] = None,
        websocket: Optional[Any] = None
    ) -> str:
        """获取AI响应"""
        
        # 获取或创建对话
        conversation = await self._get_or_create_conversation(conversation_id, preset_id)
        
        # 获取预设
        preset = None
        if preset_id:
            preset = storage.get_preset(preset_id)
        
        # 获取历史消息（限制最近10条作为上下文）
        history_messages = storage.get_messages(conversation["id"], limit=10)
        
        # 构建消息数组
        messages = []
        
        # 添加系统提示
        if preset:
            messages.append({"role": "system", "content": preset["system_prompt"]})
        else:
            messages.append({"role": "system", "content": "你是一个有用的AI助手。请友好、专业地回答用户问题。"})
        
        # 添加历史对话
        for msg in history_messages:
            role = "user" if msg["sender"] == "user" else "assistant"
            messages.append({"role": role, "content": msg["content"]})
        
        # 添加当前用户消息
        messages.append({"role": "user", "content": message})
        
        # 保存用户消息到存储
        storage.add_message(conversation["id"], "user", message)
        
        # 调用LM Studio API
        response_text = await self._call_lm_studio_api(messages, websocket)
        
        # 保存AI回复到存储
        storage.add_message(conversation["id"], "ai", response_text)
        
        return response_text
    
    async def _get_or_create_conversation(
        self, 
        conversation_id: Optional[str], 
        preset_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """获取或创建对话"""
        if conversation_id:
            # 尝试获取现有对话
            conversation = storage.get_conversation(conversation_id)
            if conversation:
                # 更新预设
                if preset_id and conversation.get("preset_id") != preset_id:
                    storage.update_conversation(conversation_id, {"preset_id": preset_id})
                    conversation["preset_id"] = preset_id
                return conversation
        
        # 创建新对话
        new_id = storage.create_conversation("新建对话", preset_id)
        return storage.get_conversation(new_id)
    
    async def _call_lm_studio_api(
        self, 
        messages: List[Dict[str, str]], 
        websocket: Optional[Any] = None
    ) -> str:
        """调用LM Studio API"""
        
        # 获取默认模型
        model = await self.get_default_model()
        if not model:
            raise Exception("无法获取可用的模型")
        
        # 构建请求数据
        payload = {
            "model": model,
            "messages": messages,
            "stream": websocket is not None,  # 如果有websocket连接则启用流式响应
            "temperature": 0.7,
            "max_tokens": 2048
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"LM Studio API错误: {response.status} - {error_text}")
                    
                    if websocket:
                        # 流式响应处理
                        response_text = ""
                        async for line in response.content:
                            line = line.decode('utf-8').strip()
                            if line.startswith("data: ") and not line.endswith("[DONE]"):
                                try:
                                    data = json.loads(line[6:])
                                    if "choices" in data and len(data["choices"]) > 0:
                                        delta = data["choices"][0].get("delta", {})
                                        content = delta.get("content", "")
                                        if content:
                                            response_text += content
                                            # 发送流式数据到客户端
                                            await websocket.send_json({
                                                "type": "stream",
                                                "content": content
                                            })
                                except json.JSONDecodeError:
                                    continue
                        
                        return response_text
                    else:
                        # 非流式响应
                        data = await response.json()
                        if "choices" in data and len(data["choices"]) > 0:
                            return data["choices"][0]["message"]["content"]
                        else:
                            raise Exception("API响应格式不正确")
        
        except aiohttp.ClientError as e:
            logger.error(f"调用LM Studio API时出错: {e}")
            raise Exception("无法连接到LM Studio API，请确保服务正在运行")
        except Exception as e:
            logger.error(f"处理API响应时出错: {e}")
            raise