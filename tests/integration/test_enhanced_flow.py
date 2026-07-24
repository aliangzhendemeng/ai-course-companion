"""增强流程集成测试：使用 Fake 组件验证上传 → 处理 → 单课问答 → 全局问答 → 删除完整流程。"""

import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.ai.llm.base import BaseLLM
from backend.ai.vision.base import BaseVisionAnalyzer
from backend.config import settings
from backend.database import create_db_and_tables, engine
from backend.main import app
from backend.models import Course
from sqlmodel import Session


class FakeLLM(BaseLLM):
    def chat(self, system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> str:
        if "整理课程大纲" in user_prompt:
            return json.dumps([{"title": "第一章", "timestamp": 0.0}])
        if "总结课程的核心知识点" in user_prompt:
            return "这是摘要"
        if "编写一份详细讲义" in user_prompt:
            return "这是讲义"
        return "这是回答"


class FakeVisionAnalyzer(BaseVisionAnalyzer):
    def understand_frame(self, image_path: str, prompt: str | None = None) -> str:
        return "画面描述"


@pytest.fixture
def client(tmp_path: Path, monkeypatch, reset_database):
    # 使用临时数据目录，避免污染真实数据
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    monkeypatch.setattr(settings, "upload_dir", str(data_dir / "uploads"))
    monkeypatch.setattr(settings, "frame_dir", str(data_dir / "frames"))
    monkeypatch.setattr(settings, "chroma_dir", str(data_dir / "chroma"))
    monkeypatch.setattr(settings, "bm25_dir", str(data_dir / "bm25"))

    create_db_and_tables()

    # 注入 Fake 组件，避免调用真实 API
    from backend.ai import factory
    import backend.api.courses as courses_module

    monkeypatch.setattr(factory, "create_summary_llm", lambda: FakeLLM())
    monkeypatch.setattr(factory, "create_chat_llm", lambda: FakeLLM())
    monkeypatch.setattr(factory, "create_vision_analyzer", lambda: FakeVisionAnalyzer())
    monkeypatch.setattr(courses_module, "_process_course", lambda course_id: None)

    with TestClient(app) as c:
        yield c

    shutil.rmtree(data_dir, ignore_errors=True)


def _make_video_file(path: Path) -> None:
    """创建一个最小视频文件占位。"""
    path.write_bytes(b"fake video content")


def test_enhanced_course_lifecycle(client: TestClient, tmp_path: Path):
    # 1. 上传
    video_path = tmp_path / "test.mp4"
    _make_video_file(video_path)

    with video_path.open("rb") as f:
        upload_resp = client.post(
            "/api/courses/upload",
            data={"title": "集成测试课程"},
            files={"file": ("test.mp4", f, "video/mp4")},
        )
    assert upload_resp.status_code == 200
    course_id = upload_resp.json()["id"]

    # 2. 手动更新为 completed 并注入索引数据（模拟处理完成）
    with Session(engine) as session:
        course = session.get(Course, course_id)
        course.status = "completed"
        session.add(course)
        session.commit()

    from backend.ai.rag_engine import RAGEngine

    rag = RAGEngine(llm=FakeLLM())
    rag.index_course(
        course_id,
        transcripts=[{"id": 1, "text": "神经网络基础", "start_time": 0.0}],
        frames=[{"id": 1, "timestamp": 1.0, "ocr_text": "感知机", "vision_desc": "图示"}],
    )

    # 3. 获取课程详情，验证视频流 URL
    detail_resp = client.get(f"/api/courses/{course_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["video_url"]

    # 4. 单课问答
    chat_resp = client.post(
        f"/api/chat/{course_id}",
        json={"question": "什么是神经网络？", "scope": "course"},
    )
    assert chat_resp.status_code == 200
    chat_data = chat_resp.json()
    assert chat_data["answer"]
    assert chat_data["course_id"] == course_id

    # 5. 全局问答
    global_resp = client.post(
        f"/api/chat/{course_id}",
        json={"question": "神经网络", "scope": "all"},
    )
    assert global_resp.status_code == 200
    global_data = global_resp.json()
    assert global_data["answer"]

    # 6. 删除课程
    delete_resp = client.delete(f"/api/courses/{course_id}")
    assert delete_resp.status_code == 200

    # 7. 验证已删除
    get_resp = client.get(f"/api/courses/{course_id}")
    assert get_resp.status_code == 404
