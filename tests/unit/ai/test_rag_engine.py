"""RAG 引擎测试。"""

import pytest

from backend.ai.rag_engine import RAGEngine


class FakeLLM:
    def chat(self, system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> str:
        return "fake answer"


def test_rag_engine_index_and_query(tmp_path):
    engine = RAGEngine(llm=FakeLLM())
    engine._get_persist_directory = lambda: str(tmp_path / "chroma")

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
