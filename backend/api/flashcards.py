"""闪卡 API：生成、列表、熟悉度标记、统计、清空。"""

from fastapi import APIRouter, HTTPException

from backend.ai.quiz_generator import QuizGenerationError
from backend.schemas import (
    FlashcardFamiliarityRequest,
    FlashcardGenerateRequest,
    FlashcardGenerateResponse,
    FlashcardItem,
    FlashcardReviewRequest,
    FlashcardStats,
)
from backend.services.flashcard_service import FlashcardService

router = APIRouter()


def _to_item(c) -> FlashcardItem:
    return FlashcardItem(
        id=c.id,
        front=c.front,
        back=c.back,
        familiarity=c.familiarity,
        source_course_id=c.source_course_id,
        source_timestamp=c.source_timestamp,
        # 旧卡迁移加列时 SM-2 字段可能为 NULL，兜底默认值
        ease=c.ease if c.ease is not None else 2.5,
        interval_days=c.interval_days or 0,
        repetitions=c.repetitions or 0,
        due_date=c.due_date or c.created_at,
        last_reviewed_at=c.last_reviewed_at,
    )


@router.post("/generate", response_model=FlashcardGenerateResponse)
def generate_flashcards(payload: FlashcardGenerateRequest):
    """生成闪卡（追加式）。"""
    service = FlashcardService()
    try:
        generated, total = service.generate(
            course_id=payload.course_id,
            study_set_id=payload.study_set_id,
            count=payload.count,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except QuizGenerationError as e:
        raise HTTPException(status_code=502, detail=f"生成失败：{e}")
    return FlashcardGenerateResponse(generated=generated, total=total)


@router.get("", response_model=list[FlashcardItem])
def list_flashcards(
    course_id: int | None = None,
    study_set_id: int | None = None,
    due_only: bool = False,
):
    """列出某范围的全部闪卡；due_only=True 只返回已到期待复习。"""
    if course_id is None and study_set_id is None:
        raise HTTPException(status_code=400, detail="需提供 course_id 或 study_set_id")
    service = FlashcardService()
    cards = (
        service.due_queue(course_id, study_set_id)
        if due_only
        else service.list_cards(course_id, study_set_id)
    )
    return [_to_item(c) for c in cards]


@router.get("/due", response_model=list[FlashcardItem])
def due_flashcards(course_id: int | None = None, study_set_id: int | None = None):
    """今日待复习队列（已到期）。"""
    if course_id is None and study_set_id is None:
        raise HTTPException(status_code=400, detail="需提供 course_id 或 study_set_id")
    service = FlashcardService()
    return [_to_item(c) for c in service.due_queue(course_id, study_set_id)]


@router.get("/stats", response_model=FlashcardStats)
def flashcard_stats(course_id: int | None = None, study_set_id: int | None = None):
    """熟悉度 + 待复习统计。"""
    if course_id is None and study_set_id is None:
        raise HTTPException(status_code=400, detail="需提供 course_id 或 study_set_id")
    service = FlashcardService()
    data = service.stats(course_id, study_set_id)
    data["due"] = service.due_count(course_id, study_set_id)
    return FlashcardStats(**data)


@router.patch("/{flashcard_id}", response_model=FlashcardItem)
def set_familiarity(flashcard_id: int, payload: FlashcardFamiliarityRequest):
    """标记三档熟悉度。"""
    service = FlashcardService()
    try:
        card = service.set_familiarity(flashcard_id, payload.familiarity)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _to_item(card)


@router.post("/{flashcard_id}/review", response_model=FlashcardItem)
def review_flashcard(flashcard_id: int, payload: FlashcardReviewRequest):
    """SM-2 复习：按回忆质量 quality(0-5) 更新调度。"""
    service = FlashcardService()
    try:
        card = service.review(flashcard_id, payload.quality)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _to_item(card)


@router.delete("")
def clear_flashcards(course_id: int | None = None, study_set_id: int | None = None):
    """清空某范围的全部闪卡。"""
    if course_id is None and study_set_id is None:
        raise HTTPException(status_code=400, detail="需提供 course_id 或 study_set_id")
    service = FlashcardService()
    n = service.clear(course_id, study_set_id)
    return {"message": f"已清空 {n} 张闪卡", "deleted": n}
