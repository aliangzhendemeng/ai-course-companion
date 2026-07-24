"""RAG 引擎：基于课程内容的检索与问答。"""

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_core.documents import Document

from backend.ai.factory import create_chat_llm
from backend.ai.llm.base import BaseLLM
from backend.config import settings


class RAGEngine:
    """课程 RAG 引擎。"""

    def __init__(
        self,
        llm: BaseLLM | None = None,
        embedding_model: str = "BAAI/bge-base-zh-v1.5",
    ) -> None:
        self.llm = llm or create_chat_llm()
        self.embeddings = HuggingFaceEmbeddings(model_name=embedding_model)
        self.top_k = settings.rag_top_k

    def _get_collection_name(self, course_id: int) -> str:
        return f"course_{course_id}"

    def _get_persist_directory(self) -> str:
        return str(settings.resolve_path(settings.chroma_dir))

    def _clean_metadata(self, metadata: dict) -> dict:
        """过滤 Chroma 不支持的 None / 复杂类型 metadata。"""
        allowed_types = (str, int, float, bool)
        return {k: v for k, v in metadata.items() if isinstance(v, allowed_types)}

    def index_course(
        self,
        course_id: int,
        transcripts: list,
        frames: list,
    ) -> None:
        """为课程构建向量索引。"""
        documents = []

        # 字幕文本切块
        for transcript in transcripts:
            text = transcript.text if hasattr(transcript, "text") else transcript["text"]
            start_time = transcript.start_time if hasattr(transcript, "start_time") else transcript["start_time"]
            transcript_id = transcript.id if hasattr(transcript, "id") else transcript.get("id")
            documents.append(Document(
                page_content=text,
                metadata=self._clean_metadata({
                    "course_id": course_id,
                    "source_type": "transcript",
                    "timestamp": start_time,
                    "transcript_id": transcript_id,
                }),
            ))

        # 帧 OCR 文字
        for frame in frames:
            ocr_text = frame.ocr_text if hasattr(frame, "ocr_text") else frame.get("ocr_text")
            vision_desc = frame.vision_desc if hasattr(frame, "vision_desc") else frame.get("vision_desc")
            timestamp = frame.timestamp if hasattr(frame, "timestamp") else frame["timestamp"]
            frame_id = frame.id if hasattr(frame, "id") else frame.get("id")

            if ocr_text:
                documents.append(Document(
                    page_content=ocr_text,
                    metadata=self._clean_metadata({
                        "course_id": course_id,
                        "source_type": "ocr_text",
                        "timestamp": timestamp,
                        "frame_id": frame_id,
                    }),
                ))

            # 帧视觉描述
            if vision_desc:
                documents.append(Document(
                    page_content=vision_desc,
                    metadata=self._clean_metadata({
                        "course_id": course_id,
                        "source_type": "vision_desc",
                        "timestamp": timestamp,
                        "frame_id": frame_id,
                    }),
                ))

        if not documents:
            return

        documents = filter_complex_metadata(documents)

        Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            collection_name=self._get_collection_name(course_id),
            persist_directory=self._get_persist_directory(),
        )

    def query(self, course_id: int, question: str) -> dict:
        """基于课程内容回答问题。"""
        persist_dir = self._get_persist_directory()
        collection_name = self._get_collection_name(course_id)

        vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=persist_dir,
        )

        docs = vectorstore.similarity_search(question, k=self.top_k)

        context_parts = []
        sources = []
        for i, doc in enumerate(docs, 1):
            context_parts.append(f"[{i}] {doc.page_content}")
            source = {
                "type": doc.metadata.get("source_type"),
                "timestamp": doc.metadata.get("timestamp"),
                "text": doc.page_content[:200],
            }
            if doc.metadata.get("frame_id"):
                source["frame_id"] = doc.metadata["frame_id"]
            if doc.metadata.get("transcript_id"):
                source["transcript_id"] = doc.metadata["transcript_id"]
            sources.append(source)

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
            "sources": sources,
        }

    def delete_index(self, course_id: int) -> None:
        """删除课程向量索引。"""
        persist_dir = self._get_persist_directory()
        collection_name = self._get_collection_name(course_id)
        vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=persist_dir,
        )
        vectorstore.delete_collection()
