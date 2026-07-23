import json

import pytest

from backend.ai.summarizer import Summarizer


class FakeLLM:
    def chat(self, system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> str:
        if "大纲" in user_prompt:
            return json.dumps([{"title": "第一章", "timestamp": 0.0}])
        if "摘要" in user_prompt:
            return "这是摘要"
        return "这是讲义"


def test_summarizer_build_context():
    summarizer = Summarizer(llm=FakeLLM())
    transcripts = [{"text": "你好", "start_time": 0.0, "end_time": 1.0}]
    frames = [{"timestamp": 0.5, "ocr_text": "文字", "vision_desc": "描述"}]
    result = summarizer.summarize(transcripts, frames)

    assert "outline" in result
    assert "abstract" in result
    assert "lecture_notes" in result
    assert result["abstract"] == "这是摘要"
