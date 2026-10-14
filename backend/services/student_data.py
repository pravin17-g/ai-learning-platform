"""
The ONLY file that touches your existing student / assessment tables.
Phase 6/7 code goes through StudentData, so tests can swap it out.
"""
from typing import Dict, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session


# ----------------------------------------------------------------- ADAPT BLOCK
def fetch_current_levels(db: Session, student_id: int, career: str) -> Dict[str, Optional[float]]:
    from models import StudentSkill
    rows = db.query(StudentSkill).filter(StudentSkill.student_id == student_id).all()
    levels = {}
    for r in rows:
        if r.skill:
            levels[r.skill.skill_name] = r.current_level
            levels[r.skill.slug] = r.current_level
    return levels


def save_level(db: Session, student_id: int, skill_name: str, level: int) -> None:
    """Upsert one assessed level. Does not commit (the caller commits)."""
    from models import Skill, StudentSkill
    skill = db.query(Skill).filter(
        (func.lower(Skill.skill_name) == skill_name.lower()) |
        (func.lower(Skill.slug) == skill_name.lower())
    ).first()
    if not skill:
        return
    row = (db.query(StudentSkill)
           .filter(StudentSkill.student_id == student_id,
                   StudentSkill.skill_id == skill.id)
           .first())
    if row:
        row.current_level = level
    else:
        db.add(StudentSkill(student_id=student_id, skill_id=skill.id, current_level=level))


def get_student_profile(db: Session, student_id: int) -> Optional[dict]:
    from models import Student
    s = db.query(Student).filter(Student.id == student_id).first()
    if not s:
        return None

    career_name = None
    if s.career:
        career_name = s.career.career_name

    return {
        "name": s.name,
        "career": career_name,
    }
# -------------------------------------------------------------------------------


class StudentData:
    def levels(self, db, student_id, career):
        return fetch_current_levels(db, student_id, career)

    def save_levels(self, db, student_id, career, levels: Dict[str, int]):
        for skill, level in levels.items():
            save_level(db, student_id, skill, level)
        # ADAPT: if your Phase 5 skill-gap engine stores gap results in a table,
        # recompute and store them here so older pages stay consistent.

    def profile(self, db, student_id):
        return get_student_profile(db, student_id)


def get_student_data() -> StudentData:
    """FastAPI dependency; tests override it."""
    return StudentData()
