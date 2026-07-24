"""视频抽帧模块：均匀采样 + 场景变化检测。"""

from pathlib import Path

import cv2
import numpy as np


class FrameExtractor:
    """从视频中抽取关键帧。"""

    def __init__(
        self,
        max_frames: int = 120,
        frame_interval: float = 20.0,
        mode: str = "uniform",
        scene_change_threshold: float = 0.65,
        min_scene_interval: float = 5.0,
    ) -> None:
        self.max_frames = max_frames
        self.frame_interval = frame_interval
        self.mode = mode
        self.scene_change_threshold = scene_change_threshold
        self.min_scene_interval = min_scene_interval

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

        if self.mode == "scene":
            frames = self._extract_scene_based(cap, fps, duration, output_dir)
        else:
            frames = self._extract_uniform(cap, fps, duration, output_dir)

        cap.release()

        # 如果场景变化模式一个帧都没抽到（极短或异常视频），回退到均匀采样
        if not frames:
            cap = cv2.VideoCapture(str(video_path))
            frames = self._extract_uniform(cap, fps, duration, output_dir)
            cap.release()

        # 超过最大帧数时均匀下采样
        if len(frames) > self.max_frames:
            step = len(frames) / self.max_frames
            frames = [frames[int(i * step)] for i in range(self.max_frames)]

        return frames

    def _save_frame(self, frame: np.ndarray, timestamp: float, output_dir: Path) -> dict:
        """保存单帧并返回信息。"""
        frame_filename = f"frame_{timestamp:.2f}.jpg"
        frame_path = output_dir / frame_filename
        cv2.imwrite(str(frame_path), frame)
        return {
            "timestamp": round(timestamp, 2),
            "path": str(frame_path),
        }

    def _extract_uniform(
        self,
        cap: cv2.VideoCapture,
        fps: float,
        duration: float,
        output_dir: Path,
    ) -> list[dict]:
        """均匀抽帧。"""
        if duration > 0:
            interval_by_max = duration / self.max_frames
            actual_interval = max(self.frame_interval, interval_by_max)
        else:
            actual_interval = self.frame_interval

        frames = []
        frame_index = 0
        current_time = 0.0

        while current_time <= duration:
            frame_pos = int(current_time * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
            ret, frame = cap.read()
            if not ret:
                break

            frames.append(self._save_frame(frame, current_time, output_dir))

            frame_index += 1
            current_time = frame_index * actual_interval

        return frames

    def _extract_scene_based(
        self,
        cap: cv2.VideoCapture,
        fps: float,
        duration: float,
        output_dir: Path,
    ) -> list[dict]:
        """基于场景变化检测抽帧。"""
        frames = []
        last_keyframe_time = -self.min_scene_interval
        last_keyframe_hist = None
        frame_count = 0

        # 用于兜底均匀采样的计时器
        last_fallback_time = -self.frame_interval

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            current_time = frame_count / fps if fps > 0 else 0
            frame_count += 1

            # 转换为灰度并计算直方图
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            hist = cv2.calcHist([gray], [0], None, [64], [0, 256])
            hist = cv2.normalize(hist, hist).flatten()

            scene_changed = False
            if last_keyframe_hist is not None:
                similarity = cv2.compareHist(last_keyframe_hist, hist, cv2.HISTCMP_CORREL)
                time_since_last = current_time - last_keyframe_time
                if similarity < self.scene_change_threshold and time_since_last >= self.min_scene_interval:
                    scene_changed = True

            # 兜底：按 frame_interval 强制抽帧
            fallback_due = (current_time - last_fallback_time) >= self.frame_interval

            if scene_changed or fallback_due or last_keyframe_hist is None:
                frames.append(self._save_frame(frame, current_time, output_dir))
                last_keyframe_time = current_time
                last_keyframe_hist = hist
                last_fallback_time = current_time
            else:
                # 更新参考直方图为加权移动平均，避免渐变场景漏检
                last_keyframe_hist = 0.9 * last_keyframe_hist + 0.1 * hist

        return frames
