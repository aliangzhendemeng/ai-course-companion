"""时间段总结测试。"""

import pytest
from sqlmodel import Session, SQLModel, create_engine

from backend.models import Course, Frame, Transcript
from backend.services.segment_service import SegmentSummaryService


class FakeLLM:
    def __init__(self):
        self.last_prompt = ""

    def chat(self, system_prompt: str, user_prompt: str, max_tokens: int = 800) -> str:
        self.last_prompt = user_prompt
        return "这是该段的要点总结。"


@pytest.fixture
def db_engine(tmp_path):
    eng = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    SQLModel.metadata.create_all(eng)
    return eng


@pytest.fixture
def course_id(db_engine):
    with Session(db_engine) as s:
        c = Course(title="seg", video_path="/tmp/seg.mp4", status="completed")
        s.add(c); s.commit(); s.refresh(c)
        cid = c.id
        # 字幕：0-300s 分布
        for i, t in enumerate(range(0, 300, 30)):
            s.add(Transcript(course_id=cid, text=f"内容{t}", start_time=float(t), end_time=t + 5))
        s.add(Frame(course_id=cid, timestamp=100.0, image_path="frame.png", ocr_text="课件A"))
        s.commit()
    return cid


@pytest.fixture(autouse=True)
def _patch_engine(db_engine, monkeypatch):
    """让 SegmentSummaryService 用测试库。"""
    import backend.services.segment_service as ss
    monkeypatch.setattr(ss, "engine", db_engine)


def test_summarize_filters_range(db_engine, course_id):
    llm = FakeLLM()
    with Session(db_engine) as _:
        pass
    svc = SegmentSummaryService(llm=llm)
    result = svc.summarize(course_id, start=60, end=120)
    assert "要点总结" in result["summary"]
    assert result["segment_count"] >= 1
    # 范围内字幕（60,90,120）应进入上下文，0/30 不应
    assert "内容60" in llm.last_prompt
    assert "内容90" in llm.last_prompt
    assert "内容0" not in llm.last_prompt
    assert "课件A" in llm.last_prompt  # frame@100 在范围内


def test_summarize_empty_range_raises(db_engine, course_id):
    svc = SegmentSummaryService(llm=FakeLLM())
    with pytest.raises(ValueError, match="没有字幕"):
        svc.summarize(course_id, start=10000, end=10060)


def test_summarize_invalid_range(db_engine, course_id):
    svc = SegmentSummaryService(llm=FakeLLM())
    with pytest.raises(ValueError, match="非法"):
        svc.summarize(course_id, start=100, end=100)
    with pytest.raises(ValueError, match="非法"):
        svc.summarize(course_id, start=-1, end=10)


def test_summarize_too_long(db_engine, course_id):
    svc = SegmentSummaryService(llm=FakeLLM())
    with pytest.raises(ValueError, match="过长"):
        svc.summarize(course_id, start=0, end=60 * 60)  # 1 小时


def test_summarize_missing_course(db_engine):
    svc = SegmentSummaryService(llm=FakeLLM())
    with pytest.raises(ValueError, match="课程不存在"):
        svc.summarize(9999, start=0, end=10)
