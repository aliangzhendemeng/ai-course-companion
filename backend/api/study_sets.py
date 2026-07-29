"""学习集 API：命名课程组合的 CRUD，用于限定问答范围。"""

from fastapi import APIRouter, HTTPException

from backend.schemas import StudySetCreate, StudySetItem, StudySetUpdate
from backend.services.course_service import CourseService
from backend.services.study_set_service import StudySetService

router = APIRouter()


def _to_item(service: StudySetService, study_set, course_titles: dict[int, str]) -> StudySetItem:
    course_ids = service.get_course_ids(study_set.id)
    return StudySetItem(
        id=study_set.id,
        name=study_set.name,
        course_ids=course_ids,
        course_titles=[course_titles.get(cid, f"课程 {cid}") for cid in course_ids],
        created_at=study_set.created_at,
    )


def _course_titles_map() -> dict[int, str]:
    return {c.id: c.title for c in CourseService().list_courses()}


@router.get("", response_model=list[StudySetItem])
def list_study_sets():
    """列出所有学习集。"""
    service = StudySetService()
    titles = _course_titles_map()
    return [_to_item(service, s, titles) for s in service.list_sets()]


@router.post("", response_model=StudySetItem)
def create_study_set(payload: StudySetCreate):
    """创建学习集。"""
    service = StudySetService()
    try:
        study_set = service.create_set(payload.name, payload.course_ids)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _to_item(service, study_set, _course_titles_map())


@router.patch("/{study_set_id}", response_model=StudySetItem)
def update_study_set(study_set_id: int, payload: StudySetUpdate):
    """更新学习集（重命名 / 整体替换课程）。"""
    service = StudySetService()
    try:
        study_set = service.update_set(study_set_id, name=payload.name, course_ids=payload.course_ids)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _to_item(service, study_set, _course_titles_map())


@router.delete("/{study_set_id}")
def delete_study_set(study_set_id: int):
    """删除学习集（不影响课程本身）。"""
    service = StudySetService()
    if not service.get_set(study_set_id):
        raise HTTPException(status_code=404, detail="学习集不存在")
    service.delete_set(study_set_id)
    return {"message": "已删除"}
