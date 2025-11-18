from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import logging

from .api.chat_json import chat_router
from .api.preset_json import preset_router
from .api.conversation_json import conversation_router
from .routes_json import router as page_router
from .storage.json_storage import storage
from .services.history_cleanup_json import cleanup_old_conversations
from .services.lm_studio_client_json import LMStudioClient
from .websocket.connection_manager import ConnectionManager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局变量
connection_manager = ConnectionManager()
lm_client = LMStudioClient()

@asynccontextmanager
async def lifespan(_app: FastAPI):
    # 启动时执行的代码
    logger.info("启动AI对话服务...")
    
    # 初始化存储（创建默认预设）
    await init_storage()
    
    # 启动历史记录清理任务
    _ = asyncio.create_task(periodic_cleanup())
    
    yield
    
    # 关闭时执行的代码
    logger.info("AI对话服务已关闭")

app = FastAPI(
    title="AI对话API",
    description="基于LM Studio的AI对话API服务",
    version="1.0.0",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应设置为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件和模板
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 注册路由
app.include_router(chat_router, prefix="/api", tags=["chat"])
app.include_router(preset_router, prefix="/api", tags=["presets"])
app.include_router(conversation_router, prefix="/api", tags=["conversations"])
app.include_router(page_router, tags=["pages"])

# 定期清理历史记录
async def periodic_cleanup():
    """定期清理历史记录"""
    while True:
        try:
            logger.info("开始清理历史记录...")
            deleted_count = await cleanup_old_conversations()
            logger.info(f"清理完成，删除了 {deleted_count} 条历史记录")
            
            # 每24小时执行一次清理
            await asyncio.sleep(24 * 60 * 60)  # 24小时
        except Exception as e:
            logger.error(f"清理历史记录时出错: {e}")
            # 出错后等待1小时再重试
            await asyncio.sleep(60 * 60)

# WebSocket连接处理
@app.websocket("/ws/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: str):
    await connection_manager.connect(websocket, conversation_id)
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_json()
            message: str = data.get("message", "")
            preset_id = data.get("preset_id", None)
            
            # 将消息转发给所有连接到同一会话的客户端
            await connection_manager.broadcast_to_conversation(
                conversation_id, 
                {"type": "message", "sender": "user", "content": message}  # type: ignore
            )
            
            # 获取AI回复
            try:
                response: str = await lm_client.get_response(
                    message=message,
                    conversation_id=conversation_id,
                    preset_id=preset_id,
                    websocket=websocket
                )
                
                # 广播AI回复
                await connection_manager.broadcast_to_conversation(
                    conversation_id,
                    {"type": "message", "sender": "ai", "content": response}  # type: ignore
                )
            except Exception as e:
                logger.error(f"获取AI回复时出错: {e}")
                await connection_manager.send_personal_message(
                    {"type": "error", "message": "AI服务暂时不可用，请稍后再试"},  # type: ignore
                    websocket
                )
                
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, conversation_id)

# 初始化存储（创建默认预设）
async def init_storage():
    """初始化JSON存储并创建默认预设"""
    try:
        # 检查是否已有预设
        presets = storage.get_presets()
        
        if len(presets) == 0:
            # 创建默认预设
            default_presets = [
                {
                    "name": "通用助手",
                    "description": "一个通用的AI助手，可以回答各种问题和提供建议",
                    "system_prompt": "你是一个有用的AI助手。请用友好、专业的方式回答用户的问题，并提供准确、有用的信息。如果不确定答案，请诚实地说明。",
                    "is_active": True
                },
                {
                    "name": "编程助手",
                    "description": "专门用于编程相关问题的AI助手",
                    "system_prompt": "你是一个专业的编程助手。请提供清晰的代码示例和解释，遵循最佳实践，并考虑代码的安全性和可维护性。",
                    "is_active": True
                },
                {
                    "name": "创意写作助手",
                    "description": "帮助用户进行创意写作的AI助手",
                    "system_prompt": "你是一个创意写作助手。请帮助用户创作故事、诗歌、剧本等内容，发挥想象力，并提供富有创意的建议。",
                    "is_active": True
                }
            ]
            
            for preset_data in default_presets:
                storage.create_preset(
                    name=preset_data["name"],
                    description=preset_data["description"],
                    system_prompt=preset_data["system_prompt"],
                    is_active=preset_data["is_active"]
                )
            
            logger.info("默认预设创建完成")
    except Exception as e:
        logger.error(f"初始化存储失败: {e}")
        raise



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)