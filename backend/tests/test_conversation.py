"""会话制问答测试：ConversationService CRUD + ChatService 多轮 + 旧数据迁移。"""

import json

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from backend.models import ChatMessage, Course, Transcript
from backend.services.chat_service import ChatService
from backend.services.conversation_service import ConversationService


class FakeLLM:
    model_identifier = "fake"

    def chat(self, system_prompt: str, user_prompt: str, max_tokens: int = 800) -> str:
        return "llm回答"


class FakeRag:
    """模拟 RAGEngine，记录传入的 history。"""

    def __init__(self):
        self.llm = FakeLLM()
        self.last_history = None

    def query(self, course_id, question, history=None):
        self.last_history = history or []
        return {"answer": f"答：{question}", "sources": [], "debug": {}}

    def query_all(self, question, history=None):
        self.last_history = history or []
        return {"answer": "全局答", "sources": [], "debug": {}}

    def query_multiple(self, course_ids, question, history=None):
        self.last_history = history or []
        return {"answer": "多课答", "sources": [], "debug": {}}


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
    import backend.database as dbmod
    monkeypatch.setattr(cs, "engine", db_engine)
    monkeypatch.setattr(cv, "engine", db_engine)
    monkeypatch.setattr(course_svc, "engine", db_engine)
    monkeypatch.setattr(dbmod, "engine", db_engine)


@pytest.fixture
def course_id(db_engine):
    with Session(db_engine) as s:
        c = Course(title="会话测试", video_path="/tmp/c.mp4", status="completed")
        s.add(c); s.commit(); s.refresh(c)
        return c.id


# ----- ChatService 多轮 -----

def test_ask_creates_new_conversation(course_id):
    rag = FakeRag()
    result = ChatService(rag_engine=rag).ask(course_id, "什么是过拟合")
    assert result["conversation_id"]
    msgs = ConversationService().messages(result["conversation_id"])
    assert len(msgs) == 2  # user + assistant
    assert msgs[0].role == "user" and msgs[1].role == "assistant"
    conv = ConversationService().get(result["conversation_id"])
    assert conv.title == "什么是过拟合"  # 标题取首问


def test_ask_continues_with_history(course_id):
    rag = FakeRag()
    svc = ChatService(rag_engine=rag)
    r1 = svc.ask(course_id, "什么是过拟合")
    cid = r1["conversation_id"]
    r2 = svc.ask(course_id, "再详细讲讲", conversation_id=cid)
    assert r2["conversation_id"] == cid  # 续写同一会话
    # 续写时把上一轮 user+assistant 作为 history 传入
    assert len(rag.last_history) == 2
    assert rag.last_history[0][0] == "user"
    assert rag.last_history[1][0] == "assistant"
    msgs = ConversationService().messages(cid)
    assert len(msgs) == 4  # 两轮共 4 条


def test_ask_rejectes_foreign_conversation(course_id, db_engine):
    # 另一门课
    with Session(db_engine) as s:
        c2 = Course(title="别的课", video_path="/tmp/c2.mp4", status="completed")
        s.add(c2); s.commit(); s.refresh(c2)
        other = c2.id
    svc = ChatService(rag_engine=FakeRag())
    r = svc.ask(other, "问题")
    with pytest.raises(ValueError, match="不属于"):
        svc.ask(course_id, "续写", conversation_id=r["conversation_id"])


def test_history_truncated_to_six(course_id):
    """历史窗口最多 6 条。"""
    rag = FakeRag()
    svc = ChatService(rag_engine=rag)
    r = svc.ask(course_id, "q1")
    cid = r["conversation_id"]
    for i in range(2, 10):  # 再问 8 轮，共 9 轮 = 18 条
        svc.ask(course_id, f"q{i}", conversation_id=cid)
    # 第 10 轮时 history 应 ≤ 6
    assert len(rag.last_history) <= 6


# ----- ConversationService CRUD -----

def test_conversation_service_crud(course_id):
    svc = ConversationService()
    conv = svc.create(course_id, title="测试会话")
    assert conv.id
    assert svc.get(conv.id).title == "测试会话"

    # list_by_course
    assert any(c.id == conv.id for c in svc.list_by_course(course_id))

    # rename
    renamed = svc.rename(conv.id, "新名字")
    assert renamed.title == "新名字"

    # delete（含消息）
    ChatService(rag_engine=FakeRag()).ask(course_id, "x", conversation_id=conv.id)
    assert len(svc.messages(conv.id)) == 2
    n = svc.delete(conv.id)
    assert n == 2
    assert svc.get(conv.id) is None


# ----- 旧数据迁移 -----

def test_migrate_groups_old_messages(course_id, db_engine):
    """无 conversation_id 的旧消息按 (course, scope, course_ids) 分组迁成会话。"""
    import backend.database as dbmod
    with Session(db_engine) as s:
        # 课程问答旧消息（无 conversation_id）
        s.add(ChatMessage(course_id=course_id, role="user", content="旧问1", scope="course"))
        s.add(ChatMessage(course_id=course_id, role="assistant", content="旧答1", scope="course"))
        s.commit()
    # 跑迁移
    dbmod._migrate_conversations()
    convs = ConversationService().list_by_course(course_id)
    assert len(convs) == 1
    assert convs[0].title == "旧问1"  # 首条 user 作标题
    msgs = ConversationService().messages(convs[0].id)
    assert len(msgs) == 2
    # 迁移幂等：再跑不重复
    dbmod._migrate_conversations()
    assert len(ConversationService().list_by_course(course_id)) == 1


def test_migrate_separates_different_context(course_id, db_engine):
    """不同上下文（course vs set）的旧消息迁成不同会话。"""
    import backend.database as dbmod
    with Session(db_engine) as s:
        s.add(ChatMessage(course_id=course_id, role="user", content="课程问", scope="course"))
        s.add(ChatMessage(course_id=course_id, role="assistant", content="课程答", scope="course"))
        s.add(ChatMessage(course_id=course_id, role="user", content="集问", scope="set", course_ids=json.dumps([1, 2])))
        s.add(ChatMessage(course_id=course_id, role="assistant", content="集答", scope="set", course_ids=json.dumps([1, 2])))
        s.commit()
    dbmod._migrate_conversations()
    convs = ConversationService().list_by_course(course_id)
    assert len(convs) == 2  # course 与 set 分开
