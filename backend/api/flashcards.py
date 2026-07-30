"""闪卡 API：生成、列表、熟悉度标记、统计、清空。"""

from fastapi import APIRouter, HTTPException

from backend.ai.quiz_generator import QuizGenerationError
from backend.schemas import (
    FlashcardFamiliarityRequest,
    FlashcardGenerateRequest,
    FlashcardGenerateResponse,
    FlashcardItem,
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
def list_flashcards(course_id: int | None = None, study_set_id: int | None = None):
    """列出某范围的全部闪卡。"""
    if course_id is None and study_set_id is None:
        raise HTTPException(status_code=400, detail="需提供 course_id 或 study_set_id")
    service = FlashcardService()
    return [_to_item(c) for c in service.list_cards(course_id, study_set_id)]


@router.get("/stats", response_model=FlashcardStats)
def flashcard_stats(course_id: int | None = None, study_set_id: int | None = None):
    """熟悉度统计。"""
    if course_id is None and study_set_id is None:
        raise HTTPException(status_code=400, detail="需提供 course_id 或 study_set_id")
    service = FlashcardService()
    return FlashcardStats(**service.stats(course_id, study_set_id))


@router.patch("/{flashcard_id}", response_model=FlashcardItem)
def set_familiarity(flashcard_id: int, payload: FlashcardFamiliarityRequest):
    """标记三档熟悉度。"""
    service = FlashcardService()
    try:
        card = service.set_familiarity(flashcard_id, payload.familiarity)
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
