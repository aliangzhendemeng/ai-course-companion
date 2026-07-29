"""配置相关 API。"""

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.settings_service import SettingsService

router = APIRouter()


class SettingsPayload(BaseModel):
    chat_model: str | None = "deepseek"
    chat_api_key: str | None = ""
    summary_model: str | None = "deepseek"
    summary_api_key: str | None = ""
    vision_model: str | None = "deepseek"
    vision_api_key: str | None = ""
    enable_vision: bool = False


class SettingsResponse(BaseModel):
    chat_model: str
    chat_api_key: str
    summary_model: str
    summary_api_key: str
    vision_model: str
    vision_api_key: str
    enable_vision: bool
    is_configured: bool
    restart_required: bool = True


@router.get("", response_model=SettingsResponse)
def get_settings():
    """获取当前配置（不返回明文 key 以外的敏感信息）。"""
    data = SettingsService().load()
    return SettingsResponse(
        chat_model=data["chat_model"],
        chat_api_key=data["chat_api_key"],
        summary_model=data["summary_model"],
        summary_api_key=data["summary_api_key"],
        vision_model=data["vision_model"],
        vision_api_key=data["vision_api_key"],
        enable_vision=data["enable_vision"],
        is_configured=data["is_configured"],
    )


@router.post("", response_model=SettingsResponse)
def save_settings(payload: SettingsPayload):
    """保存配置到 .env，需要重启后端才能完全生效。"""
    service = SettingsService()
    data = service.save(payload.model_dump(exclude_unset=True))
    return SettingsResponse(
        chat_model=data["chat_model"],
        chat_api_key=data["chat_api_key"],
        summary_model=data["summary_model"],
        summary_api_key=data["summary_api_key"],
        vision_model=data["vision_model"],
        vision_api_key=data["vision_api_key"],
        enable_vision=data["enable_vision"],
        is_configured=data["is_configured"],
        restart_required=True,
    )


@router.post("/restart")
def restart_backend():
    """触发后端重载使新配置生效。

    在 uvicorn --reload 模式下，触碰 .env 文件即会触发自动重载；
    非 reload 模式下需用户手动重启（返回提示）。
    """
    env_path = SettingsService().env_path
    try:
        # 更新 .env 的修改时间，触发 uvicorn reload（若开启）
        if env_path.exists():
            os.utime(env_path, None)
        else:
            Path(env_path).touch()
        return {"message": "已触发重载，配置即将生效（reload 模式下自动完成）", "reloaded": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"触发重载失败，请手动重启后端: {e}")
