"""视频抽帧模块：均匀采样关键帧。"""

from pathlib import Path

import cv2


class FrameExtractor:
    """从视频中均匀抽取关键帧。"""

    def __init__(self, max_frames: int = 120, frame_interval: float = 20.0) -> None:
        self.max_frames = max_frames
        self.frame_interval = frame_interval

    def extract(
        self,
        video_path: str | Path,
        output_dir: str | Path,
    ) -> list[dict]:
        """抽取关键帧并返回帧信息列表。

        返回每个帧的时间戳（秒）和保存路径。
        """
        video_path = Path(video_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"无法打开视频: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0

        # 计算实际抽帧间隔：优先满足最大帧数
        if duration > 0:
            interval_by_max = duration / self.max_frames
            actual_interval = max(self.frame_interval, interval_by_max)
        else:
            actual_interval = self.frame_interval

        frames = []
        current_time = 0.0
        frame_index = 0

        while current_time <= duration:
            frame_pos = int(current_time * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
            ret, frame = cap.read()

            if not ret:
                break

            frame_filename = f"frame_{current_time:.2f}.jpg"
            frame_path = output_dir / frame_filename
            cv2.imwrite(str(frame_path), frame)

            frames.append({
                "timestamp": round(current_time, 2),
                "path": str(frame_path),
            })

            frame_index += 1
            current_time = frame_index * actual_interval

        cap.release()
        return frames
