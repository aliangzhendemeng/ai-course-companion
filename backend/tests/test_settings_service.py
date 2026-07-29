"""SettingsService 单元测试。"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from backend.services.settings_service import SettingsService


@pytest.fixture
def service(tmp_path: Path):
    env_path = tmp_path / ".env"
    return SettingsService(env_path=env_path)


class TestSettingsServiceLoad:
    def test_default_values_when_no_env(self, service: SettingsService):
        result = service.load()
        assert result["chat_model"] == "deepseek"
        assert result["summary_model"] == "deepseek"
        assert result["vision_model"] == "deepseek"
        assert result["chat_api_key"] == ""
        assert result["summary_api_key"] == ""
        assert result["vision_api_key"] == ""
        assert result["enable_vision"] is False
        assert result["is_configured"] is False

    def test_api_key_fallback_to_deepseek(self, service: SettingsService):
        service._write_env({"DEEPSEEK_API_KEY": "sk-deepseek"})
        result = service.load()
        assert result["chat_api_key"] == "sk-deepseek"
        assert result["summary_api_key"] == "sk-deepseek"
        assert result["vision_api_key"] == "sk-deepseek"
        assert result["is_configured"] is True

    def test_role_key_priority_over_provider_key(self, service: SettingsService):
        service._write_env({
            "DEEPSEEK_API_KEY": "sk-deepseek",
            "CHAT_API_KEY": "sk-chat",
            "SUMMARY_API_KEY": "sk-summary",
            "VISION_API_KEY": "sk-vision",
        })
        result = service.load()
        assert result["chat_api_key"] == "sk-chat"
        assert result["summary_api_key"] == "sk-summary"
        assert result["vision_api_key"] == "sk-vision"

    def test_main_api_key_is_configured(self, service: SettingsService):
        service.save({"main_api_key": "sk-main"})
        result = service.load()
        # save 会把 main_api_key 同步到角色 key
        assert result["chat_api_key"] == "sk-main"
        assert result["is_configured"] is True


class TestSettingsServiceSave:
    def test_save_merges_with_existing_env(self, service: SettingsService):
        service._write_env({
            "DEEPSEEK_API_KEY": "sk-old",
            "GEMINI_API_KEY": "sk-gemini",
            "CUSTOM_VAR": "keep",
        })
        result = service.save({"chat_model": "gemini:gemini-1.5-flash"})
        assert result["chat_model"] == "gemini:gemini-1.5-flash"

        env = service._read_env()
        assert env["GEMINI_API_KEY"] == "sk-gemini"
        assert env["CUSTOM_VAR"] == "keep"
        assert env["CHAT_MODEL"] == "gemini:gemini-1.5-flash"

    def test_save_main_api_key_fills_empty_roles(self, service: SettingsService):
        service.save({
            "main_api_key": "sk-main",
            "chat_model": "deepseek",
            "summary_model": "deepseek",
            "vision_model": "deepseek",
            "enable_vision": True,
        })
        env = service._read_env()
        assert env["CHAT_API_KEY"] == "sk-main"
        assert env["SUMMARY_API_KEY"] == "sk-main"
        assert env["VISION_API_KEY"] == "sk-main"
        assert env["DEEPSEEK_API_KEY"] == "sk-main"
        assert env["ENABLE_VISION"] == "true"

    def test_save_main_key_overwrites_existing_role_key(self, service: SettingsService):
        service._write_env({"CHAT_API_KEY": "sk-existing-chat"})
        service.save({
            "main_api_key": "sk-main",
            "chat_model": "deepseek",
            "summary_model": "deepseek",
            "vision_model": "deepseek",
            "enable_vision": False,
        })
        env = service._read_env()
        # main_api_key 优先级更高，会覆盖已有角色 key
        assert env["CHAT_API_KEY"] == "sk-main"
        assert env["SUMMARY_API_KEY"] == "sk-main"
        assert env["DEEPSEEK_API_KEY"] == "sk-main"

    def test_save_specific_role_key_preserved_without_main_key(self, service: SettingsService):
        service._write_env({"CHAT_API_KEY": "sk-existing-chat", "SUMMARY_API_KEY": "sk-existing-summary"})
        service.save({
            "chat_model": "deepseek",
            "summary_model": "deepseek",
            "vision_model": "deepseek",
            "enable_vision": False,
        })
        env = service._read_env()
        assert env["CHAT_API_KEY"] == "sk-existing-chat"
        assert env["SUMMARY_API_KEY"] == "sk-existing-summary"

    def test_save_enable_vision_false(self, service: SettingsService):
        service._write_env({"ENABLE_VISION": "true"})
        service.save({"enable_vision": False})
        env = service._read_env()
        assert env["ENABLE_VISION"] == "false"


def test_default_env_path():
    """默认 env 路径为项目根目录 .env。"""
    service = SettingsService()
    assert service.env_path.name == ".env"
    assert "ai-course-companion" in str(service.env_path)
