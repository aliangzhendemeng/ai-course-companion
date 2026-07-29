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

    def _phash(self, frame: np.ndarray, hash_size: int = 8) -> np.ndarray:
        """计算感知哈希（基于 DCT），用于检测视觉相似的幻灯片。

        返回一个 hash_size*hash_size 位的 0/1 数组。
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # 缩放到 4 倍 hash_size 再做 DCT，取左上角低频分量
        img_size = hash_size * 4
        small = cv2.resize(gray, (img_size, img_size), interpolation=cv2.INTER_AREA)
        dct = cv2.dct(np.float32(small))
        dct_low = dct[:hash_size, :hash_size]
        # 以中位数为阈值，排除直流分量（左上角）以免整图亮度影响
        median = np.median(dct_low.flatten()[1:])
        return (dct_low > median).flatten()

    @staticmethod
    def _hamming(a: np.ndarray, b: np.ndarray) -> int:
        """两个哈希之间的汉明距离。"""
        return int(np.count_nonzero(a != b))

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
        """基于场景变化检测抽帧。

        除了与上一关键帧比较直方图判断场景变化外，还用感知哈希对"所有"已保存
        关键帧去重：当讲师反复回到同一张幻灯片时，视觉上相同的帧只保留首次出现。
        """
        frames = []
        last_keyframe_time = -self.min_scene_interval
        last_keyframe_hist = None
        frame_count = 0

        # 兜底间隔：当场景变化检测失灵时，按此间隔强制抽帧，
        # 取 frame_interval 与 duration/max_frames 的较大值，避免产生过多帧
        fallback_interval = max(self.frame_interval, duration / self.max_frames) if duration > 0 else self.frame_interval
        last_fallback_time = -fallback_interval

        # 已保存关键帧的感知哈希，用于检测重复幻灯片
        saved_hashes: list[np.ndarray] = []
        # 两帧感知哈希汉明距离 <= 此阈值视为视觉重复（8x8=64 位）
        dedup_threshold = 10

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

            # 兜底：按稀疏间隔强制抽帧
            fallback_due = (current_time - last_fallback_time) >= fallback_interval

            if scene_changed or fallback_due or last_keyframe_hist is None:
                # 去重：与所有已保存关键帧比较，视觉重复则跳过（首帧除外）
                if last_keyframe_hist is not None:
                    ph = self._phash(frame)
                    is_duplicate = any(self._hamming(ph, h) <= dedup_threshold for h in saved_hashes)
                else:
                    is_duplicate = False

                if is_duplicate:
                    # 视觉重复，不保存，但更新参考直方图以追踪当前画面
                    last_keyframe_hist = hist
                    last_keyframe_time = current_time
                    last_fallback_time = current_time
                    continue

                frames.append(self._save_frame(frame, current_time, output_dir))
                saved_hashes.append(self._phash(frame))
                last_keyframe_time = current_time
                last_keyframe_hist = hist
                last_fallback_time = current_time
            else:
                # 更新参考直方图为加权移动平均，避免渐变场景漏检
                last_keyframe_hist = 0.9 * last_keyframe_hist + 0.1 * hist

        return frames
