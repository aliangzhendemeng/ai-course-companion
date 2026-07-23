"""总结相关 API。"""

from fastapi import APIRouter, HTTPException

from backend.schemas import SummaryResponse
from backend.services.summary_service import SummaryService

router = APIRouter()


@router.get("/{course_id}", response_model=SummaryResponse)
def get_summary(course_id: int):
    """获取课程总结。"""
    service = SummaryService()
    summary = service.get_summary(course_id)
    if not summary:
        raise HTTPException(status_code=404, detail="总结不存在")
    return summary
