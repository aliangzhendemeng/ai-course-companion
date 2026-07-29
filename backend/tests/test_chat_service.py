"""ChatService 单元测试。"""

from datetime import datetime

import pytest
from sqlmodel import Session, SQLModel, create_engine

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
            id=1,
            title="测试课程",
            video_path="/tmp/test.mp4",
            status="completed",
            progress_percent=100,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(course)
        session.commit()
        return course


class MockRAGEngine:
    def query(self, course_id: int, question: str) -> dict:
        return {
            "answer": f"课程回答：{question}",
            "sources": [{"type": "transcript", "timestamp": 12.0, "text": "测试字幕"}],
            "debug": {
                "model": "deepseek:deepseek-chat",
                "prompt": "system:\n...\nuser:\n...",
                "context": "测试上下文",
                "raw_answer": f"课程回答：{question}",
            },
        }

    def query_all(self, question: str) -> dict:
        return {
            "answer": f"全局回答：{question}",
            "sources": [{"type": "course_full_text", "timestamp": 0, "text": "课程全文"}],
            "debug": {
                "model": "deepseek:deepseek-chat",
                "prompt": "global prompt",
                "context": "global context",
                "raw_answer": f"全局回答：{question}",
            },
        }


@pytest.fixture
def chat_service(db_engine, sample_course, monkeypatch):
    monkeypatch.setattr("backend.services.chat_service.engine", db_engine)
    return ChatService(rag_engine=MockRAGEngine())


class TestChatServiceAsk:
    def test_save_user_and_assistant_messages(self, chat_service: ChatService, sample_course: Course):
        result = chat_service.ask(sample_course.id, "什么是 AI？", scope="course")

        assert result["answer"] == "课程回答：什么是 AI？"
        assert result["answer_message_id"] is not None

        with Session(chat_service.rag_engine) as session:
            # 用正确的 engine 查询
            pass

        with Session(chat_service.rag_engine) as session:
            messages = session.query(ChatMessage).order_by(ChatMessage.created_at).all()
            assert len(messages) == 2
            assert messages[0].role == "user"
            assert messages[0].content == "什么是 AI？"
            assert messages[0].scope == "course"
            assert messages[1].role == "assistant"
            assert messages[1].scope == "course"
            assert "测试字幕" in messages[1].sources
            assert "deepseek" in messages[1].debug_info

    def test_save_scope_all(self, chat_service: ChatService, sample_course: Course):
        chat_service.ask(sample_course.id, "总结所有课程", scope="all")

        from sqlmodel import Session
        with Session(chat_service.rag_engine) as session:
            assistant = session.query(ChatMessage).filter(ChatMessage.role == "assistant").first()
            assert assistant is not None
            assert assistant.scope == "all"
            assert "全局回答" in assistant.content

    def test_course_not_completed_raises(self, chat_service: ChatService, sample_course: Course):
        sample_course.status = "processing"
        with pytest.raises(ValueError, match="课程尚未处理完成"):
            chat_service.ask(sample_course.id, "问题")
