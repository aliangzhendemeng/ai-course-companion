"""问答服务。"""

import base64
import json
import logging
import re
import tempfile
from pathlib import Path

from sqlmodel import Session

from backend.ai.factory import create_vision_analyzer
from backend.ai.llm.base import BaseLLM
from backend.ai.rag_engine import RAGEngine
from backend.ai.vision.base import BaseVisionAnalyzer
from backend.database import engine
from backend.models import ChatMessage
from backend.services.conversation_service import ConversationService
from backend.services.course_service import CourseService

logger = logging.getLogger(__name__)


class ChatService:
    """课程问答服务。"""

    def __init__(
        self,
        rag_engine: RAGEngine | None = None,
        vision_analyzer: BaseVisionAnalyzer | None = None,
    ) -> None:
        self.rag_engine = rag_engine or RAGEngine()
        self.course_service = CourseService()
        self._vision_analyzer = vision_analyzer

    @property
    def vision_analyzer(self) -> BaseVisionAnalyzer:
        if self._vision_analyzer is None:
            self._vision_analyzer = create_vision_analyzer()
        return self._vision_analyzer

    def ask(
        self,
        course_id: int,
        question: str,
        scope: str = "course",
        course_ids: list[int] | None = None,
        image: str | None = None,
        conversation_id: int | None = None,
    ) -> dict:
        """提问并返回答案。支持多轮会话：传 conversation_id 续写（带历史上下文），
        不传则新建会话。

        scope="course"：单课程；scope="all"：全部课程；
        scope="set"（或传入 course_ids）：限定在指定课程集合内（学习集）。
        image：用户上传图片（base64 data url），有图则走视觉问答，不依赖课程检索。
        """
        course = self.course_service.get_course(course_id)
        if not course:
            raise ValueError(f"课程不存在: {course_id}")

        conv_svc = ConversationService()
        history: list[tuple[str, str]] = []

        # 续写：校验会话归属，沿用会话范围，取最近历史作上下文
        if conversation_id:
            conv = conv_svc.get(conversation_id)
            if not conv:
                raise ValueError(f"会话不存在: {conversation_id}")
            if conv.course_id != course_id:
                raise ValueError("会话不属于该课程")
            scope = conv.scope or scope
            course_ids = json.loads(conv.course_ids) if conv.course_ids else None
            msgs = conv_svc.messages(conversation_id)
            history = [(m.role, m.content) for m in msgs][-6:]

        # 图片问答：不要求课程处理完成，也不走 RAG
        if image:
            return self._answer_with_image(
                course_id, question, image, scope, history, conversation_id, conv_svc
            )

        if course.status != "completed":
            raise ValueError("课程尚未处理完成，无法问答")

        if course_ids:
            result = self.rag_engine.query_multiple(course_ids, question, history=history)
        elif scope == "all":
            result = self.rag_engine.query_all(question, history=history)
        else:
            result = self.rag_engine.query(course_id, question, history=history)

        # set/all 范围：记录实际涉及的课程 id，供历史页正确显示归属（而非锚点课程）
        involved_ids = self._involved_course_ids(course_ids, result)

        # 新会话：首次提问时创建（标题取问题前 20 字）
        if not conversation_id:
            conv = conv_svc.create(
                course_id,
                title=(question or "新会话")[:20],
                scope=scope,
                course_ids=json.dumps(involved_ids) if involved_ids else None,
            )
            conversation_id = conv.id

        cids_str = json.dumps(involved_ids) if involved_ids else None
        with Session(engine) as session:
            user_msg = ChatMessage(
                course_id=course_id,
                conversation_id=conversation_id,
                role="user",
                content=question,
                scope=scope,
                course_ids=cids_str,
            )
            assistant_msg = ChatMessage(
                course_id=course_id,
                conversation_id=conversation_id,
                role="assistant",
                content=result["answer"],
                scope=scope,
                course_ids=cids_str,
                sources=json.dumps(result["sources"], ensure_ascii=False),
                debug_info=json.dumps(result.get("debug", {}), ensure_ascii=False),
            )
            session.add(user_msg)
            session.add(assistant_msg)
            session.commit()
            session.refresh(assistant_msg)

        conv_svc.touch(conversation_id)
        return {**result, "answer_message_id": assistant_msg.id, "conversation_id": conversation_id}

    # ----- 图片问答 -----

    _DATA_URL_RE = re.compile(r"data:([^;]+);base64,(.+)", re.DOTALL)

    def _decode_image(self, image: str) -> tuple[str, bytes]:
        """解析 base64 data url（或纯 base64），返回 (mime, bytes)。"""
        m = self._DATA_URL_RE.match(image.strip())
        if m:
            mime = m.group(1)
            raw = base64.b64decode(m.group(2))
        else:
            mime = "image/png"
            raw = base64.b64decode(image)
        return mime, raw

    def _describe_image(self, image: str) -> str:
        """把上传图片存临时文件，调用视觉模型得到文字描述。"""
        mime, raw = self._decode_image(image)
        ext = ".png"
        for e in (".png", ".jpg", ".jpeg", ".webp", ".gif"):
            if e in mime:
                ext = e
                break
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(raw)
            tmp_path = Path(tmp.name)
        try:
            return self.vision_analyzer.understand_frame(tmp_path)
        except Exception as e:
            logger.warning("图片视觉理解失败: %s", e)
            return "（图片识别失败）"
        finally:
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass

    def _answer_with_image(
        self,
        course_id: int,
        question: str,
        image: str,
        scope: str,
        history: list[tuple[str, str]] | None = None,
        conversation_id: int | None = None,
        conv_svc: ConversationService | None = None,
    ) -> dict:
        """图片问答：视觉描述 + 用户问题 -> chat LLM 回答。带会话历史上下文。"""
        conv_svc = conv_svc or ConversationService()
        desc = self._describe_image(image)
        llm: BaseLLM = self.rag_engine.llm
        hist = RAGEngine._format_history(history)
        system_prompt = (
            "你是一位课程助教。用户上传了一张图片并提出了问题。"
            "下面是视觉模型对图片的内容描述，请据此回答用户问题。"
            "若描述信息不足以回答，请如实说明并给出你能判断的部分。"
        )
        user_prompt = f"{hist}图片内容描述：\n{desc}\n\n用户问题：{question}"
        answer = llm.chat(system_prompt, user_prompt, max_tokens=1200)

        if not conversation_id:
            conv = conv_svc.create(course_id, title=(question or "图片提问")[:20], scope=scope)
            conversation_id = conv.id

        with Session(engine) as session:
            user_msg = ChatMessage(
                course_id=course_id,
                conversation_id=conversation_id,
                role="user",
                content=f"{question}\n[附图片]",
                scope=scope,
            )
            assistant_msg = ChatMessage(
                course_id=course_id,
                conversation_id=conversation_id,
                role="assistant",
                content=answer,
                scope=scope,
            )
            session.add(user_msg)
            session.add(assistant_msg)
            session.commit()
            session.refresh(assistant_msg)

        conv_svc.touch(conversation_id)
        return {
            "answer": answer,
            "sources": [],
            "debug": {"image_description": desc},
            "answer_message_id": assistant_msg.id,
            "conversation_id": conversation_id,
        }

    def _involved_course_ids(
        self, course_ids: list[int] | None, result: dict
    ) -> list[int]:
        """set/all 范围下，消息实际涉及的课程 id 列表。"""
        if course_ids:
            return sorted(set(course_ids))
        # all / 其它：从来源里提取实际命中的课程
        ids = {
            s.get("course_id")
            for s in (result.get("sources") or [])
            if s.get("course_id") is not None
        }
        return sorted(ids)

    def get_history(self, course_id: int) -> list[ChatMessage]:
        """获取问答历史。"""
        from sqlmodel import Session, select

        with Session(engine) as session:
            statement = (
                select(ChatMessage)
                .where(ChatMessage.course_id == course_id)
                .order_by(ChatMessage.created_at.asc())
            )
            return list(session.exec(statement).all())
