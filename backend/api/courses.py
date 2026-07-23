"""课程相关 API。"""

import shutil
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, BackgroundTasks

from backend.ai.processor import VideoProcessor
from backend.config import settings
from backend.schemas import CourseCreateResponse, CourseDetail, CourseListItem
from backend.services.course_service import CourseService

router = APIRouter()


@router.get("", response_model=list[CourseListItem])
def list_courses():
    """列出所有课程。"""
    service = CourseService()
    return service.list_courses()


@router.post("/upload", response_model=CourseCreateResponse)
def upload_course(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    file: UploadFile = File(...),
):
    """上传视频并创建课程。"""
    service = CourseService()

    # 创建课程记录
    course = service.create_course(title=title, video_path="")

    # 保存上传文件
    upload_dir = settings.resolve_path(settings.upload_dir) / str(course.id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_ext = Path(file.filename or "video.mp4").suffix
    video_path = upload_dir / f"video{file_ext}"

    with open(video_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # 更新课程路径和状态
    course.video_path = str(video_path)
    service.update_course(course)

    # 后台处理
    background_tasks.add_task(VideoProcessor().process, course.id)

    return CourseCreateResponse(
        id=course.id,
        title=course.title,
        status=course.status,
        created_at=course.created_at,
    )


@router.get("/{course_id}", response_model=CourseDetail)
def get_course(course_id: int):
    """获取课程详情。"""
    service = CourseService()
    course = service.get_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    return course


@router.delete("/{course_id}")
def delete_course(course_id: int):
    """删除课程。"""
    service = CourseService()
    service.delete_course(course_id)
    return {"message": "已删除"}


@router.post("/{course_id}/reprocess")
def reprocess_course(course_id: int, background_tasks: BackgroundTasks):
    """重新处理课程。"""
    service = CourseService()
    course = service.get_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")

    service.update_status(course_id, "uploaded", "重新处理")
    background_tasks.add_task(VideoProcessor().process, course_id)
    return {"message": "已加入处理队列"}
