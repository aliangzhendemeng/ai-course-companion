"""导出 API：闪卡/错题导出为文件下载。"""

from fastapi import APIRouter, HTTPException, Response

from backend.services.export_service import (
    VALID_FLASHCARD_FORMATS,
    VALID_WRONG_FORMATS,
    ExportService,
)

router = APIRouter()


def _resolve_scope(course_id: int | None, study_set_id: int | None) -> None:
    if (course_id is None) == (study_set_id is None):
        raise HTTPException(status_code=400, detail="需提供 course_id 或 study_set_id")


def _attachment(filename: str, content: str, media_type: str) -> Response:
    return Response(
        content=content.encode("utf-8"),
        media_type=media_type,
        headers={
            # filename* 用 UTF-8，避免中文文件名乱码
            "Content-Disposition": f"attachment; filename*=UTF-8''{filename}",
        },
    )


@router.get("/flashcards")
def export_flashcards(
    course_id: int | None = None,
    study_set_id: int | None = None,
    fmt: str = "md",
):
    """导出闪卡：md（按熟悉度分组的 Markdown）或 anki（可导入 Anki 的 TSV）。"""
    _resolve_scope(course_id, study_set_id)
    if fmt not in VALID_FLASHCARD_FORMATS:
        raise HTTPException(status_code=400, detail=f"格式应为 {VALID_FLASHCARD_FORMATS}")
    service = ExportService()
    try:
        content = service.export_flashcards(course_id, study_set_id, fmt)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    ext = "txt" if fmt == "anki" else "md"
    media = "text/tab-separated-values; charset=utf-8" if fmt == "anki" else "text/markdown; charset=utf-8"
    return _attachment(f"flashcards.{ext}", content, media)


@router.get("/wrong-questions")
def export_wrong_questions(
    course_id: int | None = None,
    study_set_id: int | None = None,
    fmt: str = "md",
):
    """导出错题本（Markdown）。"""
    _resolve_scope(course_id, study_set_id)
    if fmt not in VALID_WRONG_FORMATS:
        raise HTTPException(status_code=400, detail=f"格式应为 {VALID_WRONG_FORMATS}")
    service = ExportService()
    try:
        content = service.export_wrong_questions(course_id, study_set_id, fmt)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _attachment("wrong-questions.md", content, "text/markdown; charset=utf-8")
