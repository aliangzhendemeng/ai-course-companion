"""三级总结生成器。"""

import json

from backend.ai.factory import create_summary_llm
from backend.ai.llm.base import BaseLLM


class Summarizer:
    """基于音频字幕和画面信息生成三级总结。"""

    def __init__(self, llm: BaseLLM | None = None) -> None:
        self.llm = llm or create_summary_llm()

    def summarize(
        self,
        transcripts: list[dict],
        frames: list[dict],
    ) -> dict[str, str]:
        """生成大纲、摘要、讲义。

        transcripts: [{text, start_time, end_time}]
        frames: [{timestamp, ocr_text, vision_desc}]
        """
        context = self._build_context(transcripts, frames)

        outline = self._generate_outline(context)
        abstract = self._generate_abstract(context)
        lecture_notes = self._generate_lecture_notes(context)

        return {
            "outline": outline,
            "abstract": abstract,
            "lecture_notes": lecture_notes,
        }

    def _build_context(self, transcripts: list[dict], frames: list[dict]) -> str:
        """构建融合音频和画面的上下文文本。"""
        lines = ["【音频字幕】"]
        for t in transcripts:
            lines.append(f"[{t['start_time']:.1f}s - {t['end_time']:.1f}s] {t['text']}")

        lines.append("\n【画面信息】")
        for f in frames:
            lines.append(f"[{f['timestamp']:.1f}s]")
            if f.get("ocr_text"):
                lines.append(f"  OCR文字: {f['ocr_text']}")
            if f.get("vision_desc"):
                lines.append(f"  画面描述: {f['vision_desc']}")

        return "\n".join(lines)

    def _generate_outline(self, context: str) -> str:
        """生成课程大纲。"""
        system_prompt = "你是一位优秀的课程助教，擅长整理课程大纲。"
        user_prompt = f"""
        请根据以下课程内容，生成一个结构清晰的课程大纲。
        每个章节请包含标题和对应的时间戳（秒）。
        以 JSON 数组格式返回，例如：
        [{{"title": "第一章 简介", "timestamp": 0.0}}, ...]

        课程内容：
        {context[:8000]}
        """
        response = self.llm.chat(system_prompt, user_prompt, max_tokens=1500)
        return self._extract_json(response)

    def _generate_abstract(self, context: str) -> str:
        """生成内容摘要。"""
        system_prompt = "你是一位优秀的课程助教，擅长提炼课程核心内容。"
        user_prompt = f"""
        请根据以下课程内容，用 300-500 字总结课程的核心知识点。
        重点涵盖音频讲解和画面中的图表、公式、代码等关键信息。

        课程内容：
        {context[:12000]}
        """
        return self.llm.chat(system_prompt, user_prompt, max_tokens=1500)

    def _generate_lecture_notes(self, context: str) -> str:
        """生成详细讲义。"""
        system_prompt = "你是一位优秀的课程助教，擅长编写详细讲义。"
        user_prompt = f"""
        请根据以下课程内容，编写一份详细讲义。
        讲义应包含：
        1. 各章节核心知识点
        2. 画面中的图表、公式、代码说明
        3. 重要概念的解释
        使用 Markdown 格式，结构清晰。

        课程内容：
        {context[:15000]}
        """
        return self.llm.chat(system_prompt, user_prompt, max_tokens=3000)

    def _extract_json(self, text: str) -> str:
        """尝试从 LLM 响应中提取 JSON。"""
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        try:
            json.loads(text)
            return text
        except json.JSONDecodeError:
            # 如果解析失败，返回原始文本
            return text
