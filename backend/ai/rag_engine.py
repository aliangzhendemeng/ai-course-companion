"""RAG 引擎：基于课程内容的混合检索与问答。"""

import json
import logging
from pathlib import Path

import bm25s
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_core.documents import Document
from sqlmodel import Session, select

from backend.ai.factory import create_chat_llm
from backend.ai.llm.base import BaseLLM
from backend.ai.rank_utils import rrf_fuse
from backend.ai.text_utils import tokenize_for_bm25
from backend.config import settings
from backend.database import engine
from backend.models import Frame, Transcript

logger = logging.getLogger(__name__)


class RAGEngine:
    """课程 RAG 引擎，支持向量检索、BM25 稀疏检索、全局跨课程搜索。"""

    GLOBAL_COLLECTION = "global_courses"
    # 单课程完整文本上限，超过后自动切换到片段 RAG
    FULL_TEXT_MAX_CHARS = 200000

    def __init__(
        self,
        llm: BaseLLM | None = None,
        embedding_model: str = "BAAI/bge-base-zh-v1.5",
    ) -> None:
        self.llm = llm or create_chat_llm()
        self.embeddings = HuggingFaceEmbeddings(model_name=embedding_model)
        self.top_k = settings.rag_top_k
        self.vector_k = settings.rag_vector_k
        self.bm25_k = settings.rag_bm25_k
        self.rrf_k = settings.rag_rrf_k

    def _get_collection_name(self, course_id: int) -> str:
        return f"course_{course_id}"

    def _get_persist_directory(self) -> str:
        return str(settings.resolve_path(settings.chroma_dir))

    def _get_bm25_dir(self) -> Path:
        bm25_dir = settings.resolve_path(settings.bm25_dir)
        bm25_dir.mkdir(parents=True, exist_ok=True)
        return bm25_dir

    def _clean_metadata(self, metadata: dict) -> dict:
        """过滤 Chroma 不支持的 None / 复杂类型 metadata。"""
        allowed_types = (str, int, float, bool)
        return {k: v for k, v in metadata.items() if isinstance(v, allowed_types)}

    def _build_doc_id(self, course_id: int, source_type: str, item_id, index: int) -> str:
        """生成稳定的文档 ID。"""
        base = f"{course_id}:{source_type}:{item_id or index}:{index}"
        return base

    def _build_documents(
        self,
        course_id: int,
        transcripts: list,
        frames: list,
    ) -> tuple[list[Document], list[str]]:
        """构建 Document 列表和对应 doc_id 列表。"""
        documents = []
        doc_ids = []

        for idx, transcript in enumerate(transcripts):
            text = transcript.text if hasattr(transcript, "text") else transcript["text"]
            start_time = transcript.start_time if hasattr(transcript, "start_time") else transcript["start_time"]
            transcript_id = transcript.id if hasattr(transcript, "id") else transcript.get("id")
            doc_id = self._build_doc_id(course_id, "transcript", transcript_id, idx)
            doc_ids.append(doc_id)
            documents.append(Document(
                page_content=text,
                metadata=self._clean_metadata({
                    "course_id": course_id,
                    "source_type": "transcript",
                    "timestamp": start_time,
                    "transcript_id": transcript_id,
                    "doc_id": doc_id,
                }),
            ))

        frame_index = len(transcripts)
        for frame in frames:
            ocr_text = frame.ocr_text if hasattr(frame, "ocr_text") else frame.get("ocr_text")
            vision_desc = frame.vision_desc if hasattr(frame, "vision_desc") else frame.get("vision_desc")
            timestamp = frame.timestamp if hasattr(frame, "timestamp") else frame["timestamp"]
            frame_id = frame.id if hasattr(frame, "id") else frame.get("id")

            if ocr_text:
                # 对 OCR 文本按行合并，避免标题和正文被拆成多个短文档
                merged_ocr = self._merge_ocr_text(ocr_text)
                doc_id = self._build_doc_id(course_id, "ocr_text", frame_id, frame_index)
                doc_ids.append(doc_id)
                documents.append(Document(
                    page_content=merged_ocr,
                    metadata=self._clean_metadata({
                        "course_id": course_id,
                        "source_type": "ocr_text",
                        "timestamp": timestamp,
                        "frame_id": frame_id,
                        "doc_id": doc_id,
                    }),
                ))
                frame_index += 1

            if vision_desc:
                doc_id = self._build_doc_id(course_id, "vision_desc", frame_id, frame_index)
                doc_ids.append(doc_id)
                documents.append(Document(
                    page_content=vision_desc,
                    metadata=self._clean_metadata({
                        "course_id": course_id,
                        "source_type": "vision_desc",
                        "timestamp": timestamp,
                        "frame_id": frame_id,
                        "doc_id": doc_id,
                    }),
                ))
                frame_index += 1

        return documents, doc_ids

    def _merge_ocr_text(self, ocr_text: str) -> str:
        """合并 OCR 文本中的短行，保留段落结构。"""
        lines = [line.strip() for line in ocr_text.split("\n") if line.strip()]
        if not lines:
            return ""
        merged = []
        current = lines[0]
        for line in lines[1:]:
            # 如果当前行较短（标题/列表项）或下一行是列表项，则换行
            if len(current) < 20 or line.startswith("·") or line.startswith("-") or line[0].isdigit():
                merged.append(current)
                current = line
            else:
                current += line
        merged.append(current)
        return "\n".join(merged)

    def _get_bm25_path(self, name: str) -> Path:
        """获取 BM25 索引路径。"""
        return self._get_bm25_dir() / f"{name}.bm25"

    def _get_bm25_doc_ids_path(self, name: str) -> Path:
        return self._get_bm25_dir() / f"{name}_doc_ids.json"

    def _save_bm25(self, name: str, documents: list[Document], doc_ids: list[str]) -> None:
        """保存 BM25 索引到磁盘。"""
        if not documents:
            return
        texts = [doc.page_content for doc in documents]
        tokenized = tokenize_for_bm25(texts)
        retriever = bm25s.BM25()
        retriever.index(tokenized)
        retriever.save(str(self._get_bm25_path(name)))
        self._get_bm25_doc_ids_path(name).write_text(
            json.dumps(doc_ids, ensure_ascii=False),
            encoding="utf-8",
        )

    def _load_bm25(self, name: str):
        """加载 BM25 索引，不存在则返回 None。"""
        index_path = self._get_bm25_path(name)
        doc_ids_path = self._get_bm25_doc_ids_path(name)
        if not index_path.exists() or not doc_ids_path.exists():
            return None, None
        retriever = bm25s.BM25.load(str(index_path))
        doc_ids = json.loads(doc_ids_path.read_text(encoding="utf-8"))
        return retriever, doc_ids

    def _query_bm25(self, name: str, question: str, top_k: int) -> list[tuple[str, int]]:
        """使用 BM25 检索，返回 (doc_id, index) 列表。"""
        retriever, doc_ids = self._load_bm25(name)
        if retriever is None or not doc_ids:
            return []
        tokenized = tokenize_for_bm25([question])
        if not tokenized:
            return []
        results = retriever.retrieve(tokenized, k=min(top_k, len(doc_ids)))
        # bm25s 返回结果是 numpy ndarray，形状通常为 (1, k)，元素是文档在 doc_ids 中的索引
        import numpy as np
        indices = np.asarray(results[0]).flatten()
        matched = []
        for idx in indices:
            idx = int(idx)
            matched.append((doc_ids[idx], idx))
        return matched

    def index_course(
        self,
        course_id: int,
        transcripts: list,
        frames: list,
    ) -> None:
        """为课程构建向量索引、BM25 索引，并同步到全局索引。"""
        documents, doc_ids = self._build_documents(course_id, transcripts, frames)
        if not documents:
            return

        documents = filter_complex_metadata(documents)

        persist_dir = self._get_persist_directory()
        collection_name = self._get_collection_name(course_id)

        # 1. 课程向量索引
        Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            collection_name=collection_name,
            persist_directory=persist_dir,
            ids=doc_ids,
        )

        # 2. 课程 BM25 索引
        self._save_bm25(collection_name, documents, doc_ids)

        # 3. 全局向量索引（metadata 带 course_id，id 加前缀避免冲突）
        global_documents = []
        global_doc_ids = []
        for doc, doc_id in zip(documents, doc_ids):
            global_doc_id = f"g:{doc_id}"
            global_doc_ids.append(global_doc_id)
            global_documents.append(Document(
                page_content=doc.page_content,
                metadata=self._clean_metadata({
                    **doc.metadata,
                    "course_id": course_id,
                }),
            ))

        vectorstore = Chroma(
            collection_name=self.GLOBAL_COLLECTION,
            embedding_function=self.embeddings,
            persist_directory=persist_dir,
        )
        vectorstore.add_documents(global_documents, ids=global_doc_ids)

        # 4. 全局 BM25 索引重建（简单实现：全量重建）
        self._rebuild_global_bm25(persist_dir)

    def _rebuild_global_bm25(self, persist_dir: str) -> None:
        """重建全局 BM25 索引。"""
        vectorstore = Chroma(
            collection_name=self.GLOBAL_COLLECTION,
            embedding_function=self.embeddings,
            persist_directory=persist_dir,
        )
        all_docs = vectorstore.get(include=["documents", "metadatas"])
        ids = all_docs.get("ids", [])
        documents = all_docs.get("documents", [])
        metadatas = all_docs.get("metadatas", [])

        if not documents:
            return

        docs = [Document(page_content=text, metadata=meta or {}) for text, meta in zip(documents, metadatas)]
        self._save_bm25(self.GLOBAL_COLLECTION, docs, ids)

    def _get_course_titles(self, course_ids: list[int]) -> dict[int, str]:
        """按 course_id 批量查询课程标题。"""
        if not course_ids:
            return {}
        from backend.models import Course
        titles: dict[int, str] = {}
        with Session(engine) as session:
            for cid in course_ids:
                course = session.get(Course, cid)
                if course:
                    titles[cid] = course.title
        return titles

    def _format_sources(
        self,
        docs: list[Document],
        course_titles: dict[int, str] | None = None,
        fallback_title: str | None = None,
    ) -> list[dict]:
        """将 Document 格式化为来源列表，附带课程名和真实时间戳。"""
        sources = []
        for doc in docs:
            course_id = doc.metadata.get("course_id")
            title = None
            if course_titles and course_id in course_titles:
                title = course_titles[course_id]
            elif fallback_title:
                title = fallback_title
            source = {
                "type": doc.metadata.get("source_type"),
                "timestamp": doc.metadata.get("timestamp") or 0,
                "text": doc.page_content[:200],
                "course_id": course_id,
                "course_title": title,
            }
            if doc.metadata.get("frame_id"):
                source["frame_id"] = doc.metadata["frame_id"]
            if doc.metadata.get("transcript_id"):
                source["transcript_id"] = doc.metadata["transcript_id"]
            sources.append(source)
        return sources

    def _retrieve(
        self,
        collection_name: str,
        bm25_name: str,
        question: str,
        course_filter: list[int] | None = None,
    ) -> list[Document]:
        """执行向量 + BM25 混合检索并 RRF 融合。

        course_filter：限定只检索这些课程的文档（学习集/多课程场景）。
        向量检索用 Chroma where 过滤；BM25 结果在应用层按 course_id 过滤。
        """
        persist_dir = self._get_persist_directory()

        # 向量检索（Chroma where 过滤课程）
        vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=persist_dir,
        )
        where = {"course_id": {"$in": course_filter}} if course_filter else None
        vector_docs = vectorstore.similarity_search(question, k=self.vector_k, filter=where)

        # 构建 doc_id -> Document 映射
        doc_by_id: dict[str, Document] = {}
        for doc in vector_docs:
            doc_id = doc.metadata.get("doc_id") or doc.page_content
            doc_by_id[str(doc_id)] = doc

        # BM25 检索（应用层按 course_id 过滤）
        bm25_results = self._query_bm25(bm25_name, question, self.bm25_k)
        for doc_id, _ in bm25_results:
            if doc_id not in doc_by_id:
                # 尝试从 Chroma 获取
                try:
                    chroma_doc = vectorstore.get(ids=[doc_id], include=["documents", "metadatas"])
                    if chroma_doc and chroma_doc["documents"]:
                        meta = chroma_doc["metadatas"][0] or {}
                        # 课程过滤：不在范围内的 BM25 候选直接跳过
                        if course_filter and meta.get("course_id") not in course_filter:
                            continue
                        doc_by_id[doc_id] = Document(
                            page_content=chroma_doc["documents"][0],
                            metadata=meta,
                        )
                except Exception:
                    pass

        # RRF 融合，保留更多候选，再做多样性重排序
        vector_ranked = [
            {"id": doc.metadata.get("doc_id", doc.page_content), **doc.metadata, "text": doc.page_content}
            for doc in vector_docs
        ]
        bm25_ranked = [
            {"id": doc_id, **doc_by_id[doc_id].metadata, "text": doc_by_id[doc_id].page_content}
            for doc_id, _ in bm25_results if doc_id in doc_by_id
        ]

        fused = rrf_fuse([vector_ranked, bm25_ranked], k=self.rrf_k, top_n=self.top_k * 2, key="id")
        fused = self._diversity_rerank(fused, top_n=self.top_k)

        # 转回 Document
        result_docs = []
        for item in fused:
            doc_id = item["id"]
            if doc_id in doc_by_id:
                result_docs.append(doc_by_id[doc_id])

        return result_docs

    def _diversity_rerank(self, items: list[dict], top_n: int) -> list[dict]:
        """多样性重排序：避免同一页面/幻灯片的重复内容挤占结果。"""
        selected = []
        for item in items:
            text = item.get("text", "")
            if len(selected) >= top_n:
                break
            # 跳过与已选文档高度重复的内容（同一幻灯片被多次采样）
            if any(self._overlap_ratio(text, s.get("text", "")) > 0.7 for s in selected):
                continue
            selected.append(item)
        for item in items:
            if item not in selected:
                selected.append(item)
        return selected[:top_n]

    def _overlap_ratio(self, a: str, b: str) -> float:
        """计算两个字符串的 token 重叠率。"""
        set_a = set(a)
        set_b = set(b)
        if not set_a or not set_b:
            return 0.0
        return len(set_a & set_b) / min(len(set_a), len(set_b))

    def query(self, course_id: int, question: str) -> dict:
        """基于课程内容回答问题（单课程）。

        优先使用完整清洗文本；如果文本过长，则回退到 RAG 片段。
        """
        full_text = self._load_course_full_text(course_id)
        if full_text and len(full_text) <= self.FULL_TEXT_MAX_CHARS:
            return self._query_with_full_text(question, full_text, course_id)

        # 回退：课程无内容或过长，使用 RAG 片段
        collection_name = self._get_collection_name(course_id)
        docs = self._retrieve(collection_name, collection_name, question)
        return self._answer_with_docs(question, docs, multi_course=False)

    def _load_course_full_text(self, course_id: int) -> str:
        """从数据库加载一门课的完整清洗文本（字幕 + OCR）。"""
        with Session(engine) as session:
            transcripts = session.exec(
                select(Transcript).where(Transcript.course_id == course_id).order_by(Transcript.start_time)
            ).all()
            frames = session.exec(
                select(Frame).where(Frame.course_id == course_id).order_by(Frame.timestamp)
            ).all()

        parts = []
        for t in transcripts:
            if t.text:
                parts.append(f"[字幕 {format_timestamp(t.start_time)}] {t.text}")
        for f in frames:
            if f.ocr_text:
                merged = self._merge_ocr_text(f.ocr_text)
                if merged:
                    parts.append(f"[课件 {format_timestamp(f.timestamp)}] {merged}")

        return "\n\n".join(parts)

    def _query_with_full_text(self, question: str, full_text: str, course_id: int) -> dict:
        """使用完整课程文本直接回答。"""
        system_prompt = (
            "你是一位严谨的课程助教。请严格根据下面提供的完整课程内容回答用户问题。"
            "如果内容中没有包含问题的答案，请明确告诉用户'根据现有课程内容，无法找到答案'，不要编造。"
        )
        user_prompt = f"""
        以下是完整课程内容：

        {full_text}

        用户问题：{question}

        要求：
        1. 仅基于以上课程内容回答。
        2. 如果内容中没有答案，明确说明无法找到。
        3. 回答尽量准确、完整。
        """

        raw_answer = self.llm.chat(system_prompt, user_prompt, max_tokens=1500)

        # 用检索片段生成带真实时间戳和课程名的来源，而不是 0:00 占位
        collection_name = self._get_collection_name(course_id)
        try:
            source_docs = self._retrieve(collection_name, collection_name, question)
        except Exception as e:
            logger.warning("全文问答来源检索失败 course=%s: %s", course_id, e)
            source_docs = []
        course_titles = self._get_course_titles([course_id])

        return {
            "answer": raw_answer,
            "debug": {
                "model": getattr(self.llm, "model_identifier", "unknown"),
                "prompt": f"system:\n{system_prompt}\n\nuser:\n{user_prompt}",
                "context": full_text,
                "raw_answer": raw_answer,
            },
            "sources": self._format_sources(
                source_docs,
                course_titles=course_titles,
                fallback_title=course_titles.get(course_id),
            ),
        }

    def _answer_with_docs(self, question: str, docs: list[Document], multi_course: bool) -> dict:
        """使用 RAG 检索到的片段回答。"""
        context_parts = []
        for i, doc in enumerate(docs, 1):
            context_parts.append(f"[{i}] {doc.page_content}")
        context = "\n\n".join(context_parts)

        if multi_course:
            system_prompt = (
                "你是一位严谨的课程助教。请严格根据下面提供的多门课程内容片段回答用户问题。"
                "如果片段中没有包含问题的答案，请明确告诉用户'根据现有课程内容，无法找到答案'，不要编造。"
                "回答时尽量引用相关片段的编号，并说明来自哪门课程。"
            )
            user_prompt = f"""
            以下是多门课程的内容片段，按相关性排序：

            {context}

            用户问题：{question}

            要求：
            1. 仅基于以上片段内容回答。
            2. 如果片段中没有答案，明确说明无法找到。
            3. 引用相关片段编号 [1]、[2] 等。
            """
        else:
            system_prompt = (
                "你是一位严谨的课程助教。请严格根据下面提供的课程内容片段回答用户问题。"
                "如果片段中没有包含问题的答案，请明确告诉用户'根据现有课程内容，无法找到答案'，不要编造。"
                "回答时尽量引用相关片段的编号。"
            )
            user_prompt = f"""
            以下是课程内容片段，按相关性排序：

            {context}

            用户问题：{question}

            要求：
            1. 仅基于以上片段内容回答。
            2. 如果片段中没有答案，明确说明无法找到。
            3. 引用相关片段编号 [1]、[2] 等。
            """

        answer = self.llm.chat(system_prompt, user_prompt, max_tokens=1500)

        course_ids = list({doc.metadata.get("course_id") for doc in docs if doc.metadata.get("course_id") is not None})
        course_titles = self._get_course_titles(course_ids)

        return {
            "answer": answer,
            "debug": {
                "model": getattr(self.llm, "model_identifier", "unknown"),
                "prompt": f"system:\n{system_prompt}\n\nuser:\n{user_prompt}",
                "context": context,
                "raw_answer": answer,
            },
            "sources": self._format_sources(docs, course_titles=course_titles),
        }

    def query_all(self, question: str) -> dict:
        """基于所有课程内容回答问题（全局搜索）。"""
        return self._query_across_courses(question, course_filter=None)

    def query_multiple(self, course_ids: list[int], question: str) -> dict:
        """基于指定的若干门课程回答问题（学习集/多课程范围）。

        与 query_all 的区别：检索与全文拼接都限制在 course_ids 范围内，
        不引入其他课程的内容。
        """
        if not course_ids:
            return {
                "answer": "学习集内暂无可用课程（可能都未处理完成或已被删除）。",
                "debug": {"model": getattr(self.llm, "model_identifier", "unknown"), "prompt": "", "context": "", "raw_answer": ""},
                "sources": [],
            }
        return self._query_across_courses(question, course_filter=course_ids)

    def _query_across_courses(self, question: str, course_filter: list[int] | None) -> dict:
        """跨课程回答核心：先全局检索定位相关课程，再拼接这些课的完整文本回答。

        course_filter 为 None 表示全部课程；否则限定在指定课程集合内。
        """
        docs = self._retrieve(self.GLOBAL_COLLECTION, self.GLOBAL_COLLECTION, question, course_filter=course_filter)

        # 收集相关课程 ID，按 RRF 分数排序去重
        course_ids: list[int] = []
        seen = set()
        for doc in docs:
            cid = doc.metadata.get("course_id")
            if cid is not None and cid not in seen:
                course_ids.append(cid)
                seen.add(cid)

        if not course_ids:
            return self._answer_with_docs(question, docs, multi_course=True)

        # 取前 N 门相关课程，避免上下文爆炸
        course_ids = course_ids[:3]
        course_titles = self._get_course_titles(course_ids)
        context_parts = []
        for cid in course_ids:
            full_text = self._load_course_full_text(cid)
            if not full_text:
                continue
            title = course_titles.get(cid, f"课程 {cid}")
            context_parts.append(f"===== {title} =====\n{full_text}")

        if not context_parts:
            return self._answer_with_docs(question, docs, multi_course=True)

        context = "\n\n".join(context_parts)
        system_prompt = (
            "你是一位严谨的课程助教。请严格根据下面提供的多门完整课程内容回答用户问题。"
            "如果内容中没有包含问题的答案，请明确告诉用户'根据现有课程内容，无法找到答案'，不要编造。"
        )
        user_prompt = f"""
        以下是多门课程的完整内容：

        {context}

        用户问题：{question}

        要求：
        1. 仅基于以上课程内容回答。
        2. 如果内容中没有答案，明确说明无法找到。
        3. 回答时尽量说明来自哪门课程或哪个时间点。
        """

        answer = self.llm.chat(system_prompt, user_prompt, max_tokens=1500)

        # 用全局检索片段作为来源，带课程名和时间戳
        sources = self._format_sources(docs, course_titles=course_titles)

        return {
            "answer": answer,
            "debug": {
                "model": getattr(self.llm, "model_identifier", "unknown"),
                "prompt": f"system:\n{system_prompt}\n\nuser:\n{user_prompt}",
                "context": context,
                "raw_answer": answer,
            },
            "sources": sources,
        }

    def delete_index(self, course_id: int) -> None:
        """删除课程向量索引、BM25 索引，并清理全局索引。"""
        persist_dir = self._get_persist_directory()
        collection_name = self._get_collection_name(course_id)

        # 删除课程向量索引
        try:
            vectorstore = Chroma(
                collection_name=collection_name,
                embedding_function=self.embeddings,
                persist_directory=persist_dir,
            )
            vectorstore.delete_collection()
        except Exception as e:
            logger.warning("删除课程向量索引失败 course=%s: %s", course_id, e)

        # 删除课程 BM25 索引（bm25s 保存的是目录）
        try:
            import shutil
            bm25_path = self._get_bm25_path(collection_name)
            if bm25_path.exists():
                shutil.rmtree(bm25_path)
            self._get_bm25_doc_ids_path(collection_name).unlink(missing_ok=True)
        except Exception as e:
            logger.warning("删除课程 BM25 索引失败 course=%s: %s", course_id, e)

        # 删除全局 collection 中该课程的文档
        try:
            global_store = Chroma(
                collection_name=self.GLOBAL_COLLECTION,
                embedding_function=self.embeddings,
                persist_directory=persist_dir,
            )
            global_store.delete(where={"course_id": course_id})
        except Exception as e:
            logger.warning("删除全局索引中课程文档失败 course=%s: %s", course_id, e)

        # 重建全局 BM25 索引
        try:
            self._rebuild_global_bm25(persist_dir)
        except Exception as e:
            logger.warning("重建全局 BM25 索引失败 course=%s: %s", course_id, e)


def format_timestamp(seconds: float) -> str:
    """将秒数格式化为 mm:ss。"""
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m}:{s:02d}"
