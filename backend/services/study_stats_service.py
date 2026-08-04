"""学习统计服务：连续学习天数（streak）、累计学习天数、最近活动日。

零侵入设计：不新增打卡表，而是聚合已有学习行为的 created_at：
  问答(ChatMessage) / 做题(QuestionAttempt) / 笔记(Note) / 生成闪卡(Flashcard)
任意一项发生即视为当天有学习活动。
"""

import logging
from datetime import datetime, date, timedelta

from sqlmodel import Session, select

from backend.database import engine
from backend.models import ChatMessage, Flashcard, Note, QuestionAttempt

logger = logging.getLogger(__name__)

# 聚合的学习行为来源表
_ACTIVITY_TABLES = (ChatMessage, QuestionAttempt, Note, Flashcard)
# 前端日历回看天数
RECENT_DAYS = 30


def _to_local_date(dt) -> date | None:
    """datetime -> 本地日期（aware 转本地时区；naive 直接取 date）。"""
    if dt is None:
        return None
    if getattr(dt, "tzinfo", None) is not None:
        return dt.astimezone().date()  # aware -> 系统本地时区
    return dt.date()


class StudyStatsService:
    """学习 streak 与活动统计。"""

    def __init__(self, session: Session | None = None) -> None:
        self.session = session
        self._owns_session = session is None

    def _get_session(self) -> Session:
        if self.session is None:
            return Session(engine)
        return self.session

    def study_dates(self) -> set[date]:
        """所有有学习活动的本地日期集合。"""
        session = self._get_session()
        dates: set[date] = set()
        for model in _ACTIVITY_TABLES:
            try:
                for dt in session.exec(select(model.created_at)).all():
                    d = _to_local_date(dt)
                    if d is not None:
                        dates.add(d)
            except Exception as e:
                logger.warning("聚合 %s 学习日期失败: %s", model.__name__, e)
        if self._owns_session:
            session.close()
        return dates

    def stats(self) -> dict:
        """返回 streak / total_days / today_active / recent（最近30天活动日）。"""
        dates = self.study_dates()
        today = datetime.now().date()

        # streak：今天有活动则从今天起算；否则给一天宽限，从昨天起算（今天还没学不算断）
        start = today if today in dates else today - timedelta(days=1)
        streak = 0
        d = start
        while d in dates:
            streak += 1
            d -= timedelta(days=1)

        recent = sorted(
            (today - timedelta(days=i) for i in range(RECENT_DAYS)),
            reverse=True,
        )
        recent_active = [d.isoformat() for d in recent if d in dates]

        return {
            "streak": streak,
            "total_days": len(dates),
            "today_active": today in dates,
            "recent": recent_active,
        }
