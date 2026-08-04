"""测验/闪卡生成器：从课程全文用 LLM 生成结构化题目与卡片。

设计要点：
- prompt 强制"只输出 JSON 数组"，减少废话。
- 解析用正则提取首个 `[...]` 块，容错 LLM 在 JSON 前后加的解释文字。
- 解析失败重试一次，仍失败抛出生成失败异常。
"""

import json
import logging
import re

from backend.ai.factory import create_chat_llm
from backend.ai.llm.base import BaseLLM

logger = logging.getLogger(__name__)


class QuizGenerationError(Exception):
    """出题失败（LLM 输出无法解析为合法 JSON）。"""


def _extract_json_array(text: str) -> list:
    """从 LLM 输出中提取首个 JSON 数组并解析。

    容错：LLM 常在 JSON 前后加解释，故用正则抓首个平衡的 [...] 块。
    """
    text = text.strip()
    # 去掉 markdown 代码围栏
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE)

    start = text.find("[")
    if start == -1:
        raise QuizGenerationError("输出中未找到 JSON 数组")

    # 从首个 [ 起，按括号平衡截取完整数组
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                candidate = text[start : i + 1]
                try:
                    data = json.loads(candidate)
                    if isinstance(data, list):
                        return data
                    raise QuizGenerationError("JSON 顶层不是数组")
                except json.JSONDecodeError as e:
                    raise QuizGenerationError(f"JSON 解析失败: {e}") from e

    raise QuizGenerationError("JSON 数组未闭合")


_QUESTION_SYSTEM = (
    "你是一位专业的课程命题老师。请严格根据给定的课程内容出选择题和判断题，"
    "帮助学生自测对知识的掌握。题目必须基于课程内容，不要编造课程中没有的知识点。"
)

_FLASHCARD_SYSTEM = (
    "你是一位专业的课程学习卡片制作者。请严格根据给定的课程内容制作记忆闪卡，"
    "正面是核心概念或问题，背面是简明解释。内容必须来自课程，不要编造。"
)


def _call_llm_json(llm: BaseLLM, system: str, user: str) -> list:
    """调 LLM 并解析为 JSON 数组，失败重试一次。"""
    last_err: Exception | None = None
    for attempt in range(2):
        try:
            raw = llm.chat(system, user, max_tokens=3000)
            return _extract_json_array(raw)
        except QuizGenerationError as e:
            last_err = e
            logger.warning("出题 JSON 解析失败（第 %d 次）: %s", attempt + 1, e)
        except Exception as e:  # LLM 调用本身失败
            last_err = e
            logger.warning("出题 LLM 调用失败（第 %d 次）: %s", attempt + 1, e)
    raise QuizGenerationError(f"出题失败：{last_err}")


def generate_questions(
    full_text: str,
    count: int = 12,
    llm: BaseLLM | None = None,
) -> list[dict]:
    """从课程全文生成选择题/判断题。

    返回列表，每项：{type, question, options, answer, explanation}
    - type: "choice" | "judge"
    - options: list[str]（选择题），判断题为 null
    - answer: 选择题为 "A"/"B"...，判断题为 "正确"/"错误"
    """
    llm = llm or create_chat_llm()
    choice_n = max(1, round(count * 0.7))
    judge_n = count - choice_n

    user = f"""
以下是课程内容：

{full_text}

请出 {choice_n} 道单选题和 {judge_n} 道判断题，帮助学生自测。
要求：
1. 只输出一个 JSON 数组，不要输出任何其他文字（不要解释、不要 markdown 围栏）。
2. 数组中每个元素是一道题，格式如下：
   单选题：{{"type": "choice", "question": "题干", "options": ["选项A内容", "选项B内容", "选项C内容", "选项D内容"], "answer": "A", "explanation": "解析"}}
   判断题：{{"type": "judge", "question": "题干", "options": null, "answer": "正确", "explanation": "解析"}}
3. answer 单选题填正确选项的字母（A/B/C/D），判断题填"正确"或"错误"。
4. 题目要覆盖课程的不同知识点，难度适中。
5. 全部使用中文。
"""
    data = _call_llm_json(llm, _QUESTION_SYSTEM, user)
    return _normalize_questions(data)


def generate_flashcards(
    full_text: str,
    count: int = 15,
    llm: BaseLLM | None = None,
) -> list[dict]:
    """从课程全文生成闪卡。

    返回列表，每项：{front, back}
    """
    llm = llm or create_chat_llm()
    user = f"""
以下是课程内容：

{full_text}

请制作 {count} 张记忆闪卡，帮助学生记忆核心概念。
要求：
1. 只输出一个 JSON 数组，不要输出任何其他文字（不要解释、不要 markdown 围栏）。
2. 数组中每个元素是一张卡，格式：{{"front": "概念或问题", "back": "简明解释"}}
3. 正面是核心概念、术语或问题，背面是简洁准确的解释（一两句话）。
4. 覆盖课程的不同知识点。
5. 全部使用中文。
"""
    data = _call_llm_json(llm, _FLASHCARD_SYSTEM, user)
    return _normalize_flashcards(data)


def _normalize_questions(data: list) -> list[dict]:
    """校验并规范化题目，过滤非法项。"""
    result = []
    for item in data:
        if not isinstance(item, dict):
            continue
        qtype = item.get("type")
        question = (item.get("question") or "").strip()
        answer = str(item.get("answer") or "").strip()
        if not question or not answer or qtype not in ("choice", "judge"):
            continue
        options = item.get("options")
        if qtype == "choice":
            if not isinstance(options, list) or len(options) < 2:
                continue
            options = [str(o).strip() for o in options]
            answer = answer.upper()
            if answer not in [chr(ord("A") + i) for i in range(len(options))]:
                continue  # 答案字母超出选项范围，丢弃
        else:  # judge
            options = None
            if answer not in ("正确", "错误"):
                # 兼容 true/false、对/错
                if answer in ("对", "true", "True", "√"):
                    answer = "正确"
                elif answer in ("错", "false", "False", "×"):
                    answer = "错误"
                else:
                    continue
        result.append(
            {
                "type": qtype,
                "question": question,
                "options": options,
                "answer": answer,
                "explanation": (item.get("explanation") or "").strip() or None,
            }
        )
    return result


def _normalize_flashcards(data: list) -> list[dict]:
    """校验并规范化闪卡，过滤非法项。"""
    result = []
    for item in data:
        if not isinstance(item, dict):
            continue
        front = (item.get("front") or "").strip()
        back = (item.get("back") or "").strip()
        if not front or not back:
            continue
        result.append({"front": front, "back": back})
    return result
