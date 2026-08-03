"""学习周报测试：模块 + 端到端。"""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from backend.main import app
from backend.models import ChatMessage, Course, Flashcard, Note, Question, QuestionAttempt
from backend.services.weekly_report_service import WeeklyReportService


@pytest.fixture
def db_engine(tmp_path):
    eng = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    SQLModel.metadata.create_all(eng)
    return eng


@pytest.fixture
def session(db_engine):
    with Session(db_engine) as s:
        yield s


@pytest.fixture
def course_id(session):
    c = Course(title="周报课", video_path="/tmp/w.mp4", status="completed")
    session.add(c); session.commit(); session.refresh(c)
    return c.id


def _utc(days_ago: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=days_ago)


def _patch(monkeypatch, db_engine):
    import backend.services.weekly_report_service as wr
    import backend.services.study_stats_service as ss
    monkeypatch.setattr(wr, "engine", db_engine)
    monkeypatch.setattr(ss, "engine", db_engine)


def test_empty_report(session):
    s = WeeklyReportService(session=session).weekly()
    assert s["quiz"]["attempts"] == 0
    assert s["flashcards_generated"] == 0
    assert s["study_days"] == 0


def test_weekly_aggregation(session, course_id, monkeypatch, db_engine):
    _patch(monkeypatch, db_engine)
    q = Question(course_id=course_id, type="judge", question="q", answer="正确")
    session.add(q); session.commit(); session.refresh(q)
    # 最近 7 天内：3 对 1 错
    session.add(QuestionAttempt(question_id=q.id, answer="正确", correct=True, created_at=_utc(1)))
    session.add(QuestionAttempt(question_id=q.id, answer="正确", correct=True, created_at=_utc(2)))
    session.add(QuestionAttempt(question_id=q.id, answer="正确", correct=True, created_at=_utc(3)))
    session.add(QuestionAttempt(question_id=q.id, answer="错误", correct=False, created_at=_utc(4)))
    session.add(Flashcard(course_id=course_id, front="f", back="b", familiarity="known", created_at=_utc(2)))
    session.add(Note(course_id=course_id, kind="note", content="n", timestamp=0, created_at=_utc(1)))
    session.add(ChatMessage(course_id=course_id, role="user", content="q", created_at=_utc(1)))
    session.add(ChatMessage(course_id=course_id, role="assistant", content="a", created_at=_utc(1)))
    session.commit()

    s = WeeklyReportService(session=session).weekly()
    assert s["quiz"]["attempts"] == 4
    assert s["quiz"]["correct"] == 3
    assert s["quiz"]["accuracy"] == 0.75
    assert s["flashcards_generated"] == 1
    assert s["notes"] == 1
    assert s["questions"] == 2
    assert s["study_days"] >= 1


def test_excludes_old_data(session, course_id):
    q = Question(course_id=course_id, type="judge", question="q", answer="正确")
    session.add(q); session.commit(); session.refresh(q)
    # 10 天前的不计入
    session.add(QuestionAttempt(question_id=q.id, answer="错误", correct=False, created_at=_utc(10)))
    session.commit()
    s = WeeklyReportService(session=session).weekly()
    assert s["quiz"]["attempts"] == 0


def test_api_weekly_report(db_engine, monkeypatch):
    _patch(monkeypatch, db_engine)
    import backend.services.weekly_report_service as wr
    monkeypatch.setattr(wr, "engine", db_engine)
    with TestClient(app) as client:
        r = client.get("/api/weekly-report")
    assert r.status_code == 200
    data = r.json()
    assert data["window_days"] == 7
    assert "quiz" in data
