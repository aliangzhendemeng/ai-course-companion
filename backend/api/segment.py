"""时间段总结 API。"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.segment_service import SegmentSummaryService

router = APIRouter()


class SegmentSummaryRequest(BaseModel):
    course_id: int
    start: float
    end: float


@router.post("/summarize")
def summarize_segment(payload: SegmentSummaryRequest):
    """总结视频某段时间区间的内容。"""
    service = SegmentSummaryService()
    try:
        result = service.summarize(payload.course_id, payload.start, payload.end)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result
