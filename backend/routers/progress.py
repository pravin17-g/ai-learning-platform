from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth_deps import get_current_student_id
from database import get_db
from services import progress_service as ps
from services import roadmap_service as svc
from services.roadmap_generator import UnknownCareerError
from services.student_data import get_student_data

router = APIRouter(tags=["progress"])


def _msg(e: Exception) -> str:
    return str(e.args[0]) if e.args else str(e)


class ReassessRequest(BaseModel):
    career: Optional[str] = None
    levels: Dict[str, int]  # {"JavaScript": 3}; range is checked in the service


@router.get("/progress/me")
def my_progress(career: Optional[str] = Query(None), db: Session = Depends(get_db),
                student_id: int = Depends(get_current_student_id), data=Depends(get_student_data)):
    """The logged-in student's active roadmap with statuses and progress counts."""
    try:
        roadmap = ps.get_my_roadmap(db, student_id, data, career)
    except ps.NoCareerError:
        raise HTTPException(status_code=404, detail="No roadmap yet. Generate one on the Learning Roadmap page.")
    except UnknownCareerError as e:
        raise HTTPException(status_code=400, detail=_msg(e))
    if not roadmap:
        raise HTTPException(status_code=404, detail="No roadmap yet. Generate one on the Learning Roadmap page.")
    return svc.serialize_roadmap(roadmap)


@router.get("/dashboard/me")
def my_dashboard(career: Optional[str] = Query(None), db: Session = Depends(get_db),
                 student_id: int = Depends(get_current_student_id), data=Depends(get_student_data)):
    try:
        return ps.build_dashboard(db, student_id, data, career)
    except UnknownCareerError as e:
        raise HTTPException(status_code=400, detail=_msg(e))


@router.post("/assessments/reassess")
def reassess(req: ReassessRequest, db: Session = Depends(get_db),
             student_id: int = Depends(get_current_student_id), data=Depends(get_student_data)):
    try:
        return ps.reassess(db, student_id, data, req.levels, req.career)
    except (UnknownCareerError, ValueError) as e:  # ValueError covers NoCareerError and bad levels
        raise HTTPException(status_code=400, detail=_msg(e))
