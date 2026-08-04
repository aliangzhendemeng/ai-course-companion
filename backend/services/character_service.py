"""学伴角色服务：扫描 assets/characters/ 下的角色定义与素材，供学伴系统使用。

设计（代码与素材分离，合规前提）：
- 角色的"配置"（meta.json：名字/口头禅/语气 prompt/音色/动作槽）可进仓库。
- 角色的"形象素材"（图片/动画帧）不进 git，由用户本地放入 assets/characters/<id>/。
- 每个动作槽目录可放多张图，后端随机返回一张，实现轮换播放。
"""

import json
import logging
import random
from pathlib import Path

from backend.config import settings

logger = logging.getLogger(__name__)

# 角色素材根目录（本地自放，gitignore）
CHARACTERS_DIR_NAME = "assets/characters"

_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}


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
        # 检测每个动作槽有多少张素材（供前端占位降级 + 轮换计数）
        motion_assets: dict[str, bool] = {}
        motion_counts: dict[str, int] = {}
        for motion in motions:
            files = self._image_files(char_dir / motion)
            motion_assets[motion] = len(files) > 0
            motion_counts[motion] = len(files)
        has_any_asset = any(motion_assets.values())

        return {
            "id": meta.get("id", character_id),
            "name": meta.get("name", character_id),
            "catchphrases": meta.get("catchphrases", {}),
            "persona_prompt": meta.get("persona_prompt", ""),
            "voice": meta.get("voice", {}),
            "motions": motions,
            "motion_assets": motion_assets,
            "motion_counts": motion_counts,
            "has_assets": has_any_asset,
        }

    @staticmethod
    def _image_files(directory: Path) -> list[Path]:
        """该动作目录下全部图片文件（排序，保证可复现）。"""
        if not directory.is_dir():
            return []
        return sorted(
            f for f in directory.iterdir() if f.is_file() and f.suffix.lower() in _IMAGE_EXTS
        )

    def get_asset_path(self, character_id: str, motion: str, index: int | None = None) -> Path | None:
        """返回某角色某动作的一张素材路径。

        - index 为 None：随机返回一张（轮换播放）
        - index 指定：返回第 index 张（取模，便于前端按序号轮换）
        目录无图返回 None。
        """
        files = self._image_files(characters_root() / character_id / motion)
        if not files:
            return None
        if index is None:
            return random.choice(files)
        return files[index % len(files)]
