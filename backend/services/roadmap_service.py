import hashlib
import json
import math
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

from sqlalchemy.orm import Session

from roadmap_models import LearningRoadmap, RoadmapActivity
from services.roadmap_generator import PLAN_SLOWDOWN, build_weekly_schedule, generate_roadmap, get_career
from services.student_data import fetch_current_levels

LevelsProvider = Callable[[Session, int, str], Dict[str, Optional[float]]]
VALID_STATUSES = {"not_started", "in_progress", "completed"}


class ArchivedRoadmapError(Exception):
    """Raised when someone updates an activity of a superseded roadmap."""


def compute_progress(statuses: List[str]) -> dict:
    """completed / total * 100. An empty roadmap is safe and reports 0.0."""
    total = len(statuses)
    completed = sum(1 for s in statuses if s == "completed")
    in_progress = sum(1 for s in statuses if s == "in_progress")
    return {
        "total": total,
        "completed": completed,
        "in_progress": in_progress,
        "not_started": total - completed - in_progress,
        "remaining": total - completed,  # includes in-progress activities
        "percent": round(completed / total * 100, 1) if total else 0.0,
        "is_empty": total == 0,
    }


def _input_hash(student_id, career, hpd, dpw, levels) -> str:
    payload = {
        "s": student_id, "c": career, "h": hpd, "d": dpw,
        "l": {k.lower(): v for k, v in sorted((levels or {}).items())},
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def serialize_roadmap(r: LearningRoadmap) -> dict:
    plan = json.loads(r.plan_json)
    acts = []
    for a in r.activities:
        acts.append({
            "id": a.id, "sequence": a.sequence, "skill_name": a.skill_name,
            "current_level": a.current_level, "target_level": a.target_level, "gap": a.gap,
            "severity": a.severity, "priority_score": a.priority_score,
            "estimated_hours": a.estimated_hours, "hours_completed": a.hours_completed,
            "status": a.status,
            "learning_objectives": json.loads(a.objectives_json),
            "prerequisites": json.loads(a.prerequisites_json),
            "start_with": a.start_with, "reason": a.reason,
            "resource": {"title": a.resource_title, "url": a.resource_url},
            "unassessed": bool(a.unassessed),
            "completed_at": a.completed_at.isoformat() if a.completed_at else None,
        })
    progress = compute_progress([a["status"] for a in acts])
    summary = dict(plan["summary"])
    summary["progress_percent"] = progress["percent"]  # activity-count based
    sequence = [a["skill_name"] for a in acts]
    return {
        "roadmap_id": r.id, "student_id": r.student_id, "career": r.career,
        "is_active": r.is_active, "created_at": r.created_at.isoformat() if r.created_at else None,
        "hours_per_day": r.hours_per_day, "days_per_week": r.days_per_week,
        "activities": acts, "recommended_skills": sequence, "suggested_sequence": sequence,
        "progress": progress, "summary": summary, "weekly_schedule": plan["weekly_schedule"],
        "missing_assessments": plan["missing_assessments"],
        "warnings": plan["warnings"], "message": plan["message"],
    }


def get_active_roadmap(db: Session, student_id: int, career: Optional[str] = None) -> Optional[LearningRoadmap]:
    q = db.query(LearningRoadmap).filter(LearningRoadmap.student_id == student_id,
                                         LearningRoadmap.is_active.is_(True))
    if career:
        q = q.filter(LearningRoadmap.career == get_career(career)["name"])
    return q.order_by(LearningRoadmap.id.desc()).first()


def _exclude_done_from_schedule(plan: dict, done_skills: set, hpd: float, dpw: int) -> None:
    """Completed activities stay listed but are not scheduled or counted as remaining hours."""
    remaining = [a for a in plan["activities"] if a["skill_name"] not in done_skills]
    total = round(sum(a["estimated_hours"] for a in remaining), 2)
    weekly = plan["summary"]["weekly_hours"]
    plan["weekly_schedule"] = build_weekly_schedule(remaining, hpd, dpw)["weeks"]
    plan["summary"] = dict(
        plan["summary"], total_hours=total,
        estimated_weeks_min=math.ceil(total / weekly) if total else 0,
        estimated_weeks_max=math.ceil(total * PLAN_SLOWDOWN / weekly) if total else 0)


def create_roadmap(db: Session, student_id: int, career: str, hours_per_day: float,
                   days_per_week: int, levels_provider: LevelsProvider = fetch_current_levels,
                   force: bool = False) -> tuple[dict, bool]:
    """
    Returns (roadmap_dict, created). Identical inputs return the existing roadmap.
    Skill levels come ONLY from assessments; completing an activity never raises a level.
    """
    career_name = get_career(career)["name"]
    levels = levels_provider(db, student_id, career_name)
    h = _input_hash(student_id, career_name, hours_per_day, days_per_week, levels)

    existing = get_active_roadmap(db, student_id, career_name)
    if existing and existing.input_hash == h and not force:
        return serialize_roadmap(existing), False

    plan = generate_roadmap(career_name, levels, hours_per_day, days_per_week)
    old_progress: Dict[str, RoadmapActivity] = (
        {a.skill_name: a for a in existing.activities} if existing else {})
    planned_names = {a["skill_name"] for a in plan["activities"]}

    # Progress carry-over:
    #  completed + same level gap       -> stays completed
    #  in progress                      -> stays in progress
    #  completed but assessed level changed -> fresh activity for the remaining gap
    carried: Dict[str, tuple] = {}
    for a in plan["activities"]:
        prev = old_progress.get(a["skill_name"])
        same_gap = (prev is not None and prev.current_level == a["current_level"]
                    and prev.target_level == a["target_level"])
        if same_gap and prev.status == "completed":
            carried[a["skill_name"]] = ("completed", a["estimated_hours"], prev.completed_at)
        elif prev is not None and prev.status == "in_progress":
            carried[a["skill_name"]] = ("in_progress", min(prev.hours_completed, a["estimated_hours"]), None)

    done_skills = {n for n, v in carried.items() if v[0] == "completed"}
    if done_skills:
        _exclude_done_from_schedule(plan, done_skills, hours_per_day, days_per_week)

    for old in db.query(LearningRoadmap).filter(LearningRoadmap.student_id == student_id,
                                                LearningRoadmap.career == career_name,
                                                LearningRoadmap.is_active.is_(True)).all():
        old.is_active = False  # archived, never deleted

    roadmap = LearningRoadmap(
        student_id=student_id, career=career_name, hours_per_day=hours_per_day,
        days_per_week=days_per_week, input_hash=h, is_active=True,
        plan_json=json.dumps({"summary": plan["summary"], "weekly_schedule": plan["weekly_schedule"],
                              "missing_assessments": plan["missing_assessments"],
                              "warnings": plan["warnings"], "message": plan["message"]}),
    )

    seq = 1
    # Finished work for skills that no longer need learning stays visible as completed
    for name, old in old_progress.items():
        if old.status == "completed" and name not in planned_names:
            roadmap.activities.append(RoadmapActivity(
                sequence=seq, skill_name=old.skill_name, current_level=old.current_level,
                target_level=old.target_level, gap=old.gap, severity=old.severity,
                priority_score=old.priority_score, estimated_hours=old.estimated_hours,
                hours_completed=old.estimated_hours, status="completed",
                objectives_json=old.objectives_json, prerequisites_json=old.prerequisites_json,
                start_with=old.start_with, reason=old.reason, resource_title=old.resource_title,
                resource_url=old.resource_url, unassessed=old.unassessed, completed_at=old.completed_at))
            seq += 1

    for a in plan["activities"]:
        status, done, completed_at = carried.get(a["skill_name"], ("not_started", 0, None))
        roadmap.activities.append(RoadmapActivity(
            sequence=seq, skill_name=a["skill_name"], current_level=a["current_level"],
            target_level=a["target_level"], gap=a["gap"], severity=a["severity"],
            priority_score=a["priority_score"], estimated_hours=a["estimated_hours"],
            hours_completed=done, status=status, completed_at=completed_at,
            objectives_json=json.dumps(a["learning_objectives"]),
            prerequisites_json=json.dumps(a["prerequisites"]),
            start_with=a["start_with"], reason=a["reason"],
            resource_title=a["resource"]["title"], resource_url=a["resource"]["url"],
            unassessed=a["unassessed"]))
        seq += 1

    db.add(roadmap)
    db.commit()
    db.refresh(roadmap)
    return serialize_roadmap(roadmap), True


def update_activity(db: Session, activity_id: int, status: str,
                    hours_completed: Optional[float] = None,
                    student_id: Optional[int] = None) -> Optional[dict]:
    """
    Returns None if the activity does not exist OR belongs to another student, so the
    API never reveals other students' data. Raises ArchivedRoadmapError for activities
    of superseded roadmaps. Never changes the student's assessed skill level.
    """
    if status not in VALID_STATUSES:
        raise ValueError(f"status must be one of {sorted(VALID_STATUSES)}")
    q = (db.query(RoadmapActivity)
         .join(LearningRoadmap, LearningRoadmap.id == RoadmapActivity.roadmap_id)
         .filter(RoadmapActivity.id == activity_id))
    if student_id is not None:
        q = q.filter(LearningRoadmap.student_id == student_id)
    act = q.first()
    if not act:
        return None
    if not act.roadmap.is_active:
        raise ArchivedRoadmapError("This roadmap has been replaced. Refresh to see your current roadmap.")

    if status == "completed":
        act.hours_completed = act.estimated_hours
        act.completed_at = datetime.now(timezone.utc)
    elif status == "not_started":
        act.hours_completed = 0
        act.completed_at = None
    else:  # in_progress
        if hours_completed is not None:
            act.hours_completed = min(hours_completed, act.estimated_hours)
        act.completed_at = None
    act.status = status
    db.commit()
    db.refresh(act.roadmap)
    return serialize_roadmap(act.roadmap)
