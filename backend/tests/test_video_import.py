"""视频导入测试：download（mock yt-dlp）+ /import API（mock 下载与处理）。"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from backend.api import courses as courses_api
from backend.main import app
from backend.models import Course
from backend.services.course_service import CourseService
from backend.services.video_import_service import VideoImportService


@pytest.fixture
def db_engine(tmp_path):
    eng = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    SQLModel.metadata.create_all(eng)
    return eng


@pytest.fixture(autouse=True)
def _patch_engines(db_engine, monkeypatch):
    import backend.services.course_service as cs
    import backend.database as dbmod
    monkeypatch.setattr(cs, "engine", db_engine)
    monkeypatch.setattr(dbmod, "engine", db_engine)


class _FakeYDL:
    """模拟 yt-dlp：extract_info 时创建假视频文件并返回标题。"""

    def __init__(self, opts):
        self.opts = opts

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def extract_info(self, url, download):
        p = Path(self.opts["outtmpl"].replace("%(ext)s", "mp4"))
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"fake video content")
        return {"title": "测试视频标题"}


def test_download_success(monkeypatch, tmp_path):
    """download 正确返回标题与文件路径。"""
    import backend.services.video_import_service as vis

    class FakeSettings:
        upload_dir = "./data/uploads"
        def resolve_path(self, p):
            return tmp_path

    monkeypatch.setattr(vis, "settings", FakeSettings())
    monkeypatch.setattr(vis.yt_dlp, "YoutubeDL", _FakeYDL)
    title, path = VideoImportService().download("https://example.com/v", course_id=99)
    assert title == "测试视频标题"
    assert Path(path).exists()
    assert Path(path).read_bytes() == b"fake video content"


def test_download_failure_raises(monkeypatch, tmp_path):
    import backend.services.video_import_service as vis

    class FakeSettings:
        upload_dir = "./data/uploads"
        def resolve_path(self, p):
            return tmp_path

    monkeypatch.setattr(vis, "settings", FakeSettings())

    class _BadYDL(_FakeYDL):
        def extract_info(self, url, download):
            raise RuntimeError("网络错误")

    monkeypatch.setattr(vis.yt_dlp, "YoutubeDL", _BadYDL)
    with pytest.raises(ValueError, match="视频下载失败"):
        VideoImportService().download("https://x", course_id=1)


def test_import_endpoint(monkeypatch):
    """/import 创建课程，后台下载回填 video_path/title（mock 下载与处理）。"""
    monkeypatch.setattr(VideoImportService, "download", lambda self, url, cid: ("导入标题", "/tmp/fake.mp4"))
    monkeypatch.setattr(courses_api, "_process_course", lambda cid: None)

    with TestClient(app) as client:
        r = client.post("/api/courses/import", json={"url": "https://example.com/video"})
    assert r.status_code == 200
    cid = r.json()["id"]
    course = CourseService().get_course(cid)
    assert course is not None
    assert course.video_path == "/tmp/fake.mp4"
    assert course.title == "导入标题"


def test_import_custom_title(monkeypatch):
    monkeypatch.setattr(VideoImportService, "download", lambda self, url, cid: ("原标题", "/tmp/fake.mp4"))
    monkeypatch.setattr(courses_api, "_process_course", lambda cid: None)
    with TestClient(app) as client:
        r = client.post("/api/courses/import", json={"url": "https://x", "title": "自定义标题"})
    course = CourseService().get_course(r.json()["id"])
    # 用户传了 title 则优先用用户标题（导入流程不覆盖）
    assert course.title == "自定义标题"
