"""网络查询测试：mock WebSearchService.search，验证 ask 集成与消息存储。"""

import json

import pytest
from sqlmodel import Session, SQLModel, create_engine

from backend.models import Course, Transcript
from backend.services.chat_service import ChatService
from backend.services.conversation_service import ConversationService
from backend.services.web_search_service import WebSearchService


class FakeLLM:
    model_identifier = "fake"

    def chat(self, system_prompt, user_prompt, max_tokens=800):
        return "回答"


class FakeRag:
    llm = FakeLLM()

    def query(self, course_id, question, history=None):
        return {"answer": "答：" + question, "sources": [], "debug": {}}


@pytest.fixture
def db_engine(tmp_path):
    eng = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    SQLModel.metadata.create_all(eng)
    return eng


@pytest.fixture(autouse=True)
def _patch_engines(db_engine, monkeypatch):
    import backend.services.chat_service as cs
    import backend.services.conversation_service as cv
    import backend.services.course_service as course_svc
    monkeypatch.setattr(cs, "engine", db_engine)
    monkeypatch.setattr(cv, "engine", db_engine)
    monkeypatch.setattr(course_svc, "engine", db_engine)


@pytest.fixture
def course_id(db_engine):
    with Session(db_engine) as s:
        c = Course(title="ws", video_path="/tmp/ws.mp4", status="completed")
        s.add(c); s.commit(); s.refresh(c)
        return c.id


def test_ask_with_web_search_stores_results(course_id, monkeypatch):
    """开启 web_search：结果附在 response 且存到 assistant 消息。"""
    monkeypatch.setattr(
        WebSearchService, "search", lambda self, q, n=5: [{"title": "T", "url": "https://t", "snippet": "S"}]
    )
    svc = ChatService(rag_engine=FakeRag())
    result = svc.ask(course_id, "什么是 X", web_search=True)
    assert len(result["web_results"]) == 1
    assert result["web_results"][0]["title"] == "T"

    msgs = ConversationService().messages(result["conversation_id"])
    assistant = [m for m in msgs if m.role == "assistant"][0]
    assert assistant.web_results  # 存了 JSON
    parsed = json.loads(assistant.web_results)
    assert parsed[0]["url"] == "https://t"


def test_ask_without_web_search(course_id):
    """未开启：web_results 为空，消息不存 web_results。"""
    svc = ChatService(rag_engine=FakeRag())
    result = svc.ask(course_id, "什么是 X")
    assert result["web_results"] == []
    msgs = ConversationService().messages(result["conversation_id"])
    assistant = [m for m in msgs if m.role == "assistant"][0]
    assert assistant.web_results is None


def test_web_search_failure_returns_empty(monkeypatch):
    """_search_sync 内部异常（浏览器启动失败）兜底返回空列表，不抛出。"""
    import backend.services.web_search_service as wss

    class _BadPW:
        def __enter__(self):
            class _P:
                @property
                def chromium(self):
                    class _C:
                        def launch(self, **k):
                            raise RuntimeError("browser fail")
                    return _C()
            return _P()

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(wss, "sync_playwright", lambda: _BadPW())
    # _search_sync 是子进程实际跑的函数，直接测其异常兜底
    results = wss._search_sync("任何词")
    assert results == []
