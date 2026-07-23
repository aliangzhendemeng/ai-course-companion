"""进度相关 API。"""

from fastapi import APIRouter, HTTPException

from backend.services.progress_service import ProgressService

router = APIRouter()


@router.get("/{course_id}")
def get_progress(course_id: int):
    """获取学习进度。"""
    service = ProgressService()
    progress = service.get_progress(course_id)
    if not progress:
        return {"course_id": course_id, "last_position": 0.0}
    return {
        "course_id": progress.course_id,
        "last_position": progress.last_position,
    }


@router.post("/{course_id}")
def update_progress(course_id: int, position: float):
    """更新学习进度。"""
    service = ProgressService()
    progress = service.update_progress(course_id, position)
    return {
        "course_id": progress.course_id,
        "last_position": progress.last_position,
    }
