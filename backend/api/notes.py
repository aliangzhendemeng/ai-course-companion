"""笔记/书签 API：按课程列出、新增、编辑、删除。"""

from fastapi import APIRouter, HTTPException

from backend.schemas import NoteCreateRequest, NoteItem, NoteUpdateRequest
from backend.services.note_service import NoteService

router = APIRouter()


def _to_item(n) -> NoteItem:
    return NoteItem(
        id=n.id,
        course_id=n.course_id,
        kind=n.kind,
        content=n.content,
        timestamp=n.timestamp,
        created_at=n.created_at,
        updated_at=n.updated_at,
    )


@router.get("", response_model=list[NoteItem])
def list_notes(course_id: int):
    """列出某课程的全部笔记/书签（按视频时间点升序）。"""
    service = NoteService()
    return [_to_item(n) for n in service.list_notes(course_id)]


@router.post("", response_model=NoteItem, status_code=201)
def create_note(payload: NoteCreateRequest):
    """新增笔记或书签。"""
    service = NoteService()
    try:
        note = service.create(
            course_id=payload.course_id,
            kind=payload.kind,
            content=payload.content,
            timestamp=payload.timestamp,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _to_item(note)


@router.patch("/{note_id}", response_model=NoteItem)
def update_note(note_id: int, payload: NoteUpdateRequest):
    """编辑笔记内容。"""
    service = NoteService()
    try:
        note = service.update(note_id, payload.content)
    except ValueError as e:
        raise HTTPException(status_code=404 if "不存在" in str(e) else 400, detail=str(e))
    return _to_item(note)


@router.delete("/{note_id}", status_code=204)
def delete_note(note_id: int):
    """删除笔记/书签。"""
    service = NoteService()
    try:
        service.delete(note_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
