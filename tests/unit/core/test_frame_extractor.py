"""视频抽帧模块测试。"""

import cv2
import numpy as np

from backend.core.frame_extractor import FrameExtractor


def _create_test_video(path, frames, fps=1):
    """用 OpenCV 生成测试视频。"""
    height, width = 100, 100
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(path), fourcc, fps, (width, height))
    for frame in frames:
        writer.write(frame)
    writer.release()


def test_uniform_mode(tmp_path):
    """均匀抽帧模式应返回预期帧数。"""
    video_path = tmp_path / "uniform.mp4"
    frames = [np.full((100, 100, 3), color, dtype=np.uint8) for color in [(0, 0, 0), (255, 255, 255)]]
    _create_test_video(video_path, frames, fps=1)

    extractor = FrameExtractor(max_frames=10, frame_interval=1.0, mode="uniform")
    result = extractor.extract(video_path, tmp_path / "frames")

    assert len(result) >= 1
    for frame_info in result:
        assert "timestamp" in frame_info
        assert "path" in frame_info


def test_scene_mode_detects_changes(tmp_path):
    """场景变化模式应在画面变化时抽帧。"""
    video_path = tmp_path / "scene.mp4"
    # 0-2s 黑屏，2-4s 白屏，4-6s 黑屏
    frames = []
    frames.extend([np.zeros((100, 100, 3), dtype=np.uint8)] * 2)  # 2s black
    frames.extend([np.full((100, 100, 3), 255, dtype=np.uint8)] * 2)  # 2s white
    frames.extend([np.zeros((100, 100, 3), dtype=np.uint8)] * 2)  # 2s black
    _create_test_video(video_path, frames, fps=1)

    extractor = FrameExtractor(
        max_frames=10,
        frame_interval=1.0,
        mode="scene",
        scene_change_threshold=0.5,
        min_scene_interval=0.5,
    )
    result = extractor.extract(video_path, tmp_path / "frames")

    # 应该有至少 2 个关键帧（黑→白，白→黑）
    assert len(result) >= 2
    assert len(result) <= 10


def test_scene_mode_with_uniform_fallback(tmp_path):
    """场景变化模式在长时间无变化时仍应均匀兜底抽帧。"""
    video_path = tmp_path / "static.mp4"
    # 10s 完全相同的黑屏
    frames = [np.zeros((100, 100, 3), dtype=np.uint8)] * 10
    _create_test_video(video_path, frames, fps=1)

    extractor = FrameExtractor(
        max_frames=5,
        frame_interval=2.0,
        mode="scene",
        scene_change_threshold=0.5,
        min_scene_interval=0.5,
    )
    result = extractor.extract(video_path, tmp_path / "frames")

    # 应该至少有 1 帧兜底，不超过 max_frames
    assert len(result) >= 1
    assert len(result) <= 5


def test_invalid_mode_defaults_to_uniform(tmp_path):
    """无效模式应回退到均匀抽帧。"""
    video_path = tmp_path / "fallback.mp4"
    frames = [np.full((100, 100, 3), color, dtype=np.uint8) for color in [(0, 0, 0), (255, 255, 255)]]
    _create_test_video(video_path, frames, fps=1)

    extractor = FrameExtractor(max_frames=10, frame_interval=1.0, mode="unknown")
    result = extractor.extract(video_path, tmp_path / "frames")

    assert len(result) >= 1
