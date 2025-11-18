import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..storage.json_storage import storage

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由
preset_router = APIRouter()

# 请求/响应模型
class PresetCreate(BaseModel):
    name: str
    description: Optional[str] = None
    system_prompt: str
    parameters: Optional[Dict[str, Any]] = None
    is_active: bool = True

class PresetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class PresetResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    system_prompt: str
    parameters: Optional[Dict[str, Any]]
    is_active: bool
    created_at: str
    updated_at: str

@preset_router.get("/", response_model=List[PresetResponse])
async def get_presets():
    """
    获取所有预设列表
    """
    try:
        presets = storage.get_presets()
        
        return [
            PresetResponse(
                id=preset["id"],
                name=preset["name"],
                description=preset.get("description"),
                system_prompt=preset["system_prompt"],
                parameters=preset.get("parameters", {}),
                is_active=preset.get("is_active", True),
                created_at=preset.get("created_at", ""),
                updated_at=preset.get("updated_at", "")
            )
            for preset in presets
        ]
            
    except Exception as e:
        logger.error(f"获取预设列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取预设列表失败: {str(e)}")

@preset_router.get("/{preset_id}", response_model=PresetResponse)
async def get_preset(preset_id: int):
    """
    获取特定预设详情
    """
    try:
        preset = storage.get_preset(preset_id)
            
        if not preset:
            raise HTTPException(status_code=404, detail="预设不存在")
            
        return PresetResponse(
            id=preset["id"],
            name=preset["name"],
            description=preset.get("description"),
            system_prompt=preset["system_prompt"],
            parameters=preset.get("parameters", {}),
            is_active=preset.get("is_active", True),
            created_at=preset.get("created_at", ""),
            updated_at=preset.get("updated_at", "")
        )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取预设详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取预设详情失败: {str(e)}")

@preset_router.post("/", response_model=PresetResponse)
async def create_preset(preset_data: PresetCreate):
    """
    创建新预设
    """
    try:
        # 检查名称是否已存在
        presets = storage.get_presets()
        for preset in presets:
            if preset["name"] == preset_data.name:
                raise HTTPException(status_code=400, detail="预设名称已存在")
            
        # 创建新预设
        new_id = storage.create_preset(
            name=preset_data.name,
            description=preset_data.description or "",
            system_prompt=preset_data.system_prompt,
            parameters=preset_data.parameters or {},
            is_active=preset_data.is_active
        )
            
        preset = storage.get_preset(new_id)
            
        return PresetResponse(
            id=preset["id"],
            name=preset["name"],
            description=preset.get("description"),
            system_prompt=preset["system_prompt"],
            parameters=preset.get("parameters", {}),
            is_active=preset.get("is_active", True),
            created_at=preset.get("created_at", ""),
            updated_at=preset.get("updated_at", "")
        )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建预设失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建预设失败: {str(e)}")

@preset_router.put("/{preset_id}", response_model=PresetResponse)
async def update_preset(preset_id: int, preset_data: PresetUpdate):
    """
    更新预设
    """
    try:
        preset = storage.get_preset(preset_id)
            
        if not preset:
            raise HTTPException(status_code=404, detail="预设不存在")
            
        # 检查名称是否与其他预设重复
        if preset_data.name and preset_data.name != preset["name"]:
            presets = storage.get_presets()
            for existing_preset in presets:
                if existing_preset["id"] != preset_id and existing_preset["name"] == preset_data.name:
                    raise HTTPException(status_code=400, detail="预设名称已存在")
            
        # 更新字段
        update_data = preset_data.dict(exclude_unset=True)
        success = storage.update_preset(preset_id, update_data)
            
        if not success:
            raise HTTPException(status_code=500, detail="更新预设失败")
            
        preset = storage.get_preset(preset_id)
            
        return PresetResponse(
            id=preset["id"],
            name=preset["name"],
            description=preset.get("description"),
            system_prompt=preset["system_prompt"],
            parameters=preset.get("parameters", {}),
            is_active=preset.get("is_active", True),
            created_at=preset.get("created_at", ""),
            updated_at=preset.get("updated_at", "")
        )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新预设失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新预设失败: {str(e)}")

@preset_router.delete("/{preset_id}")
async def delete_preset(preset_id: int):
    """
    删除预设
    """
    try:
        preset = storage.get_preset(preset_id)
            
        if not preset:
            raise HTTPException(status_code=404, detail="预设不存在")
            
        success = storage.delete_preset(preset_id)
            
        if success:
            return {"message": "预设删除成功"}
        else:
            raise HTTPException(status_code=500, detail="删除预设失败")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除预设失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除预设失败: {str(e)}")

@preset_router.get("/{preset_id}/usage")
async def get_preset_usage(preset_id: int):
    """
    获取预设使用统计
    """
    try:
        preset = storage.get_preset(preset_id)
            
        if not preset:
            raise HTTPException(status_code=404, detail="预设不存在")
            
        # 获取使用此预设的对话数量
        usage = storage.get_preset_usage(preset_id)
            
        return usage
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取预设使用统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取预设使用统计失败: {str(e)}")