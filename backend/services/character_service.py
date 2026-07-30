"""学伴角色服务：扫描 assets/characters/ 下的角色定义与素材，供学伴系统使用。

设计（代码与素材分离，合规前提）：
- 角色的"配置"（meta.json：名字/口头禅/语气 prompt/音色/动作槽）可进仓库。
- 角色的"形象素材"（图片/动画帧）不进 git，由用户本地放入 assets/characters/<id>/。
- 每个角色可附 manifest.json 声明素材版本，后端据此识别有哪些素材、缺失时前端降级占位。
"""

import json
import logging
from pathlib import Path

from backend.config import settings

logger = logging.getLogger(__name__)

# 角色素材根目录（本地自放，gitignore）
CHARACTERS_DIR_NAME = "assets/characters"


def characters_root() -> Path:
    return settings.project_root / CHARACTERS_DIR_NAME


class CharacterService:
    """扫描并读取角色定义。"""

    def list_characters(self) -> list[dict]:
        """扫描所有角色，返回每个角色的配置 + 素材可用性。"""
        root = characters_root()
        result = []
        if not root.is_dir():
            return result
        for child in sorted(root.iterdir()):
            if not child.is_dir():
                continue
            info = self.get_character(child.name)
            if info:
                result.append(info)
        return result

    def get_character(self, character_id: str) -> dict | None:
        """读取单个角色：meta.json（必需）+ 素材清单。"""
        char_dir = characters_root() / character_id
        meta_path = char_dir / "meta.json"
        if not meta_path.is_file():
            return None
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("角色 %s 的 meta.json 解析失败: %s", character_id, e)
            return None

        motions = meta.get("motions", [])
        # 检测每个动作槽是否有素材（该动作目录下有图片/GIF/WebP 等）
        motion_assets: dict[str, bool] = {}
        for motion in motions:
            motion_dir = char_dir / motion
            motion_assets[motion] = self._has_image(motion_dir)
        has_any_asset = any(motion_assets.values())

        return {
            "id": meta.get("id", character_id),
            "name": meta.get("name", character_id),
            "catchphrases": meta.get("catchphrases", {}),
            "persona_prompt": meta.get("persona_prompt", ""),
            "voice": meta.get("voice", {}),
            "motions": motions,
            # 素材可用性：前端据此决定显示动画还是占位
            "motion_assets": motion_assets,
            "has_assets": has_any_asset,
        }

    @staticmethod
    def _has_image(directory: Path) -> bool:
        if not directory.is_dir():
            return False
        exts = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}
        return any(f.suffix.lower() in exts for f in directory.iterdir() if f.is_file())

    def get_asset_path(self, character_id: str, motion: str) -> Path | None:
        """返回某角色某动作的代表性素材文件路径（取该动作目录下第一个图片）。"""
        motion_dir = characters_root() / character_id / motion
        if not motion_dir.is_dir():
            return None
        exts = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}
        for f in sorted(motion_dir.iterdir()):
            if f.is_file() and f.suffix.lower() in exts:
                return f
        return None
