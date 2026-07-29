"""RAGEngine 多课程检索（query_multiple）单元测试。"""

from unittest.mock import patch

import pytest

from backend.ai.rag_engine import RAGEngine


@pytest.fixture
def rag(monkeypatch):
    """构造一个不重初始化重型组件的 RAGEngine。"""
    engine = RAGEngine.__new__(RAGEngine)
    # query_multiple 空集合分支只需 llm.model_identifier
    class _LLM:
        model_identifier = "deepseek:deepseek-chat"
    engine.llm = _LLM()
    return engine


class TestQueryMultiple:
    def test_empty_course_ids_returns_hint(self, rag):
        """空学习集：返回降级提示，不调用检索/LLM。"""
        result = rag.query_multiple([], "任意问题")
        assert "暂无可用课程" in result["answer"]
        assert result["sources"] == []

    def test_course_filter_passed_to_retrieve(self, rag):
        """非空集合：_retrieve 收到 course_filter 限定范围。"""
        captured = {}

        def fake_retrieve(collection, bm25, question, course_filter=None):
            captured["course_filter"] = course_filter
            return []

        # 无相关课时走 _answer_with_docs，mock 掉避免触 LLM
        with patch.object(rag, "_retrieve", side_effect=fake_retrieve), patch.object(
            rag, "_answer_with_docs", return_value={"answer": "x", "sources": [], "debug": {}}
        ):
            rag.query_multiple([1, 2], "大数据分析")

        assert captured["course_filter"] == [1, 2]

    def test_query_all_uses_no_filter(self, rag):
        """query_all 不限定课程（course_filter=None）。"""
        captured = {}

        def fake_retrieve(collection, bm25, question, course_filter=None):
            captured["course_filter"] = course_filter
            return []

        with patch.object(rag, "_retrieve", side_effect=fake_retrieve), patch.object(
            rag, "_answer_with_docs", return_value={"answer": "x", "sources": [], "debug": {}}
        ):
            rag.query_all("大数据分析")

        assert captured["course_filter"] is None
