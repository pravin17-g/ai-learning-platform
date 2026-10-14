from typing import Dict, Optional

from sqlalchemy.orm import Session

from services import roadmap_service as rs
from services.roadmap_generator import MAX_LEVEL, _clamp_level, _severity_label, get_career
from services.student_data import StudentData


class NoCareerError(ValueError):
    pass


def resolve_career(db: Session, student_id: int, data: StudentData, career: Optional[str] = None) -> str:
    name = career or (data.profile(db, student_id) or {}).get("career")
    if not name:
        raise NoCareerError("No career selected. Choose a career first.")
    return get_career(name)["name"]


def compute_skill_gap(career_name: str, levels: Dict[str, Optional[float]]) -> dict:
    """Rule-based gap using the career_skills.json targets (same source as the roadmap generator)."""
    career = get_career(career_name)
    norm = {k.strip().lower(): v for k, v in (levels or {}).items()}
    rows = []
    for s in career["skills"]:
        raw = norm.get(s["name"].lower())
        assessed = raw is not None
        current = _clamp_level(raw) if assessed else 0
        target = s["target_level"]
        gap = max(target - current, 0)
        rows.append({
            "name": s["name"], "current_level": current, "target_level": target, "gap": gap,
            "achieved": gap == 0, "assessed": assessed,
            "severity": _severity_label(gap / target) if gap else "none",
        })
    total_target = sum(r["target_level"] for r in rows)
    got = sum(min(r["current_level"], r["target_level"]) for r in rows)
    return {
        "skills": rows,
        "readiness_score": round(100 * got / total_target, 1) if total_target else 0.0,
        "achieved_skills": [r["name"] for r in rows if r["achieved"]],
        "improvement_skills": [r["name"] for r in rows if not r["achieved"]],
        "has_assessments": any(r["assessed"] for r in rows),
    }


def build_dashboard(db: Session, student_id: int, data: StudentData, career: Optional[str] = None) -> dict:
    profile = data.profile(db, student_id) or {}
    result = {
        "student": {"id": student_id, "name": profile.get("name")},
        "career": None, "has_assessments": False, "readiness_score": 0.0,
        "skills": [], "achieved_skills": [], "improvement_skills": [], "needs_reassessment": [],
        "roadmap": None, "recommended_activities": [], "message": None,
    }
    name = career or profile.get("career")
    if not name:
        result["message"] = "No career selected yet. Choose a career to see your dashboard."
        return result

    career_name = get_career(name)["name"]
    gap = compute_skill_gap(career_name, data.levels(db, student_id, career_name))
    result.update(career=career_name, **gap)
    if not gap["has_assessments"]:
        result["message"] = "No assessment results yet. Complete the skill assessment to see your readiness."

    roadmap = rs.get_active_roadmap(db, student_id, career_name)
    if roadmap:
        rm = rs.serialize_roadmap(roadmap)
        completed = {a["skill_name"] for a in rm["activities"] if a["status"] == "completed"}
        # Learning finished but target not confirmed: only a new assessment can confirm it
        result["needs_reassessment"] = [n for n in gap["improvement_skills"] if n in completed]
        result["roadmap"] = {"roadmap_id": rm["roadmap_id"], "hours_per_day": rm["hours_per_day"],
                             "days_per_week": rm["days_per_week"], "progress": rm["progress"]}
        result["recommended_activities"] = [
            {"id": a["id"], "sequence": a["sequence"], "skill_name": a["skill_name"],
             "estimated_hours": a["estimated_hours"], "status": a["status"], "resource": a["resource"]}
            for a in rm["activities"] if a["status"] != "completed"][:3]
    return result


def get_my_roadmap(db: Session, student_id: int, data: StudentData, career: Optional[str] = None):
    return rs.get_active_roadmap(db, student_id, resolve_career(db, student_id, data, career))


def reassess(db: Session, student_id: int, data: StudentData, new_levels: Dict[str, int],
             career: Optional[str] = None) -> dict:
    """Validate -> save levels -> refresh roadmap only if levels changed -> return fresh dashboard."""
    career_name = resolve_career(db, student_id, data, career)
    names = {s["name"].lower(): s["name"] for s in get_career(career_name)["skills"]}
    if not new_levels:
        raise ValueError("No skill levels provided.")
    clean: Dict[str, int] = {}
    for skill, level in new_levels.items():
        canonical = names.get(skill.strip().lower())
        if canonical is None:
            raise ValueError(f"Unknown skill for {career_name}: {skill!r}")
        if isinstance(level, bool) or not isinstance(level, int) or not 0 <= level <= MAX_LEVEL:
            raise ValueError(f"Level for {canonical} must be a whole number from 0 to {MAX_LEVEL}.")
        clean[canonical] = level

    data.save_levels(db, student_id, career_name, clean)
    db.commit()

    regenerated = False
    existing = rs.get_active_roadmap(db, student_id, career_name)
    if existing:  # unchanged levels -> same input hash -> no new roadmap
        _, regenerated = rs.create_roadmap(db, student_id, career_name, existing.hours_per_day,
                                           existing.days_per_week, data.levels)
    dash = build_dashboard(db, student_id, data, career_name)
    return {**dash, "roadmap_regenerated": regenerated, "updated_skills": clean}
