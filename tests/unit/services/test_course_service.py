"""课程服务测试。"""

import pytest

from backend.services.course_service import CourseService


def test_create_course():
    service = CourseService()
    course = service.create_course(title="测试课程", video_path="/tmp/test.mp4")
    assert course.title == "测试课程"
    assert course.status == "uploaded"

    # 清理
    service.delete_course(course.id)


def test_update_status():
    service = CourseService()
    course = service.create_course(title="测试课程", video_path="/tmp/test.mp4")
    updated = service.update_status(course.id, "transcribing", "转写中")
    assert updated.status == "transcribing"
    assert updated.status_message == "转写中"

    # 清理
    service.delete_course(course.id)
