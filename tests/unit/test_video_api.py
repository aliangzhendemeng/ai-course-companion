"""视频流 API 测试。"""

from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import app
from backend.services.course_service import CourseService

client = TestClient(app)


def test_video_stream_without_range(tmp_path):
    """无 Range 头时应返回完整视频流。"""
    video_path = tmp_path / "test.mp4"
    video_path.write_bytes(b"fake video content here")

    service = CourseService()
    course = service.create_course(
        title="test video",
        video_path=str(video_path),
        file_hash="hash1",
    )

    response = client.get(f"/api/courses/{course.id}/video")
    assert response.status_code == 200
    assert response.headers["content-type"] == "video/mp4"
    assert response.content == video_path.read_bytes()


def test_video_stream_with_range(tmp_path):
    """有 Range 头时应返回 206 与正确 Content-Range。"""
    video_path = tmp_path / "test.mkv"
    content = b"0123456789"
    video_path.write_bytes(content)

    service = CourseService()
    course = service.create_course(
        title="test video range",
        video_path=str(video_path),
        file_hash="hash2",
    )

    response = client.get(
        f"/api/courses/{course.id}/video",
        headers={"Range": "bytes=2-5"},
    )
    assert response.status_code == 206
    assert response.headers["content-type"] == "video/x-matroska"
    assert response.headers["content-range"] == f"bytes 2-5/{len(content)}"
    assert response.content == b"2345"


def test_video_stream_course_not_found():
    """课程不存在时返回 404。"""
    response = client.get("/api/courses/99999/video")
    assert response.status_code == 404


def test_course_detail_returns_video_url(tmp_path):
    """CourseDetail 应返回 video_url 而非 video_path。"""
    video_path = tmp_path / "detail.mp4"
    video_path.write_bytes(b"detail")

    service = CourseService()
    course = service.create_course(
        title="detail test",
        video_path=str(video_path),
        file_hash="hash3",
    )

    response = client.get(f"/api/courses/{course.id}")
    assert response.status_code == 200
    data = response.json()
    assert "video_url" in data
    assert "video_path" not in data
    assert data["video_url"].endswith(f"/api/courses/{course.id}/video")
