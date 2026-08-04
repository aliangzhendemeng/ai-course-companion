"""学习周报 API。"""

from fastapi import APIRouter

from backend.services.weekly_report_service import WeeklyReportService

router = APIRouter()


@router.get("")
def weekly_report():
    """返回最近 7 天学习情况汇总。"""
    return WeeklyReportService().weekly()
