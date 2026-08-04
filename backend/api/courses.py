"""课程相关 API。"""

import hashlib
import mimetypes
import shutil
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, BackgroundTasks, Request
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel

from backend.ai.processor import VideoProcessor
from backend.config import settings
from backend.schemas import CourseCreateResponse, CourseDetail, CourseListItem
from backend.services.course_service import CourseService

router = APIRouter()


class ImportRequest(BaseModel):
    url: str
    title: str | None = None


def _process_course(course_id: int) -> None:
    """在后台任务中初始化处理器并处理课程，避免上传请求被阻塞。"""
    VideoProcessor().process(course_id)


def _compute_file_hash(file: UploadFile) -> str:
    """计算上传文件 SHA256 哈希，用于幂等性判断。"""
    hasher = hashlib.sha256()
    file.file.seek(0)
    for chunk in iter(lambda: file.file.read(8192), b""):
        hasher.update(chunk)
    file.file.seek(0)
    return hasher.hexdigest()


def _get_video_url(course_id: int, request: Request) -> str:
    """构造视频流 URL。"""
    return str(request.url_for("stream_course_video", course_id=course_id))


def _guess_media_type(video_path: Path) -> str:
    """根据文件后缀猜测视频 MIME 类型。"""
    ext = video_path.suffix.lower()
    mapping = {
        ".mp4": "video/mp4",
        ".mkv": "video/x-matroska",
        ".mov": "video/quicktime",
        ".avi": "video/x-msvideo",
        ".webm": "video/webm",
    }
    return mapping.get(ext) or mimetypes.guess_type(str(video_path))[0] or "application/octet-stream"


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

    # 计算文件哈希，避免重复上传同一文件创建多个课程
    file_hash = _compute_file_hash(file)
    existing = service.get_course_by_file_hash(file_hash)
    if existing and existing.status != "failed":
        return CourseCreateResponse(
            id=existing.id,
            title=existing.title,
            status=existing.status,
            created_at=existing.created_at,
        )

    # 创建课程记录
    course = service.create_course(title=title, video_path="", file_hash=file_hash)

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

    # 后台处理：延迟初始化 VideoProcessor，避免阻塞上传响应
    background_tasks.add_task(_process_course, course.id)

    return CourseCreateResponse(
        id=course.id,
        title=course.title,
        status=course.status,
        created_at=course.created_at,
    )


def _import_course(course_id: int, url: str) -> None:
    """后台：从 URL 下载视频 → 回填路径/标题 → 复用现有处理流程。"""
    from backend.services.video_import_service import VideoImportService

    service = CourseService()
    try:
        service.update_status(course_id, "downloading", "正在下载视频…")
        title, video_path = VideoImportService().download(url, course_id)
        course = service.get_course(course_id)
        if not course:
            return
        course.video_path = video_path
        # 仅当用户未自定义标题（占位"导入中…"）时才用视频原标题
        if not course.title or course.title == "导入中…":
            course.title = title
        service.update_course(course)
    except Exception as e:
        service.update_status(course_id, "failed", f"导入失败：{e}")
        return
    _process_course(course_id)


@router.post("/import", response_model=CourseCreateResponse)
def import_course(payload: ImportRequest, background_tasks: BackgroundTasks):
    """通过视频链接导入（yt-dlp 下载），后台下载+处理。"""
    service = CourseService()
    course = service.create_course(title=payload.title or "导入中…", video_path="", file_hash=None)
    background_tasks.add_task(_import_course, course.id, payload.url)
    return CourseCreateResponse(
        id=course.id,
        title=course.title,
        status=course.status,
        created_at=course.created_at,
    )


@router.get("/{course_id}", response_model=CourseDetail)
def get_course(course_id: int, request: Request):
    """获取课程详情。"""
    service = CourseService()
    course = service.get_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")

    return CourseDetail(
        id=course.id,
        title=course.title,
        video_url=_get_video_url(course_id, request),
        duration=course.duration,
        status=course.status,
        status_message=course.status_message,
        progress_percent=course.progress_percent,
        created_at=course.created_at,
        updated_at=course.updated_at,
    )


@router.get("/{course_id}/video")
def stream_course_video(course_id: int, request: Request):
    """流式返回课程视频，支持 Range 请求。"""
    service = CourseService()
    course = service.get_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")

    video_path = Path(course.video_path)
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="视频文件不存在")

    media_type = _guess_media_type(video_path)
    file_size = video_path.stat().st_size

    def iter_file(start: int = 0, end: int | None = None):
        with open(video_path, "rb") as f:
            f.seek(start)
            remaining = (end - start + 1) if end is not None else (file_size - start)
            chunk_size = settings.video_stream_chunk_size
            while remaining > 0:
                to_read = min(chunk_size, remaining)
                data = f.read(to_read)
                if not data:
                    break
                yield data
                remaining -= len(data)

    range_header = request.headers.get("range")
    if range_header:
        # 仅支持单区间 "bytes=start-end" 或 "bytes=start-"
        try:
            unit, ranges = range_header.split("=")
            if unit.strip().lower() != "bytes":
                raise ValueError("不支持的 Range 单位")
            start_str, end_str = ranges.split("-")
            start = int(start_str)
            end = int(end_str) if end_str else file_size - 1
            if start >= file_size or end >= file_size:
                raise HTTPException(
                    status_code=416,
                    detail="Range 超出文件范围",
                    headers={"Content-Range": f"bytes */{file_size}"},
                )
            content_length = end - start + 1
            headers = {
                "Content-Type": media_type,
                "Content-Length": str(content_length),
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
            }
            return StreamingResponse(
                iter_file(start, end),
                status_code=206,
                media_type=media_type,
                headers=headers,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"无效的 Range 头: {e}") from e

    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(file_size),
    }
    return StreamingResponse(
        iter_file(),
        media_type=media_type,
        headers=headers,
    )


def _format_vtt_time(seconds: float) -> str:
    """秒 -> WebVTT 时间戳 HH:MM:SS.mmm。"""
    if seconds < 0:
        seconds = 0
    ms = int(round((seconds - int(seconds)) * 1000))
    total = int(seconds)
    if ms == 1000:  # 进位（如 1.9995 -> 2.000）
        total += 1
        ms = 0
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


@router.get("/{course_id}/subtitles")
def get_course_subtitles(course_id: int):
    """返回课程字幕（WebVTT 格式），供 <video><track> 显示。"""
    from sqlmodel import select

    from backend.database import engine
    from backend.models import Transcript
    from sqlmodel import Session

    service = CourseService()
    if not service.get_course(course_id):
        raise HTTPException(status_code=404, detail="课程不存在")

    with Session(engine) as session:
        rows = session.exec(
            select(Transcript)
            .where(Transcript.course_id == course_id)
            .order_by(Transcript.start_time)
        ).all()

    lines = ["WEBVTT", ""]
    for t in rows:
        text = (t.text or "").strip()
        if not text:
            continue
        lines.append(f"{_format_vtt_time(t.start_time)} --> {_format_vtt_time(t.end_time)}")
        lines.append(text)
        lines.append("")
    vtt = "\n".join(lines)
    return Response(content=vtt, media_type="text/vtt; charset=utf-8")


@router.get("/{course_id}/chapters")
def list_chapters(course_id: int):
    """返回课程章节速览（首次调用自动生成并缓存）。"""
    from backend.services.chapter_service import ChapterService

    try:
        chapters = ChapterService().list_chapters(course_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return [
        {
            "id": c.id,
            "index": c.index,
            "title": c.title,
            "summary": c.summary,
            "start_time": c.start_time,
            "end_time": c.end_time,
        }
        for c in chapters
    ]


@router.get("/{course_id}/mindmap")
def get_mindmap(course_id: int):
    """返回课程思维导图树（首次调用自动生成并缓存）。"""
    from backend.services.mindmap_service import MindMapService

    try:
        tree = MindMapService().get_or_generate(course_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return tree


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
