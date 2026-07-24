"""RAG 引擎测试：混合检索与全局搜索。"""

import pytest

from backend.ai.rag_engine import RAGEngine
from backend.ai.llm.base import BaseLLM
from backend.config import settings


class FakeLLM(BaseLLM):
    """伪 LLM，记录调用参数并返回固定答案。"""

    def __init__(self, answer: str = "fake answer"):
        self.answer = answer

    def chat(self, system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> str:
        return self.answer


@pytest.fixture
def tmp_chroma_dir(tmp_path, monkeypatch):
    """使用临时 Chroma 目录，避免污染真实数据。"""
    chroma_dir = tmp_path / "chroma"
    bm25_dir = tmp_path / "bm25"
    monkeypatch.setattr(settings, "chroma_dir", str(chroma_dir))
    monkeypatch.setattr(settings, "bm25_dir", str(bm25_dir))
    return chroma_dir


def _make_transcript(course_id: int, text: str, start_time: float):
    return {
        "id": course_id * 1000 + int(start_time),
        "text": text,
        "start_time": start_time,
        "end_time": start_time + 1.0,
    }


def _make_frame(course_id: int, timestamp: float, ocr_text: str = "", vision_desc: str = ""):
    return {
        "id": course_id * 1000 + int(timestamp) + 500,
        "timestamp": timestamp,
        "ocr_text": ocr_text,
        "vision_desc": vision_desc,
    }


def test_rag_engine_index_and_query(tmp_chroma_dir):
    """基础索引与查询。"""
    engine = RAGEngine(llm=FakeLLM())

    transcripts = [
        {"text": "这是测试字幕", "start_time": 0.0, "end_time": 1.0, "id": 1},
    ]
    frames = [
        {"timestamp": 0.5, "ocr_text": "测试文字", "vision_desc": "测试画面", "id": 1},
    ]

    engine.index_course(1, transcripts, frames)
    result = engine.query(1, "测试")

    assert "answer" in result
    assert "sources" in result
    assert result["answer"] == "fake answer"
    assert len(result["sources"]) > 0


def test_hybrid_retrieval_with_bm25(tmp_chroma_dir):
    """混合检索应召回 BM25 更擅长的精确关键词文档。"""
    engine = RAGEngine(llm=FakeLLM())

    transcripts = [
        _make_transcript(1, "神经网络的前向传播算法", 0.0),
        _make_transcript(1, "反向传播用于更新权重", 5.0),
    ]
    frames = [
        _make_frame(1, 10.0, ocr_text="梯度下降公式"),
    ]

    engine.index_course(1, transcripts, frames)

    # 精确关键词 "反向传播" 应被召回
    result = engine.query(1, "反向传播")
    assert result["answer"] == "fake answer"
    sources_text = " ".join(s["text"] for s in result["sources"])
    assert "反向传播" in sources_text


def test_global_search_returns_multiple_courses(tmp_chroma_dir):
    """全局搜索应返回多个课程的来源。"""
    engine = RAGEngine(llm=FakeLLM())

    # 课程 1
    engine.index_course(1, [_make_transcript(1, "Python 列表推导式", 0.0)], [])
    # 课程 2
    engine.index_course(2, [_make_transcript(2, "Python 装饰器用法", 0.0)], [])

    result = engine.query_all("Python")
    course_ids = {s["course_id"] for s in result["sources"]}
    assert len(course_ids) >= 2


def test_delete_index_removes_global_docs(tmp_chroma_dir):
    """删除课程索引后，全局 collection 中不应再包含该课程文档。"""
    engine = RAGEngine(llm=FakeLLM())

    engine.index_course(1, [_make_transcript(1, "机器学习基础", 0.0)], [])
    engine.index_course(2, [_make_transcript(2, "深度学习进阶", 0.0)], [])

    # 删除课程 1
    engine.delete_index(1)

    # 全局搜索不应再返回课程 1
    result = engine.query_all("机器学习")
    course_ids = {s["course_id"] for s in result["sources"]}
    assert 1 not in course_ids
