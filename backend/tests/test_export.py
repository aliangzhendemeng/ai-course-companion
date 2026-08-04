"""导出服务测试：模块（格式正确性）+ 端到端（API 下载）。"""

import json
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from backend.api.export import _attachment  # noqa: F401  (确保模块可导入)
from backend.main import app
from backend.models import Course, Flashcard, Question, QuestionAttempt
from backend.services.export_service import ExportService


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
    c = Course(title="导出测试课", video_path="/tmp/e.mp4", status="completed", progress_percent=100)
    session.add(c)
    session.commit()
    session.refresh(c)
    return c.id


@pytest.fixture
def seeded(session, course_id):
    """造 3 张闪卡（不同熟悉度）+ 1 道错题（未掌握）+ 1 道（已掌握）。"""
    session.add(Flashcard(course_id=course_id, front="什么是过拟合", back="训练集好泛化差", familiarity="unknown"))
    session.add(Flashcard(course_id=course_id, front="什么是正则化", back="防过拟合", familiarity="fuzzy"))
    session.add(Flashcard(course_id=course_id, front="什么是梯度", back="方向导数", familiarity="known"))

    q1 = Question(course_id=course_id, type="choice", question="下列哪个是过拟合表现?",
                  options=json.dumps(["训练集差", "泛化好", "训练好泛化差", "都差"]), answer="C",
                  explanation="过拟合指训练集表现好但泛化差", source_timestamp=120.0)
    q2 = Question(course_id=course_id, type="judge", question="正则化能完全消除过拟合", answer="错误",
                  explanation="只能缓解", source_timestamp=200.0)
    session.add(q1)
    session.add(q2)
    session.commit()
    session.refresh(q1)
    session.refresh(q2)
    now = datetime.now(timezone.utc)
    # q1：答错 -> 未掌握
    session.add(QuestionAttempt(question_id=q1.id, answer="A", correct=False, created_at=now))
    # q2：答错后连对2次 -> 已掌握
    session.add(QuestionAttempt(question_id=q2.id, answer="正确", correct=False, created_at=now))
    session.add(QuestionAttempt(question_id=q2.id, answer="错误", correct=True, created_at=now))
    session.add(QuestionAttempt(question_id=q2.id, answer="错误", correct=True, created_at=now))
    session.commit()
    return course_id


# ----- 模块测试 -----

def test_flashcards_md_groups_by_familiarity(session, seeded):
    md = ExportService(session=session).export_flashcards(course_id=seeded, fmt="md")
    assert "闪卡导出" in md
    assert "✗ 不认识" in md and "~ 模糊" in md and "✓ 认识" in md
    assert "什么是过拟合" in md


def test_flashcards_anki_tsv_format(session, seeded):
    tsv = ExportService(session=session).export_flashcards(course_id=seeded, fmt="anki")
    lines = [l for l in tsv.split("\n") if l]
    assert len(lines) == 3
    for line in lines:
        assert line.count("\t") == 1  # 正面<TAB>背面
    assert "什么是过拟合\t训练集好泛化差" in tsv


def test_flashcards_anki_escapes_newlines(db_engine):
    """含换行的卡片内容应转为 <br>，避免破坏 TSV 行结构。"""
    with Session(db_engine) as s:
        c = Course(title="t", video_path="/tmp/x", status="completed")
        s.add(c); s.commit(); s.refresh(c)
        s.add(Flashcard(course_id=c.id, front="多行\n问题", back="答案\n第二行", familiarity="known"))
        s.commit()
        tsv = ExportService(session=s).export_flashcards(course_id=c.id, fmt="anki")
    assert "\n" not in tsv
    assert "<br>" in tsv


def test_wrong_questions_md(session, seeded):
    md = ExportService(session=session).export_wrong_questions(course_id=seeded)
    assert "错题本导出" in md
    assert "未掌握" in md and "已掌握" in md
    # 选择题选项标注正确答案 C
    assert "✓ C" in md
    assert "正确答案：** C" in md or "正确答案：** C" in md
    assert "错 1 次" in md  # q1 错1次
    assert "错 1 次" in md  # q2 也错1次（虽已掌握）


def test_invalid_format_raises(session, seeded):
    with pytest.raises(ValueError):
        ExportService(session=session).export_flashcards(course_id=seeded, fmt="pdf")


# ----- 端到端（API 下载） -----

@pytest.fixture
def client(db_engine, seeded):
    """用注入的测试库启动 app（不走真实 data/app.db）。"""
    import backend.database as dbmod
    import backend.services.export_service as esvc
    import backend.services.flashcard_service as fs
    import backend.services.quiz_service as qs

    orig_engine = dbmod.engine
    dbmod.engine = db_engine
    # 让各 service 用测试库
    for mod in (esvc, fs, qs):
        mod.engine = db_engine
    with TestClient(app) as c:
        yield c
    dbmod.engine = orig_engine


def test_api_export_flashcards_md(client, course_id):
    r = client.get(f"/api/export/flashcards?course_id={course_id}&fmt=md")
    assert r.status_code == 200
    assert "text/markdown" in r.headers["content-type"]
    assert "attachment" in r.headers["content-disposition"]
    assert "闪卡导出" in r.text


def test_api_export_flashcards_anki(client, course_id):
    r = client.get(f"/api/export/flashcards?course_id={course_id}&fmt=anki")
    assert r.status_code == 200
    assert "tab-separated" in r.headers["content-type"]
    assert "什么是过拟合" in r.text


def test_api_export_wrong_questions(client, course_id):
    r = client.get(f"/api/export/wrong-questions?course_id={course_id}")
    assert r.status_code == 200
    assert "错题本导出" in r.text
    assert "未掌握" in r.text


def test_api_export_requires_scope(client):
    r = client.get("/api/export/flashcards")
    assert r.status_code == 400


def test_api_export_invalid_format(client, course_id):
    r = client.get(f"/api/export/flashcards?course_id={course_id}&fmt=pdf")
    assert r.status_code == 400
