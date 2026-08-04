"""章节速览测试。"""

import pytest
from sqlmodel import Session, SQLModel, create_engine

from backend.models import Chapter, Course, Transcript
from backend.services.chapter_service import ChapterService, _extract_json_array


class FakeLLM:
    def chat(self, system_prompt: str, user_prompt: str, max_tokens: int = 1200) -> str:
        # 返回每章标题/速览 JSON
        import re
        idxs = re.findall(r"第(\d+)章", user_prompt)
        items = [{"index": int(i), "title": f"标题{i}", "summary": f"速览{i}"} for i in idxs]
        import json
        return json.dumps(items, ensure_ascii=False)


@pytest.fixture
def db_engine(tmp_path):
    eng = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    SQLModel.metadata.create_all(eng)
    return eng


@pytest.fixture
def course_id(db_engine):
    with Session(db_engine) as s:
        c = Course(title="ch", video_path="/tmp/ch.mp4", status="completed")
        s.add(c); s.commit(); s.refresh(c)
        cid = c.id
        # 0-600s 字幕，每 30s 一条
        for t in range(0, 600, 30):
            s.add(Transcript(course_id=cid, text=f"内容{t}", start_time=float(t), end_time=t + 5))
        s.commit()
    return cid


@pytest.fixture(autouse=True)
def _patch_engine(db_engine, monkeypatch):
    import backend.services.chapter_service as cs
    monkeypatch.setattr(cs, "engine", db_engine)


def test_extract_json_array_handles_fences():
    text = '```json\n[{"a":1}]\n```'
    assert _extract_json_array(text) == [{"a": 1}]


def test_extract_json_array_handles_brackets_in_strings():
    text = '[{"x":"包含[括号]的文本"}]'
    assert _extract_json_array(text)[0]["x"] == "包含[括号]的文本"


def test_split_by_window(course_id, db_engine):
    svc = ChapterService(llm=FakeLLM())
    with Session(db_engine) as s:
        ts = list(s.exec(__import__("sqlmodel").select(__import__("backend.models", fromlist=["Transcript"]).Transcript)).all())
    chapters = svc._split(ts)
    assert 3 <= len(chapters) <= 12
    # 章节时间连续覆盖
    assert chapters[0]["start"] == 0
    for i in range(1, len(chapters)):
        assert chapters[i]["start"] >= chapters[i - 1]["start"]


def test_generate_creates_and_persists(course_id, db_engine):
    svc = ChapterService(llm=FakeLLM())
    rows = svc.generate(course_id)
    assert len(rows) >= 3
    assert all(r.title.startswith("标题") for r in rows)
    # 已存库
    with Session(db_engine) as s:
        stored = list(s.exec(__import__("sqlmodel").select(Chapter)).all())
    assert len(stored) == len(rows)


def test_list_chapters_caches(course_id, db_engine):
    svc = ChapterService(llm=FakeLLM())
    first = svc.list_chapters(course_id)
    # 第二次应直接读库（不再生成）
    second = svc.list_chapters(course_id)
    assert [c.id for c in first] == [c.id for c in second]


def test_regenerate_replaces_old(course_id, db_engine):
    svc = ChapterService(llm=FakeLLM())
    svc.generate(course_id)
    svc.generate(course_id)  # 重新生成
    with Session(db_engine) as s:
        stored = list(s.exec(__import__("sqlmodel").select(Chapter)).all())
    # 不应翻倍
    assert len(stored) <= 12


def test_empty_transcripts_returns_empty(db_engine):
    with Session(db_engine) as s:
        c = Course(title="e", video_path="/tmp/e.mp4", status="completed")
        s.add(c); s.commit(); s.refresh(c)
        cid = c.id
    svc = ChapterService(llm=FakeLLM())
    assert svc.list_chapters(cid) == []
