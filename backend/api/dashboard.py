"""掌握度仪表盘 API。"""

from fastapi import APIRouter

from backend.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("")
def dashboard():
    """返回全局学习掌握度统计。"""
    return DashboardService().dashboard()
