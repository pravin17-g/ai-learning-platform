"""
crud.py - Create, Read, Update, Delete helpers.

main.py (the endpoints) calls these functions, so database code stays out of the endpoints.
Every student-specific function receives the student that came from the login TOKEN.
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

import models

# The "progress" column is a percentage that follows the status
PROGRESS_BY_STATUS = {"Not Started": 0, "In Progress": 50, "Completed": 100}


# ======================================================================
# CAREERS AND SKILLS (read)
# ======================================================================
def _career_query():
    """Loads a career together with its skills and prerequisites in a few queries."""
    return select(models.Career).options(
        selectinload(models.Career.requirements).options(
            selectinload(models.CareerSkill.skill),
            selectinload(models.CareerSkill.prerequisites),
        )
    )


def list_careers(db: Session) -> List[models.Career]:
    return list(db.scalars(_career_query().order_by(models.Career.id)))


def get_career_by_slug(db: Session, slug: str) -> Optional[models.Career]:
    return db.scalars(_career_query().where(models.Career.slug == slug)).first()


def get_career_by_id(db: Session, career_id: int) -> Optional[models.Career]:
    return db.scalars(_career_query().where(models.Career.id == career_id)).first()


def get_skill_by_slug(db: Session, slug: str) -> Optional[models.Skill]:
    return db.scalars(select(models.Skill).where(models.Skill.slug == slug)).first()


def _requirement_to_dict(link: models.CareerSkill) -> dict:
    """Same dictionary shape as Phase 3, so the services need no changes."""
    prerequisites = sorted(link.prerequisites, key=lambda skill: skill.skill_name)
    return {
        "id": link.skill.slug,
        "name": link.label or link.skill.skill_name,
        "target": link.target_level,
        "priority": link.priority,
        "order": link.display_order,
        "prerequisite": ", ".join(skill.skill_name for skill in prerequisites) or None,
        "prerequisite_ids": [skill.slug for skill in prerequisites],
        "hours_per_level": link.skill.hours_per_level,
        "objective": link.skill.objective,
        "resource": {"title": link.skill.resource_title, "url": link.skill.resource_url},
    }


def get_career_skills(career: models.Career) -> List[dict]:
    """Required skills of a career, in learning order."""
    return [_requirement_to_dict(link) for link in career.requirements]


def career_summary(career: models.Career) -> dict:
    skills = get_career_skills(career)
    return {
        "id": career.slug,
        "name": career.career_name,
        "icon": career.icon,
        "description": career.description,
        "skill_count": len(skills),
        "top_skills": [skill["name"] for skill in skills[:5]],
    }


def career_detail(career: models.Career) -> dict:
    return {
        "id": career.slug,
        "name": career.career_name,
        "icon": career.icon,
        "description": career.description,
        "skills": get_career_skills(career),
    }


# ======================================================================
# STUDENTS (create and read)
# ======================================================================
def create_student(db: Session, name: str, email: str, password_hash: str) -> Optional[models.Student]:
    """CREATE a student. Returns None if the email is already registered."""
    student = models.Student(name=name, email=email, password_hash=password_hash)
    db.add(student)
    try:
        db.commit()
    except IntegrityError:  # the unique email rule was broken
        db.rollback()
        return None
    db.refresh(student)
    return student


def get_student_by_email(db: Session, email: str) -> Optional[models.Student]:
    return db.scalars(select(models.Student).where(models.Student.email == email)).first()


def get_student_by_id(db: Session, student_id: int) -> Optional[models.Student]:
    return db.get(models.Student, student_id)


def update_profile(db: Session, student: models.Student, name: str, education: str, hours: int):
    """UPDATE the profile."""
    student.name = name
    student.education = education
    student.study_hours_per_week = hours
    db.commit()
    db.refresh(student)
    return student


def set_career(db: Session, student: models.Student, career: models.Career):
    """UPDATE the chosen career goal."""
    student.career_id = career.id
    db.commit()
    db.refresh(student)
    return student


# ======================================================================
# SKILL ASSESSMENT (create / update)
# ======================================================================
def get_ratings(db: Session, student: models.Student) -> Dict[str, int]:
    """READ this student's ratings as {skill slug: level}."""
    rows = db.execute(
        select(models.Skill.slug, models.StudentSkill.current_level)
        .join(models.StudentSkill, models.StudentSkill.skill_id == models.Skill.id)
        .where(models.StudentSkill.student_id == student.id)
    ).all()
    return {slug: level for slug, level in rows}


def save_assessment(db: Session, student: models.Student, sent: Dict[str, int]) -> None:
    """
    CREATE new ratings or UPDATE existing ones (reassessment).
    Every submitted rating is also added to assessment_history.
    """
    skills = {
        skill.slug: skill
        for skill in db.scalars(select(models.Skill).where(models.Skill.slug.in_(list(sent))))
    }
    existing = {
        row.skill_id: row
        for row in db.scalars(
            select(models.StudentSkill).where(models.StudentSkill.student_id == student.id)
        )
    }
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    for slug, level in sent.items():
        skill = skills[slug]
        row = existing.get(skill.id)
        if row is None:
            db.add(models.StudentSkill(student_id=student.id, skill_id=skill.id, current_level=level))
        else:
            row.current_level = level
        db.add(
            models.AssessmentHistory(
                student_id=student.id, skill_id=skill.id, level=level, assessed_at=now
            )
        )
    db.commit()


def get_assessed_career_slugs(db: Session, ratings: Dict[str, int]) -> List[str]:
    """A career is 'assessed' when the student has rated EVERY skill of that career."""
    done = []
    for career in list_careers(db):
        needed = {link.skill.slug for link in career.requirements}
        if needed and needed.issubset(ratings):
            done.append(career.slug)
    return sorted(done)


def profile_to_dict(db: Session, student: models.Student) -> dict:
    ratings = get_ratings(db, student)
    return {
        "id": student.id,
        "name": student.name,
        "email": student.email,
        "education": student.education,
        "study_hours_per_week": student.study_hours_per_week,
        "career_id": student.career.slug if student.career else None,
        "assessed_careers": get_assessed_career_slugs(db, ratings),
    }


# ======================================================================
# LEARNING PROGRESS (create / update)
# ======================================================================
def get_activity_status(db: Session, student: models.Student) -> Dict[str, str]:
    """READ this student's activity statuses as {skill slug: status}."""
    rows = db.execute(
        select(models.Skill.slug, models.LearningProgress.status)
        .join(models.LearningProgress, models.LearningProgress.skill_id == models.Skill.id)
        .where(models.LearningProgress.student_id == student.id)
    ).all()
    return {slug: status for slug, status in rows}


def set_progress(db: Session, student: models.Student, skill: models.Skill, status: str) -> None:
    """CREATE the progress row the first time, UPDATE it afterwards."""
    percent = PROGRESS_BY_STATUS[status]
    row = db.get(models.LearningProgress, (student.id, skill.id))
    if row is None:
        db.add(
            models.LearningProgress(
                student_id=student.id, skill_id=skill.id, status=status, progress=percent
            )
        )
    else:
        row.status = status
        row.progress = percent
    db.commit()
