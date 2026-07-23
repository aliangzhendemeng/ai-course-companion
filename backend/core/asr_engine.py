"""ASR 引擎：基于 faster-whisper 的语音识别。"""

from pathlib import Path

from faster_whisper import WhisperModel


class ASREngine:
    """本地语音识别引擎。"""

    def __init__(
        self,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8",
    ) -> None:
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, audio_path: str | Path) -> list[dict]:
        """转写音频，返回带时间戳的字幕列表。"""
        audio_path = Path(audio_path)
        segments, _ = self.model.transcribe(str(audio_path), language="zh", beam_size=5)

        transcripts = []
        for segment in segments:
            transcripts.append({
                "text": segment.text.strip(),
                "start_time": round(segment.start, 2),
                "end_time": round(segment.end, 2),
            })

        return transcripts
