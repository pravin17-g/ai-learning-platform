from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth_deps import get_current_student_id
from database import get_db
from services import roadmap_service as svc
from services.roadmap_generator import CircularDependencyError, UnknownCareerError
from services.student_data import get_student_data

router = APIRouter(tags=["roadmap"])


def _msg(e: Exception) -> str:
    return str(e.args[0]) if e.args else str(e)


class RoadmapRequest(BaseModel):
    student_id: Optional[int] = None  # optional; if sent it must match the logged-in student
    career: Optional[str] = None
    hours_per_day: float = Field(..., ge=0.5, le=12, description="Available study hours per day")
    days_per_week: int = Field(7, ge=1, le=7)
    force_regenerate: bool = False


class ActivityUpdate(BaseModel):
    status: Literal["not_started", "in_progress", "completed"]
    hours_completed: Optional[float] = Field(None, ge=0)


@router.post("/roadmap")
@router.post("/roadmap/generate")
def create_roadmap(req: RoadmapRequest, response: Response, db: Session = Depends(get_db),
                   current: int = Depends(get_current_student_id), data=Depends(get_student_data)):
    if req.student_id is not None and req.student_id != current:
        raise HTTPException(status_code=403, detail="You can only create a roadmap for yourself.")
    career = req.career
    if not career:
        profile = data.profile(db, current) or {}
        career = profile.get("career")
    if not career:
        raise HTTPException(status_code=400, detail="No career specified. Choose a career first.")
    try:
        result, created = svc.create_roadmap(db, current, career, req.hours_per_day,
                                             req.days_per_week, data.levels, req.force_regenerate)
    except UnknownCareerError as e:
        raise HTTPException(status_code=400, detail=_msg(e))
    except CircularDependencyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    response.status_code = 201 if created else 200
    return {**result, "created": created}


@router.get("/roadmap/me")
@router.get("/roadmap/generate")
def get_my_roadmap(career: Optional[str] = Query(None), db: Session = Depends(get_db),
                   current: int = Depends(get_current_student_id), data=Depends(get_student_data)):
    resolved_career = career
    if not resolved_career:
        profile = data.profile(db, current) or {}
        resolved_career = profile.get("career")
    try:
        roadmap = svc.get_active_roadmap(db, current, resolved_career)
    except UnknownCareerError as e:
        raise HTTPException(status_code=400, detail=_msg(e))
    if not roadmap:
        raise HTTPException(status_code=404, detail="No saved roadmap for this student")
    return svc.serialize_roadmap(roadmap)


@router.get("/roadmap/{student_id}")
def get_roadmap(student_id: int, career: Optional[str] = Query(None), db: Session = Depends(get_db),
                current: int = Depends(get_current_student_id)):
    if student_id != current:
        raise HTTPException(status_code=403, detail="You can only view your own roadmap.")
    try:
        roadmap = svc.get_active_roadmap(db, student_id, career)
    except UnknownCareerError as e:
        raise HTTPException(status_code=400, detail=_msg(e))
    if not roadmap:
        raise HTTPException(status_code=404, detail="No saved roadmap for this student")
    return svc.serialize_roadmap(roadmap)


@router.patch("/roadmap/activities/{activity_id}")
def patch_activity(activity_id: int, body: ActivityUpdate, db: Session = Depends(get_db),
                   current: int = Depends(get_current_student_id)):
    try:
        result = svc.update_activity(db, activity_id, body.status, body.hours_completed, student_id=current)
    except svc.ArchivedRoadmapError as e:
        raise HTTPException(status_code=409, detail=str(e))
    if result is None:  # missing OR someone else's: same answer, nothing leaks
        raise HTTPException(status_code=404, detail="Activity not found")
    return result
