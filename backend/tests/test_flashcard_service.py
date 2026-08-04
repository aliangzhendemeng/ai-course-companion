"""FlashcardService 单元测试：生成、三档熟悉度标记、SM-2 间隔重复、统计、清空。"""

import json
from datetime import datetime, timedelta, timezone

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from backend.models import Course, Flashcard, Transcript
from backend.services.flashcard_service import FlashcardService


@pytest.fixture
def db_engine(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
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
        )
        session.add(course)
        session.commit()
        session.refresh(course)
        session.add(Transcript(course_id=course.id, text="过拟合是模型在训练集上表现好但泛化差。", start_time=0.0, end_time=5.0))
        session.commit()
        return course.id


class FakeLLM:
    def chat(self, system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> str:
        return json.dumps(
            [
                {"front": "什么是过拟合？", "back": "模型在训练集上表现好但泛化差"},
                {"front": "什么是正则化？", "back": "防止过拟合的技术"},
            ],
            ensure_ascii=False,
        )

    @property
    def model_identifier(self) -> str:
        return "fake"


@pytest.fixture
def flashcard_service(db_engine, monkeypatch):
    monkeypatch.setattr("backend.services.flashcard_service.engine", db_engine)
    monkeypatch.setattr("backend.services.quiz_service.engine", db_engine)
    return lambda: FlashcardService(session=Session(db_engine), llm=FakeLLM())


def _cards(db_engine) -> list[Flashcard]:
    with Session(db_engine) as session:
        return list(session.exec(select(Flashcard).order_by(Flashcard.id)).all())


def _make_card(db_engine, course_id, due_date=None) -> int:
    with Session(db_engine) as session:
        c = Flashcard(course_id=course_id, front="f", back="b", familiarity="unknown")
        if due_date is not None:
            c.due_date = due_date
        session.add(c); session.commit(); session.refresh(c)
        return c.id


def test_generate_creates_cards(flashcard_service, db_engine, sample_course):
    generated, total = flashcard_service().generate(course_id=sample_course, count=2)
    assert generated == 2
    assert total == 2
    cards = _cards(db_engine)
    assert cards[0].front == "什么是过拟合？"
    assert cards[0].familiarity == "unknown"  # 默认不认识


def test_generate_appends(flashcard_service, db_engine, sample_course):
    service = flashcard_service()
    service.generate(course_id=sample_course, count=2)
    generated, total = service.generate(course_id=sample_course, count=2)
    assert total == 4


def test_set_familiarity_three_levels(flashcard_service, db_engine, sample_course):
    service = flashcard_service()
    service.generate(course_id=sample_course, count=2)
    cards = _cards(db_engine)

    service.set_familiarity(cards[0].id, "known")
    service.set_familiarity(cards[1].id, "fuzzy")

    updated = _cards(db_engine)
    assert updated[0].familiarity == "known"
    assert updated[1].familiarity == "fuzzy"


def test_set_familiarity_invalid_raises(flashcard_service, db_engine, sample_course):
    service = flashcard_service()
    service.generate(course_id=sample_course, count=2)
    card = _cards(db_engine)[0]
    with pytest.raises(ValueError, match="非法熟悉度"):
        service.set_familiarity(card.id, "mastered")


def test_stats_counts(flashcard_service, db_engine, sample_course):
    service = flashcard_service()
    service.generate(course_id=sample_course, count=2)
    cards = _cards(db_engine)
    service.set_familiarity(cards[0].id, "known")
    # cards[1] 保持 unknown

    stats = service.stats(course_id=sample_course)
    assert stats == {"total": 2, "known": 1, "fuzzy": 0, "unknown": 1}


def test_clear(flashcard_service, db_engine, sample_course):
    service = flashcard_service()
    service.generate(course_id=sample_course, count=2)
    n = service.clear(course_id=sample_course)
    assert n == 2
    assert _cards(db_engine) == []


# ----- SM-2 间隔重复 -----

def test_review_quality5_progression(flashcard_service, db_engine, sample_course):
    """连续答对(quality=5)：间隔按 1→6→round(6*ease) 增长。"""
    svc = flashcard_service()
    cid = _make_card(db_engine, sample_course)
    c = svc.review(cid, 5)
    assert c.repetitions == 1 and c.interval_days == 1
    c = svc.review(cid, 5)
    assert c.repetitions == 2 and c.interval_days == 6
    ease_at_3rd = c.ease  # 第三次 interval 用此 ease 计算（标准 SM-2 先算 interval 再更新 ease）
    c = svc.review(cid, 5)
    assert c.repetitions == 3 and c.interval_days == round(6 * ease_at_3rd)


def test_review_below3_resets(flashcard_service, db_engine, sample_course):
    """quality<3 视为答错：连续次数归零、间隔=1。"""
    svc = flashcard_service()
    cid = _make_card(db_engine, sample_course)
    svc.review(cid, 5)
    svc.review(cid, 5)  # reps=2, interval=6
    c = svc.review(cid, 2)  # 答错
    assert c.repetitions == 0
    assert c.interval_days == 1


def test_review_familiarity_mapping(flashcard_service, db_engine, sample_course):
    svc = flashcard_service()
    cid = _make_card(db_engine, sample_course)
    assert svc.review(cid, 2).familiarity == "unknown"
    assert svc.review(cid, 3).familiarity == "fuzzy"
    assert svc.review(cid, 5).familiarity == "known"


def test_review_due_date_advances(flashcard_service, db_engine, sample_course):
    svc = flashcard_service()
    cid = _make_card(db_engine, sample_course)
    before = datetime.utcnow()  # SQLite 读回 naive，用 naive 比较
    c = svc.review(cid, 5)  # interval=1
    after = datetime.utcnow()
    due = c.due_date
    assert before + timedelta(days=1) <= due <= after + timedelta(days=1) + timedelta(seconds=5)
    assert c.last_reviewed_at is not None


def test_review_invalid_quality(flashcard_service, db_engine, sample_course):
    svc = flashcard_service()
    cid = _make_card(db_engine, sample_course)
    with pytest.raises(ValueError, match="非法 quality"):
        svc.review(cid, 7)


def test_due_queue(flashcard_service, db_engine, sample_course):
    """due_queue 只返回 due_date<=now 的卡。"""
    svc = flashcard_service()
    now = datetime.utcnow()
    _make_card(db_engine, sample_course, due_date=now - timedelta(hours=1))  # 已到期
    _make_card(db_engine, sample_course, due_date=now + timedelta(days=3))   # 未到期
    due = svc.due_queue(course_id=sample_course)
    assert len(due) == 1
    assert due[0].due_date <= now


def test_due_count(flashcard_service, db_engine, sample_course):
    svc = flashcard_service()
    now = datetime.utcnow()
    _make_card(db_engine, sample_course, due_date=now - timedelta(hours=1))
    _make_card(db_engine, sample_course, due_date=now - timedelta(hours=2))
    assert svc.due_count(course_id=sample_course) == 2
