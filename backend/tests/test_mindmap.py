"""思维导图服务测试。"""

import json

import pytest
from sqlmodel import Session, SQLModel, create_engine

from backend.models import Course, MindMap, Transcript
from backend.services.mindmap_service import (
    MindMapService,
    _extract_json_object,
    _normalize_tree,
)


class FakeLLM:
    def chat(self, system_prompt: str, user_prompt: str, max_tokens: int = 1200) -> str:
        return json.dumps(
            {
                "title": "机器学习",
                "children": [
                    {"title": "监督学习", "children": [{"title": "分类"}, {"title": "回归"}]},
                    {"title": "无监督学习", "children": [{"title": "聚类"}]},
                ],
            },
            ensure_ascii=False,
        )


@pytest.fixture
def db_engine(tmp_path):
    eng = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    SQLModel.metadata.create_all(eng)
    return eng


@pytest.fixture
def course_id(db_engine):
    with Session(db_engine) as s:
        c = Course(title="导图测试", video_path="/tmp/m.mp4", status="completed")
        s.add(c); s.commit(); s.refresh(c)
        cid = c.id
        s.add(Transcript(course_id=cid, text="机器学习包括监督学习和无监督学习。", start_time=0, end_time=5))
        s.commit()
    return cid


@pytest.fixture(autouse=True)
def _patch_engine(db_engine, monkeypatch):
    import backend.services.mindmap_service as ms
    import backend.services.quiz_service as qs
    monkeypatch.setattr(ms, "engine", db_engine)
    monkeypatch.setattr(qs, "engine", db_engine)


def test_extract_json_object_handles_fences():
    text = '```json\n{"a":{"b":1}}\n```'
    assert _extract_json_object(text) == {"a": {"b": 1}}


def test_extract_json_object_braces_in_strings():
    text = '{"x":"含}括号"}'
    assert _extract_json_object(text)["x"] == "含}括号"


def test_normalize_tree_limits_depth_and_width():
    deep = {
        "title": "r",
        "children": [
            {"title": f"b{i}", "children": [{"title": "leaf"}]} for i in range(10)
        ],
    }
    out = _normalize_tree(deep, max_depth=2)
    assert len(out["children"]) <= 6  # 限宽
    # depth=2 时子节点不应再有 children
    assert "children" not in out["children"][0]


def test_generate_returns_tree_and_persists(course_id, db_engine):
    svc = MindMapService(llm=FakeLLM())
    tree = svc.generate(course_id)
    assert tree["title"] == "机器学习"
    assert len(tree["children"]) == 2
    assert tree["children"][0]["title"] == "监督学习"
    with Session(db_engine) as s:
        stored = list(s.exec(__import__("sqlmodel").select(MindMap)).all())
    assert len(stored) == 1
    assert json.loads(stored[0].tree)["title"] == "机器学习"


def test_get_or_generate_caches(course_id):
    svc = MindMapService(llm=FakeLLM())
    first = svc.get_or_generate(course_id)
    second = svc.get_or_generate(course_id)
    assert first == second  # 第二次读缓存


def test_regenerate_replaces_old(course_id, db_engine):
    svc = MindMapService(llm=FakeLLM())
    svc.generate(course_id)
    svc.generate(course_id)
    with Session(db_engine) as s:
        stored = list(s.exec(__import__("sqlmodel").select(MindMap)).all())
    assert len(stored) == 1  # 不重复


def test_missing_course_raises(db_engine):
    svc = MindMapService(llm=FakeLLM())
    with pytest.raises(ValueError, match="课程不存在"):
        svc.generate(9999)
