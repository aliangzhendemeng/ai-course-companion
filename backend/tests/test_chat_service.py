"""ChatService 单元测试。"""

from datetime import datetime

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from backend.models import ChatMessage, Course
from backend.services.chat_service import ChatService


@pytest.fixture
def db_engine(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def sample_course(db_engine):
    with Session(db_engine) as session:
        course = Course(
            title="测试课程",
            video_path="/tmp/test.mp4",
            status="completed",
            progress_percent=100,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(course)
        session.commit()
        session.refresh(course)
        return course.id  # 返回 id，避免 detach 后访问属性报错


class MockRAGEngine:
    def query(self, course_id: int, question: str, history=None) -> dict:
        return {
            "answer": f"课程回答：{question}",
            "sources": [{"type": "transcript", "timestamp": 12.0, "text": "测试字幕", "course_id": course_id}],
            "debug": {
                "model": "deepseek:deepseek-chat",
                "prompt": "system:\n...\nuser:\n...",
                "context": "测试上下文",
                "raw_answer": f"课程回答：{question}",
            },
        }

    def query_all(self, question: str, history=None) -> dict:
        return {
            "answer": f"全局回答：{question}",
            "sources": [{"type": "course_full_text", "timestamp": 0, "text": "课程全文", "course_id": 1}],
            "debug": {
                "model": "deepseek:deepseek-chat",
                "prompt": "global prompt",
                "context": "global context",
                "raw_answer": f"全局回答：{question}",
            },
        }

    def query_multiple(self, course_ids: list[int], question: str, history=None) -> dict:
        return {
            "answer": f"学习集回答：{question}",
            "sources": [
                {"type": "transcript", "timestamp": 5.0, "text": "集合字幕", "course_id": cid}
                for cid in course_ids
            ],
            "debug": {
                "model": "deepseek:deepseek-chat",
                "prompt": "multi prompt",
                "context": "multi context",
                "raw_answer": f"学习集回答：{question}",
            },
        }


@pytest.fixture
def chat_service(db_engine, sample_course, monkeypatch):
    monkeypatch.setattr("backend.services.chat_service.engine", db_engine)
    service = ChatService(rag_engine=MockRAGEngine())
    # 让 CourseService 也用测试库，否则 get_course 会读真实库
    from backend.services.course_service import CourseService
    service.course_service = CourseService(session=Session(db_engine))
    return service


def _messages(db_engine) -> list[ChatMessage]:
    with Session(db_engine) as session:
        return list(session.exec(select(ChatMessage).order_by(ChatMessage.created_at)).all())


class TestChatServiceAsk:
    def test_save_user_and_assistant_messages(self, chat_service: ChatService, db_engine, sample_course: int):
        result = chat_service.ask(sample_course, "什么是 AI？", scope="course")

        assert result["answer"] == "课程回答：什么是 AI？"
        assert result["answer_message_id"] is not None

        messages = _messages(db_engine)
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[0].content == "什么是 AI？"
        assert messages[0].scope == "course"
        assert messages[1].role == "assistant"
        assert messages[1].scope == "course"
        assert "测试字幕" in messages[1].sources
        assert "deepseek" in messages[1].debug_info

    def test_save_scope_all(self, chat_service: ChatService, db_engine, sample_course: int):
        chat_service.ask(sample_course, "总结所有课程", scope="all")

        assistant = [m for m in _messages(db_engine) if m.role == "assistant"][0]
        assert assistant.scope == "all"
        assert "全局回答" in assistant.content

    def test_course_not_completed_raises(self, chat_service: ChatService, db_engine, sample_course: int):
        with Session(db_engine) as session:
            course = session.get(Course, sample_course)
            course.status = "processing"
            session.add(course)
            session.commit()

        with pytest.raises(ValueError, match="课程尚未处理完成"):
            chat_service.ask(sample_course, "问题")

    def test_scope_set_saves_course_ids(self, chat_service: ChatService, db_engine, sample_course: int):
        """学习集问答：scope=set 且记录实际涉及的 course_ids。"""
        result = chat_service.ask(sample_course, "总结这几门课", scope="set", course_ids=[1, 2, 3])

        assert result["answer"] == "学习集回答：总结这几门课"
        assistant = [m for m in _messages(db_engine) if m.role == "assistant"][0]
        assert assistant.scope == "set"
        import json
        assert json.loads(assistant.course_ids) == [1, 2, 3]
