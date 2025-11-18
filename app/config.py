import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # LM Studio API配置
    lm_studio_base_url: str = "http://localhost:1234"
    
    # 历史记录配置
    max_conversation_age_days: int = 30  # 对话保留天数
    cleanup_interval_hours: int = 24     # 清理间隔（小时）
    
    # 应用配置
    app_name: str = "AI对话API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    class Config:
        env_file = ".env"

settings = Settings()