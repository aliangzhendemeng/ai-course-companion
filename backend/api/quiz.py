"""测验 API：生成、列表、作答判分、错题本、清空。"""

import json

from fastapi import APIRouter, HTTPException

from backend.ai.quiz_generator import QuizGenerationError
from backend.schemas import (
    QuestionDetail,
    QuizAnswerRequest,
    QuizAnswerResponse,
    QuizGenerateRequest,
    QuizGenerateResponse,
    WrongQuestionItem,
)
from backend.services.quiz_service import QuizService

router = APIRouter()


def _to_detail(q, last_answer=None, last_correct=None) -> QuestionDetail:
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
        last_answer=last_answer,
        last_correct=last_correct,
    )


def _to_wrong(q, mastered: bool, wrong_count: int) -> WrongQuestionItem:
    options = json.loads(q.options) if q.options else None
    return WrongQuestionItem(
        id=q.id,
        type=q.type,
        question=q.question,
        options=options,
        answer=q.answer,
        explanation=q.explanation,
        source_course_id=q.source_course_id,
        source_timestamp=q.source_timestamp,
        mastered=mastered,
        wrong_count=wrong_count,
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
    """列出当前题库（未被清空的题），附带每题最近一次作答进度（断点续答）。"""
    if course_id is None and study_set_id is None:
        raise HTTPException(status_code=400, detail="需提供 course_id 或 study_set_id")
    service = QuizService()
    return [_to_detail(q, last_answer, last_correct) for q, last_answer, last_correct in service.list_questions(course_id, study_set_id)]


@router.get("/wrong", response_model=list[WrongQuestionItem])
def list_wrong(course_id: int | None = None, study_set_id: int | None = None):
    """错题本（历史记录）：所有曾答错的题，答对后标"已掌握"不移除。"""
    if course_id is None and study_set_id is None:
        raise HTTPException(status_code=400, detail="需提供 course_id 或 study_set_id")
    service = QuizService()
    return [_to_wrong(q, mastered, cnt) for q, mastered, cnt in service.get_wrong_questions(course_id, study_set_id)]


@router.delete("/wrong")
def clear_wrong(course_id: int | None = None, study_set_id: int | None = None):
    """清空错题本历史（删除该范围全部作答记录，题目保留）。"""
    if course_id is None and study_set_id is None:
        raise HTTPException(status_code=400, detail="需提供 course_id 或 study_set_id")
    service = QuizService()
    n = service.clear_wrong_book(course_id, study_set_id)
    return {"message": f"已清空错题本（{n} 条作答记录）", "deleted": n}


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
    """清空当前题库（软删除：题目 Tab 不再显示，错题本历史保留）。"""
    if course_id is None and study_set_id is None:
        raise HTTPException(status_code=400, detail="需提供 course_id 或 study_set_id")
    service = QuizService()
    n = service.clear(course_id, study_set_id)
    return {"message": f"已清空 {n} 道题", "deleted": n}
