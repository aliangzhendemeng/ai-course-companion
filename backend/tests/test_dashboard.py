"""掌握度仪表盘测试：模块 + 端到端。"""

import json

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from backend.main import app
from backend.models import Course, Flashcard, Note, Question, QuestionAttempt
from backend.services.dashboard_service import DashboardService


@pytest.fixture
def db_engine(tmp_path):
    eng = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    SQLModel.metadata.create_all(eng)
    return eng


@pytest.fixture
def session(db_engine):
    with Session(db_engine) as s:
        yield s


def _seed(session):
    c = Course(title="t", video_path="/tmp/dash.mp4", status="completed")
    session.add(c); session.commit(); session.refresh(c)
    # 闪卡：2 known, 1 fuzzy, 1 unknown
    for fam, n in (("known", 2), ("fuzzy", 1), ("unknown", 1)):
        for i in range(n):
            session.add(Flashcard(course_id=c.id, front=f"f{fam}{i}", back="b", familiarity=fam))
    # 测验作答：3 对 1 错
    q = Question(course_id=c.id, type="judge", question="q", answer="正确")
    session.add(q); session.commit(); session.refresh(q)
    session.add(QuestionAttempt(question_id=q.id, answer="正确", correct=True))
    session.add(QuestionAttempt(question_id=q.id, answer="正确", correct=True))
    session.add(QuestionAttempt(question_id=q.id, answer="正确", correct=True))
    session.add(QuestionAttempt(question_id=q.id, answer="错误", correct=False))
    # 笔记 2
    session.add(Note(course_id=c.id, kind="note", content="n1", timestamp=0))
    session.add(Note(course_id=c.id, kind="bookmark", content="", timestamp=1))
    session.commit()
    return c.id


def test_dashboard_aggregation(session):
    _seed(session)
    d = DashboardService(session=session).dashboard()
    assert d["quiz"]["total_attempts"] == 4
    assert d["quiz"]["correct"] == 3
    assert d["quiz"]["accuracy"] == 0.75
    assert d["flashcards"]["total"] == 4
    assert d["flashcards"]["known"] == 2
    assert d["flashcards"]["fuzzy"] == 1
    assert d["flashcards"]["unknown"] == 1
    assert d["wrong"]["total"] == 1  # 1 道题曾答错
    assert d["wrong"]["unmastered"] == 1  # 仅答错未连对
    assert d["notes"] == 2
    assert d["courses_completed"] == 1


def test_dashboard_empty(session):
    d = DashboardService(session=session).dashboard()
    assert d["quiz"]["total_attempts"] == 0
    assert d["quiz"]["accuracy"] == 0.0
    assert d["flashcards"]["total"] == 0
    assert d["wrong"]["total"] == 0


def test_api_dashboard(db_engine):
    import backend.database as dbmod
    import backend.services.dashboard_service as ds
    dbmod.engine = db_engine
    ds.engine = db_engine
    with Session(db_engine) as s:
        _seed(s)
    with TestClient(app) as client:
        r = client.get("/api/dashboard")
    assert r.status_code == 200
    data = r.json()
    assert data["quiz"]["total_attempts"] == 4
    assert data["flashcards"]["known"] == 2
    assert data["courses_completed"] == 1
