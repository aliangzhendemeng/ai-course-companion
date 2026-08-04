"""图片问答测试。"""

import base64

import pytest
from sqlmodel import Session, SQLModel, create_engine

from backend.models import Course
from backend.services.chat_service import ChatService


class FakeLLM:
    def chat(self, system_prompt: str, user_prompt: str, max_tokens: int = 1200) -> str:
        if "图片内容描述" in user_prompt:
            return "图中是一个三角形，问题答案：等边三角形。"
        return "ok"


class FakeVision:
    def understand_frame(self, image_path) -> str:
        return "图片显示一个几何图形"


@pytest.fixture
def db_engine(tmp_path):
    eng = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    SQLModel.metadata.create_all(eng)
    return eng


@pytest.fixture
def patch_engine(db_engine, monkeypatch):
    import backend.services.chat_service as cs
    monkeypatch.setattr(cs, "engine", db_engine)


@pytest.fixture
def course_id(db_engine):
    with Session(db_engine) as s:
        c = Course(title="img", video_path="/tmp/img.mp4", status="processing")
        s.add(c); s.commit(); s.refresh(c)
        return c.id


def _b64_png() -> str:
    # 1x1 png
    raw = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M8AAAMBAQDJ/pLvAAAAAElFTkSuQmCC"
    )
    return "data:image/png;base64," + base64.b64encode(raw).decode()


def _service(db_engine):
    class FakeRag:
        llm = FakeLLM()
    return ChatService(rag_engine=FakeRag(), vision_analyzer=FakeVision())


def test_image_answer_uses_vision_then_llm(db_engine, patch_engine, course_id):
    svc = _service(db_engine)
    result = svc.ask(course_id, "这是什么图形？", image=_b64_png())
    assert "等边三角形" in result["answer"]
    assert result["sources"] == []
    assert result["answer_message_id"]


def test_image_answer_saves_messages(db_engine, patch_engine, course_id):
    svc = _service(db_engine)
    svc.ask(course_id, "问题", image=_b64_png())
    with Session(db_engine) as s:
        from backend.models import ChatMessage
        msgs = list(s.exec(__import__("sqlmodel").select(ChatMessage)).all())
    assert len(msgs) == 2  # user + assistant
    assert msgs[0].role == "user"
    assert "[附图片]" in msgs[0].content
    assert msgs[1].role == "assistant"


def test_image_works_even_if_course_not_completed(db_engine, patch_engine, course_id):
    """图片问答不要求课程处理完成。"""
    svc = _service(db_engine)
    result = svc.ask(course_id, "x", image=_b64_png())  # course status=processing
    assert result["answer"]


def test_decode_image_handles_data_url(db_engine, patch_engine, course_id):
    svc = _service(db_engine)
    mime, raw = svc._decode_image(_b64_png())
    assert mime == "image/png"
    assert len(raw) > 0


def test_decode_image_handles_raw_base64(db_engine, patch_engine, course_id):
    svc = _service(db_engine)
    raw_b64 = base64.b64encode(b"\x89PNG fake").decode()
    mime, raw = svc._decode_image(raw_b64)
    assert raw == b"\x89PNG fake"
