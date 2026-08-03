"""学习 streak 统计测试：模块 + 端到端。"""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from backend.main import app
from backend.models import ChatMessage, Course, Flashcard, Note, Question, QuestionAttempt
from backend.services.study_stats_service import StudyStatsService


@pytest.fixture
def db_engine(tmp_path):
    eng = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    SQLModel.metadata.create_all(eng)
    return eng


@pytest.fixture
def session(db_engine):
    with Session(db_engine) as s:
        yield s


def _utc(days_ago: int) -> datetime:
    """N 天前（UTC）。"""
    return datetime.now(timezone.utc) - timedelta(days=days_ago)


def _add_activity(session, days_ago: int):
    """在 N 天前插入一条问答活动。"""
    _add_activity.seq += 1
    c = Course(title=f"t{_add_activity.seq}", video_path=f"/tmp/x{_add_activity.seq}", status="completed")
    session.add(c)
    session.commit()
    session.refresh(c)
    session.add(ChatMessage(course_id=c.id, role="user", content="q", created_at=_utc(days_ago)))
    session.commit()


_add_activity.seq = 0


def test_empty_returns_zero(session):
    s = StudyStatsService(session=session).stats()
    assert s["streak"] == 0
    assert s["total_days"] == 0
    assert s["today_active"] is False
    assert s["recent"] == []


def test_today_counts_as_active(session):
    _add_activity(session, 0)
    s = StudyStatsService(session=session).stats()
    assert s["today_active"] is True
    assert s["streak"] >= 1
    assert s["total_days"] == 1


def test_consecutive_streak(session):
    """今天+昨天+前天连续 -> streak=3。"""
    for d in (2, 1, 0):
        _add_activity(session, d)
    s = StudyStatsService(session=session).stats()
    assert s["streak"] == 3
    assert s["total_days"] == 3


def test_gap_breaks_streak(session):
    """前天有、昨天没有、今天有 -> streak=1（昨天断了）。"""
    _add_activity(session, 2)
    _add_activity(session, 0)
    s = StudyStatsService(session=session).stats()
    assert s["streak"] == 1


def test_grace_day_keeps_streak(session):
    """昨天起连续、今天还没学 -> 仍算昨天的 streak（一天宽限）。"""
    _add_activity(session, 1)
    _add_activity(session, 2)
    s = StudyStatsService(session=session).stats()
    assert s["today_active"] is False
    assert s["streak"] == 2  # 昨天起算，未因今天没学而清零


def test_multiple_activity_types_one_day(session):
    """同一天多种学习行为只算一天。"""
    c = Course(title="t", video_path="/tmp/x", status="completed")
    session.add(c); session.commit(); session.refresh(c)
    q = Question(course_id=c.id, type="judge", question="q", answer="正确")
    session.add(q); session.commit(); session.refresh(q)
    now = datetime.now(timezone.utc)
    session.add(ChatMessage(course_id=c.id, role="user", content="q", created_at=now))
    session.add(Note(course_id=c.id, kind="note", content="n", timestamp=0, created_at=now))
    session.add(Flashcard(course_id=c.id, front="f", back="b", familiarity="known", created_at=now))
    session.add(QuestionAttempt(question_id=q.id, answer="正确", correct=True, created_at=now))
    session.commit()
    s = StudyStatsService(session=session).stats()
    assert s["total_days"] == 1


def test_recent_window(session):
    """recent 只含最近 30 天。"""
    _add_activity(session, 0)
    _add_activity(session, 40)  # 超出窗口
    s = StudyStatsService(session=session).stats()
    assert any(d for d in s["recent"])
    assert len(s["recent"]) == 1  # 40 天前的不算


# ----- 端到端 -----

def test_api_study_stats(db_engine):
    import backend.database as dbmod
    import backend.services.study_stats_service as sss
    dbmod.engine = db_engine
    sss.engine = db_engine
    with Session(db_engine) as s:
        c = Course(title="t", video_path="/tmp/x", status="completed")
        s.add(c); s.commit(); s.refresh(c)
        s.add(ChatMessage(course_id=c.id, role="user", content="q", created_at=datetime.now(timezone.utc)))
        s.commit()
    with TestClient(app) as client:
        r = client.get("/api/study-stats")
    assert r.status_code == 200
    data = r.json()
    assert data["today_active"] is True
    assert data["streak"] >= 1
    assert isinstance(data["recent"], list)
