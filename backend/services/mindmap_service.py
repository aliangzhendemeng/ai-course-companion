"""思维导图服务：LLM 从课程内容生成树状知识结构，缓存到库。"""

import json
import logging

from sqlmodel import Session, select

from backend.ai.factory import create_chat_llm
from backend.ai.llm.base import BaseLLM
from backend.database import engine
from backend.models import Course, MindMap
from backend.services.quiz_service import load_course_full_text

logger = logging.getLogger(__name__)

MAX_TEXT = 6000  # 思维导图用较紧凑的上下文


def _extract_json_object(text: str) -> dict | None:
    """从 LLM 输出提取首个 JSON 对象（容错：跳过 markdown 围栏、括号平衡）。"""
    s = text.strip()
    start = s.find("{")
    if start < 0:
        return None
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(s)):
        c = s[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    try:
                        obj = json.loads(s[start : i + 1])
                        return obj if isinstance(obj, dict) else None
                    except json.JSONDecodeError:
                        return None
    return None


def _normalize_tree(node, depth: int = 0, max_depth: int = 3) -> dict:
    """规整树节点：title 必填、children 限深限宽。"""
    if not isinstance(node, dict):
        return {"title": str(node), "children": []}
    title = (str(node.get("title") or node.get("name") or "")).strip()
    if not title:
        return {"title": "（未命名）", "children": []}
    result = {"title": title}
    if depth >= max_depth - 1:
        return result  # 已到最大深度，不再展开子节点
    raw_children = node.get("children") or node.get("branches") or []
    if isinstance(raw_children, list):
        children = []
        for ch in raw_children[:6]:  # 每层最多 6 个分支
            nch = _normalize_tree(ch, depth + 1, max_depth)
            if nch["title"] and nch["title"] != "（未命名）":
                children.append(nch)
        if children:
            result["children"] = children
    return result


class MindMapService:
    """课程思维导图生成。"""

    def __init__(self, llm: BaseLLM | None = None) -> None:
        self.llm = llm or create_chat_llm()

    def get_or_generate(self, course_id: int) -> dict:
        """返回思维导图树；首次调用自动生成并缓存。"""
        with Session(engine) as session:
            existing = session.exec(
                select(MindMap).where(MindMap.course_id == course_id)
            ).first()
            if existing:
                try:
                    return json.loads(existing.tree)
                except json.JSONDecodeError:
                    pass  # 损坏则重新生成
        return self.generate(course_id)

    def generate(self, course_id: int) -> dict:
        """LLM 生成思维导图树并存库（覆盖旧的）。"""
        with Session(engine) as session:
            course = session.get(Course, course_id)
            if not course:
                raise ValueError(f"课程不存在: {course_id}")
            full_text = load_course_full_text(session, course_id)
        if not full_text.strip():
            return {"title": course.title, "children": []}

        context = full_text[:MAX_TEXT]
        system_prompt = "你是一位课程助教。请把课程内容提炼成层次清晰的思维导图（树状知识结构）。"
        user_prompt = f"""
        以下是课程内容：

        {context}

        请生成思维导图，严格输出 JSON 对象（不要额外文字、不要 markdown 围栏）：
        {{
          "title": "课程主题（简短）",
          "children": [
            {{ "title": "分支1", "children": [{{ "title": "子要点" }}, ...] }},
            ...
          ]
        }}
        要求：根节点是课程主题；2~4 个主分支；每个主分支 2~4 个子要点；总深度不超过 3 层；标题简短（不超过 12 字）。
        """
        try:
            raw = self.llm.chat(system_prompt, user_prompt, max_tokens=1200)
            obj = _extract_json_object(raw)
        except Exception as e:
            logger.warning("思维导图 LLM 调用失败: %s", e)
            obj = None

        tree = _normalize_tree(obj) if obj else {"title": course.title, "children": []}

        with Session(engine) as session:
            for old in session.exec(select(MindMap).where(MindMap.course_id == course_id)).all():
                session.delete(old)
            session.add(MindMap(course_id=course_id, tree=json.dumps(tree, ensure_ascii=False)))
            session.commit()
        return tree
