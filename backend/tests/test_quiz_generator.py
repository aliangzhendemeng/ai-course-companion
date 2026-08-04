"""quiz_generator 的 JSON 解析与规范化单元测试（不调真实 LLM）。"""

import pytest

from backend.ai.quiz_generator import (
    QuizGenerationError,
    _extract_json_array,
    _normalize_flashcards,
    _normalize_questions,
    generate_flashcards,
    generate_questions,
)


class FakeLLM:
    """模拟 LLM，按队列返回预设文本。"""

    def __init__(self, outputs: list[str]):
        self.outputs = list(outputs)
        self.calls = 0

    def chat(self, system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> str:
        self.calls += 1
        return self.outputs.pop(0)

    @property
    def model_identifier(self) -> str:
        return "fake"


# ===== _extract_json_array =====


def test_extract_clean_array():
    data = _extract_json_array('[{"a": 1}, {"a": 2}]')
    assert data == [{"a": 1}, {"a": 2}]


def test_extract_with_surrounding_text():
    text = '好的，这是题目：\n[{"q": "1+1=?"}]\n希望对你有帮助！'
    data = _extract_json_array(text)
    assert data == [{"q": "1+1=?"}]


def test_extract_strips_markdown_fence():
    text = '```json\n[{"q": "x"}]\n```'
    data = _extract_json_array(text)
    assert data == [{"q": "x"}]


def test_extract_ignores_brackets_inside_strings():
    # 字符串内的 [ ] 不应影响括号平衡
    text = '[{"q": "选项 [A] 是 [B] 吗？"}]'
    data = _extract_json_array(text)
    assert data == [{"q": "选项 [A] 是 [B] 吗？"}]


def test_extract_handles_escaped_quote_in_string():
    text = '[{"q": "他说 \\"你好\\" 对吗"}]'
    data = _extract_json_array(text)
    assert data == [{"q": '他说 "你好" 对吗'}]


def test_extract_no_array_raises():
    with pytest.raises(QuizGenerationError):
        _extract_json_array("这里没有数组")


def test_extract_unclosed_raises():
    with pytest.raises(QuizGenerationError):
        _extract_json_array('[{"a": 1}')


def test_extract_top_level_not_array_raises():
    # 顶层是对象而非数组
    with pytest.raises(QuizGenerationError):
        _extract_json_array('{"a": 1}')


# ===== _normalize_questions =====


def test_normalize_choice_and_judge():
    data = [
        {
            "type": "choice",
            "question": "1+1=?",
            "options": ["1", "2", "3", "4"],
            "answer": "B",
            "explanation": "基础算术",
        },
        {"type": "judge", "question": "地球是平的", "options": None, "answer": "错误"},
    ]
    out = _normalize_questions(data)
    assert len(out) == 2
    assert out[0]["type"] == "choice"
    assert out[0]["options"] == ["1", "2", "3", "4"]
    assert out[1]["answer"] == "错误"


def test_normalize_judge_answer_variants():
    for raw, expected in [("对", "正确"), ("true", "正确"), ("错", "错误"), ("false", "错误")]:
        out = _normalize_questions(
            [{"type": "judge", "question": "q", "answer": raw}]
        )
        assert out[0]["answer"] == expected


def test_normalize_drops_answer_out_of_range():
    # 答案字母超出选项范围 → 丢弃
    out = _normalize_questions(
        [{"type": "choice", "question": "q", "options": ["A", "B"], "answer": "D"}]
    )
    assert out == []


def test_normalize_drops_invalid_items():
    data = [
        "not a dict",
        {"type": "choice", "question": "", "options": ["a", "b"], "answer": "A"},  # 空题干
        {"type": "choice", "question": "q", "options": ["only one"], "answer": "A"},  # 选项太少
        {"type": "unknown", "question": "q", "answer": "A"},  # 非法类型
        {"type": "judge", "question": "q", "answer": "maybe"},  # 判断题答案非法
    ]
    assert _normalize_questions(data) == []


def test_normalize_empty_explanation_becomes_none():
    out = _normalize_questions(
        [{"type": "judge", "question": "q", "answer": "正确", "explanation": "  "}]
    )
    assert out[0]["explanation"] is None


# ===== _normalize_flashcards =====


def test_normalize_flashcards_filters_empty():
    data = [
        {"front": "概念", "back": "解释"},
        {"front": "", "back": "x"},  # 空正面
        {"front": "y", "back": " "},  # 空背面
        "not a dict",
    ]
    out = _normalize_flashcards(data)
    assert out == [{"front": "概念", "back": "解释"}]


# ===== 端到端（FakeLLM）：重试逻辑 =====


def test_generate_questions_retries_on_bad_json_then_succeeds():
    llm = FakeLLM(
        [
            "这不是 JSON",  # 第一次失败
            '[{"type": "judge", "question": "q", "answer": "正确"}]',  # 第二次成功
        ]
    )
    out = generate_questions("课程全文", count=2, llm=llm)
    assert llm.calls == 2
    assert len(out) == 1


def test_generate_questions_raises_after_two_failures():
    llm = FakeLLM(["bad", "still bad"])
    with pytest.raises(QuizGenerationError):
        generate_questions("课程全文", count=2, llm=llm)
    assert llm.calls == 2


def test_generate_flashcards_uses_llm():
    llm = FakeLLM(['[{"front": "f", "back": "b"}]'])
    out = generate_flashcards("课程全文", count=5, llm=llm)
    assert out == [{"front": "f", "back": "b"}]
