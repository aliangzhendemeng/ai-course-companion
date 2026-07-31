"""学伴角色 API：角色列表/详情、形象素材、TTS 语音。"""

import logging

import edge_tts
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

from backend.services.character_service import CharacterService

logger = logging.getLogger(__name__)

router = APIRouter()

# 默认音色（角色未配置 voice 时回退）
DEFAULT_VOICE = "zh-CN-XiaoyiNeural"


class TTSRequest(BaseModel):
    text: str
    character_id: str | None = None


@router.get("")
def list_characters():
    """列出所有已安装角色（含素材可用性）。"""
    return CharacterService().list_characters()


@router.get("/{character_id}")
def get_character(character_id: str):
    """获取单个角色配置。"""
    info = CharacterService().get_character(character_id)
    if not info:
        raise HTTPException(status_code=404, detail="角色不存在")
    return info


@router.get("/{character_id}/assets/{motion}")
def get_motion_asset(character_id: str, motion: str, index: int | None = None):
    """返回某角色某动作的一张形象素材。

    目录有多张图时：index 缺省随机返回一张（轮换播放）；index 指定则按序号取（取模）。
    """
    path = CharacterService().get_asset_path(character_id, motion, index)
    if not path:
        raise HTTPException(status_code=404, detail="素材不存在")
    return FileResponse(path)


@router.post("/tts")
async def tts(payload: TTSRequest):
    """把文本合成为语音（edge-tts），音色随角色配置。返回 MP3。"""
    text = (payload.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="文本不能为空")
    # 限制长度，避免过长合成
    text = text[:300]

    voice = DEFAULT_VOICE
    if payload.character_id:
        info = CharacterService().get_character(payload.character_id)
        if info:
            voice = info.get("voice", {}).get("voice_id") or DEFAULT_VOICE

    try:
        communicate = edge_tts.Communicate(text, voice)
        audio = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio += chunk["data"]
    except Exception as e:
        logger.warning("TTS 合成失败: %s", e)
        raise HTTPException(status_code=502, detail=f"语音合成失败：{e}")

    if not audio:
        raise HTTPException(status_code=502, detail="语音合成结果为空")
    return Response(content=audio, media_type="audio/mpeg")
