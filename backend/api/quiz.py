"""测验 API：生成、列表、作答判分、清空。"""

import json

from fastapi import APIRouter, HTTPException

from backend.ai.quiz_generator import QuizGenerationError
from backend.schemas import (
    QuestionDetail,
    QuizAnswerRequest,
    QuizAnswerResponse,
    QuizGenerateRequest,
    QuizGenerateResponse,
)
from backend.services.quiz_service import QuizService

router = APIRouter()


def _to_detail(q) -> QuestionDetail:
    options = json.loads(q.options) if q.options else None
    return QuestionDetail(
        id=q.id,
        type=q.type,
        question=q.question,
        options=options,
        answer=q.answer,
        explanation=q.explanation,
        source_course_id=q.source_course_id,
        source_timestamp=q.source_timestamp,
    )


@router.post("/generate", response_model=QuizGenerateResponse)
def generate_quiz(payload: QuizGenerateRequest):
    """生成测验题（追加式）。"""
    service = QuizService()
    try:
        generated, total = service.generate(
            course_id=payload.course_id,
            study_set_id=payload.study_set_id,
            count=payload.count,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except QuizGenerationError as e:
        raise HTTPException(status_code=502, detail=f"出题失败：{e}")
    return QuizGenerateResponse(generated=generated, total=total)


@router.get("", response_model=list[QuestionDetail])
def list_quiz(course_id: int | None = None, study_set_id: int | None = None):
    """列出某范围的全部题。"""
    if course_id is None and study_set_id is None:
        raise HTTPException(status_code=400, detail="需提供 course_id 或 study_set_id")
    service = QuizService()
    return [_to_detail(q) for q in service.list_questions(course_id, study_set_id)]


@router.post("/{question_id}/answer", response_model=QuizAnswerResponse)
def submit_answer(question_id: int, payload: QuizAnswerRequest):
    """作答判分。"""
    service = QuizService()
    try:
        question = service.submit_answer(question_id, payload.answer)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return QuizAnswerResponse(
        question_id=question.id,
        correct=QuizService.is_correct(question, payload.answer),
        answer=question.answer,
        explanation=question.explanation,
    )


@router.delete("")
def clear_quiz(course_id: int | None = None, study_set_id: int | None = None):
    """清空某范围的全部题（用于清空重生成）。"""
    if course_id is None and study_set_id is None:
        raise HTTPException(status_code=400, detail="需提供 course_id 或 study_set_id")
    service = QuizService()
    n = service.clear(course_id, study_set_id)
    return {"message": f"已清空 {n} 道题", "deleted": n}
