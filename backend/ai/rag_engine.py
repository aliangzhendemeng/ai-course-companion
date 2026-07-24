"""RAG 引擎：基于课程内容的混合检索与问答。"""

import json
import logging
from pathlib import Path

import bm25s
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_core.documents import Document

from backend.ai.factory import create_chat_llm
from backend.ai.llm.base import BaseLLM
from backend.ai.rank_utils import rrf_fuse
from backend.ai.text_utils import tokenize_for_bm25
from backend.config import settings

logger = logging.getLogger(__name__)


class RAGEngine:
    """课程 RAG 引擎，支持向量检索、BM25 稀疏检索、全局跨课程搜索。"""

    GLOBAL_COLLECTION = "global_courses"

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
                doc_id = self._build_doc_id(course_id, "ocr_text", frame_id, frame_index)
                doc_ids.append(doc_id)
                documents.append(Document(
                    page_content=ocr_text,
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

    def _format_sources(self, docs: list[Document], course_title: str | None = None) -> list[dict]:
        """将 Document 格式化为来源列表。"""
        sources = []
        for doc in docs:
            source = {
                "type": doc.metadata.get("source_type"),
                "timestamp": doc.metadata.get("timestamp"),
                "text": doc.page_content[:200],
                "course_id": doc.metadata.get("course_id"),
                "course_title": course_title,
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
    ) -> list[Document]:
        """执行向量 + BM25 混合检索并 RRF 融合。"""
        persist_dir = self._get_persist_directory()

        # 向量检索
        vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=persist_dir,
        )
        vector_docs = vectorstore.similarity_search(question, k=self.vector_k)

        # 构建 doc_id -> Document 映射
        doc_by_id: dict[str, Document] = {}
        for doc in vector_docs:
            doc_id = doc.metadata.get("doc_id") or doc.page_content
            doc_by_id[str(doc_id)] = doc

        # BM25 检索
        bm25_results = self._query_bm25(bm25_name, question, self.bm25_k)
        for doc_id, _ in bm25_results:
            if doc_id not in doc_by_id:
                # 尝试从 Chroma 获取
                try:
                    chroma_doc = vectorstore.get(ids=[doc_id], include=["documents", "metadatas"])
                    if chroma_doc and chroma_doc["documents"]:
                        doc_by_id[doc_id] = Document(
                            page_content=chroma_doc["documents"][0],
                            metadata=chroma_doc["metadatas"][0] or {},
                        )
                except Exception:
                    pass

        # RRF 融合
        vector_ranked = [{"id": doc.metadata.get("doc_id", doc.page_content), **doc.metadata, "text": doc.page_content}
                         for doc in vector_docs]
        bm25_ranked = [{"id": doc_id, **doc_by_id[doc_id].metadata, "text": doc_by_id[doc_id].page_content}
                       for doc_id, _ in bm25_results if doc_id in doc_by_id]

        fused = rrf_fuse([vector_ranked, bm25_ranked], k=self.rrf_k, top_n=self.top_k, key="id")

        # 转回 Document
        result_docs = []
        for item in fused:
            doc_id = item["id"]
            if doc_id in doc_by_id:
                result_docs.append(doc_by_id[doc_id])

        return result_docs

    def query(self, course_id: int, question: str) -> dict:
        """基于课程内容回答问题（单课程）。"""
        collection_name = self._get_collection_name(course_id)
        docs = self._retrieve(collection_name, collection_name, question)

        context_parts = []
        for i, doc in enumerate(docs, 1):
            context_parts.append(f"[{i}] {doc.page_content}")
        context = "\n\n".join(context_parts)

        system_prompt = "你是一位课程助教，只根据提供的课程内容回答问题。如果内容中没有答案，请明确告知用户。"
        user_prompt = f"""
        以下是课程内容片段：

        {context}

        用户问题：{question}

        请基于以上内容回答，并引用相关片段的编号。
        """

        answer = self.llm.chat(system_prompt, user_prompt, max_tokens=1500)

        return {
            "answer": answer,
            "sources": self._format_sources(docs),
        }

    def query_all(self, question: str) -> dict:
        """基于所有课程内容回答问题（全局搜索）。"""
        docs = self._retrieve(self.GLOBAL_COLLECTION, self.GLOBAL_COLLECTION, question)

        context_parts = []
        for i, doc in enumerate(docs, 1):
            context_parts.append(f"[{i}] {doc.page_content}")
        context = "\n\n".join(context_parts)

        system_prompt = "你是一位课程助教，根据提供的多门课程内容回答问题。如果内容中没有答案，请明确告知用户。"
        user_prompt = f"""
        以下是多门课程的内容片段：

        {context}

        用户问题：{question}

        请基于以上内容回答，并引用相关片段的编号。
        """

        answer = self.llm.chat(system_prompt, user_prompt, max_tokens=1500)

        return {
            "answer": answer,
            "sources": self._format_sources(docs),
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
