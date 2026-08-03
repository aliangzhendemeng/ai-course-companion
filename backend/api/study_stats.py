"""学习统计 API：连续学习天数、累计天数、最近活动日。"""

from fastapi import APIRouter

from backend.services.study_stats_service import StudyStatsService

router = APIRouter()


@router.get("")
def study_stats():
    """返回学习打卡统计（streak / total_days / today_active / recent）。"""
    return StudyStatsService().stats()
