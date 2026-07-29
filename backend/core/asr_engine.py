"""ASR 引擎：基于 faster-whisper 的语音识别。

输出统一为简体中文（OpenCC 繁→简后处理）。
关键反幻觉设置：
- condition_on_previous_text=False：不把上文（含 initial_prompt）向前传递，
  避免在静音/不清晰片段反复重复同一句话（Whisper 常见幻觉）。
- vad_filter=True：先用 VAD 跳过静音段，减少无意义幻觉。
注意：不要用 initial_prompt 下达"请用简体"这类指令——Whisper 会把它当作
转写内容在每段重复输出。简体由 OpenCC 后处理保证。
"""

from pathlib import Path

from faster_whisper import WhisperModel
from opencc import OpenCC

from backend.config import settings


class ASREngine:
    """本地语音识别引擎。"""

    def __init__(
        self,
        model_size: str | None = None,
        device: str | None = None,
        compute_type: str | None = None,
    ) -> None:
        # 未显式传入时读全局配置，便于在 .env 通过 ASR_MODEL_SIZE 调整
        self.model_size = model_size or settings.asr_model_size
        self.model = WhisperModel(
            self.model_size,
            device=device or settings.asr_device,
            compute_type=compute_type or settings.asr_compute_type,
        )
        # 繁体 -> 简体（t2s），保证输出为简体中文
        self._t2s = OpenCC("t2s")

    def transcribe(self, audio_path: str | Path) -> list[dict]:
        """转写音频，返回带时间戳的字幕列表。"""
        audio_path = Path(audio_path)
        segments, _ = self.model.transcribe(
            str(audio_path),
            language="zh",
            beam_size=5,
            # 关键：禁止把上文向前传递，消除"每段重复同一句"的幻觉
            condition_on_previous_text=False,
            # 跳过静音段，进一步减少幻觉
            vad_filter=True,
        )

        transcripts = []
        for segment in segments:
            text = segment.text.strip()
            if not text:
                continue
            # 强制转简体
            text = self._t2s.convert(text)
            transcripts.append({
                "text": text,
                "start_time": round(segment.start, 2),
                "end_time": round(segment.end, 2),
            })

        return transcripts
