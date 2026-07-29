"""配置读写服务。"""

from pathlib import Path


class SettingsService:
    """管理应用配置，以 `.env` 为持久化载体。"""

    DEFAULT_MODEL = "deepseek"

    def __init__(self, env_path: str | Path | None = None) -> None:
        if env_path is None:
            env_path = Path(__file__).parent.parent.parent / ".env"
        self.env_path = Path(env_path)

    def _read_env(self) -> dict[str, str]:
        """读取 .env 文件为键值对，忽略空行和注释。"""
        if not self.env_path.exists():
            return {}
        result: dict[str, str] = {}
        with self.env_path.open("r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                result[key.strip()] = value.strip()
        return result

    def _write_env(self, data: dict[str, str]) -> None:
        """写回 .env，保留文件中已存在的其他变量和注释。"""
        self.env_path.parent.mkdir(parents=True, exist_ok=True)
        existing: dict[str, str] = {}
        comments_and_blanks: list[str] = []
        if self.env_path.exists():
            with self.env_path.open("r", encoding="utf-8") as f:
                for raw_line in f:
                    line = raw_line.rstrip("\n")
                    stripped = line.strip()
                    if not stripped or stripped.startswith("#") or "=" not in stripped:
                        comments_and_blanks.append(line)
                        continue
                    key, value = stripped.split("=", 1)
                    existing[key.strip()] = value.strip()

        merged = {**existing, **data}
        lines: list[str] = []
        for line in comments_and_blanks:
            lines.append(line)
        for key, value in sorted(merged.items()):
            lines.append(f"{key}={value}")
        lines.append("")
        with self.env_path.open("w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def _any_api_key(self, env: dict[str, str]) -> str:
        """找到一个可用的 API Key 作为通用回退。"""
        for key in ("DEEPSEEK_API_KEY", "GEMINI_API_KEY", "CLAUDE_API_KEY"):
            value = env.get(key, "")
            if value:
                return value
        for key in ("CHAT_API_KEY", "SUMMARY_API_KEY", "VISION_API_KEY"):
            value = env.get(key, "")
            if value:
                return value
        return ""

    def _resolve_api_key(self, env: dict[str, str], key: str) -> str:
        """解析某个模型的 API Key，支持通用回退。"""
        value = env.get(key, "")
        if value:
            return value
        return self._any_api_key(env)

    def load(self) -> dict:
        """加载配置，包含默认值和 API Key 回退。"""
        env = self._read_env()
        chat_api_key = self._resolve_api_key(env, "CHAT_API_KEY")
        summary_api_key = self._resolve_api_key(env, "SUMMARY_API_KEY")
        vision_api_key = self._resolve_api_key(env, "VISION_API_KEY")
        return {
            "chat_model": env.get("CHAT_MODEL") or self.DEFAULT_MODEL,
            "chat_api_key": chat_api_key,
            "summary_model": env.get("SUMMARY_MODEL") or self.DEFAULT_MODEL,
            "summary_api_key": summary_api_key,
            "vision_model": env.get("VISION_MODEL") or self.DEFAULT_MODEL,
            "vision_api_key": vision_api_key,
            "enable_vision": env.get("ENABLE_VISION", "false").lower() == "true",
            "is_configured": bool(chat_api_key or summary_api_key or vision_api_key),
        }

    def save(self, data: dict) -> dict:
        """保存配置到 .env，只覆盖传入的字段，未传入的保持原值。"""
        env = self._read_env()

        main_key = data.get("main_api_key", "")
        chat_key = data.get("chat_api_key", "")
        summary_key = data.get("summary_api_key", "")
        vision_key = data.get("vision_api_key", "")

        if main_key:
            # 同步通用 key 到角色 key 中未填写的项
            if not chat_key:
                chat_key = main_key
            if not summary_key:
                summary_key = main_key
            if not vision_key:
                vision_key = main_key
            # 同步旧的 provider key，但不要清空已有的其他 key
            env["DEEPSEEK_API_KEY"] = main_key

        env_data: dict[str, str] = {
            "CHAT_MODEL": data.get("chat_model") or env.get("CHAT_MODEL") or self.DEFAULT_MODEL,
            "CHAT_API_KEY": chat_key or env.get("CHAT_API_KEY", ""),
            "SUMMARY_MODEL": data.get("summary_model") or env.get("SUMMARY_MODEL") or self.DEFAULT_MODEL,
            "SUMMARY_API_KEY": summary_key or env.get("SUMMARY_API_KEY", ""),
            "VISION_MODEL": data.get("vision_model") or env.get("VISION_MODEL") or self.DEFAULT_MODEL,
            "VISION_API_KEY": vision_key or env.get("VISION_API_KEY", ""),
            "ENABLE_VISION": "true" if data.get("enable_vision") else "false",
        }
        env_data.update({k: v for k, v in env.items() if k not in env_data})

        self._write_env(env_data)
        return self.load()
