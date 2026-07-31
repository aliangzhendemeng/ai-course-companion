"""NoteService 单元测试：笔记/书签的增删改查与排序。"""

import pytest
from sqlmodel import Session, SQLModel, create_engine

from backend.models import Course
from backend.services.note_service import NoteService


@pytest.fixture
def db_engine(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(db_engine):
    with Session(db_engine) as s:
        yield s


@pytest.fixture
def course_id(session):
    course = Course(title="测试课程", video_path="/tmp/test.mp4", status="completed", progress_percent=100)
    session.add(course)
    session.commit()
    session.refresh(course)
    return course.id


def test_create_note(session, course_id):
    svc = NoteService(session=session)
    note = svc.create(course_id=course_id, kind="note", content="这里讲了过拟合", timestamp=12.5)
    assert note.id is not None
    assert note.kind == "note"
    assert note.content == "这里讲了过拟合"
    assert note.timestamp == 12.5


def test_create_bookmark_allows_empty_content(session, course_id):
    svc = NoteService(session=session)
    bm = svc.create(course_id=course_id, kind="bookmark", content="", timestamp=30.0)
    assert bm.kind == "bookmark"
    assert bm.content == ""


def test_create_note_requires_content(session, course_id):
    svc = NoteService(session=session)
    with pytest.raises(ValueError, match="不能为空"):
        svc.create(course_id=course_id, kind="note", content="   ", timestamp=0)


def test_create_invalid_kind(session, course_id):
    svc = NoteService(session=session)
    with pytest.raises(ValueError, match="非法类型"):
        svc.create(course_id=course_id, kind="highlight", content="x")


def test_create_negative_timestamp(session, course_id):
    svc = NoteService(session=session)
    with pytest.raises(ValueError, match="不能为负"):
        svc.create(course_id=course_id, kind="bookmark", timestamp=-1)


def test_create_missing_course(session):
    svc = NoteService(session=session)
    with pytest.raises(ValueError, match="课程不存在"):
        svc.create(course_id=9999, kind="note", content="x")


def test_list_notes_ordered_by_timestamp(session, course_id):
    svc = NoteService(session=session)
    svc.create(course_id=course_id, kind="note", content="后面", timestamp=100.0)
    svc.create(course_id=course_id, kind="bookmark", content="", timestamp=5.0)
    svc.create(course_id=course_id, kind="note", content="中间", timestamp=50.0)
    notes = svc.list_notes(course_id)
    assert [n.timestamp for n in notes] == [5.0, 50.0, 100.0]
    assert [n.content for n in notes] == ["", "中间", "后面"]


def test_list_notes_scoped_to_course(session, course_id):
    other = Course(title="另一门", video_path="/tmp/o.mp4", status="completed", progress_percent=100)
    session.add(other)
    session.commit()
    session.refresh(other)
    svc = NoteService(session=session)
    svc.create(course_id=course_id, kind="note", content="本课", timestamp=1.0)
    svc.create(course_id=other.id, kind="note", content="别课", timestamp=1.0)
    notes = svc.list_notes(course_id)
    assert len(notes) == 1
    assert notes[0].content == "本课"


def test_update_note(session, course_id):
    svc = NoteService(session=session)
    note = svc.create(course_id=course_id, kind="note", content="旧内容", timestamp=1.0)
    updated = svc.update(note.id, "新内容")
    assert updated.content == "新内容"
    assert updated.updated_at >= updated.created_at


def test_update_requires_content(session, course_id):
    svc = NoteService(session=session)
    note = svc.create(course_id=course_id, kind="note", content="旧", timestamp=1.0)
    with pytest.raises(ValueError, match="不能为空"):
        svc.update(note.id, "  ")


def test_update_missing(session):
    svc = NoteService(session=session)
    with pytest.raises(ValueError, match="不存在"):
        svc.update(9999, "x")


def test_delete_note(session, course_id):
    svc = NoteService(session=session)
    note = svc.create(course_id=course_id, kind="note", content="x", timestamp=1.0)
    svc.delete(note.id)
    assert svc.list_notes(course_id) == []


def test_delete_missing(session):
    svc = NoteService(session=session)
    with pytest.raises(ValueError, match="不存在"):
        svc.delete(9999)
