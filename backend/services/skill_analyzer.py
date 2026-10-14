"""
skill_analyzer.py - Rule-based skill-gap engine (Phase 5).

This is a set of fixed rules and one formula. It is NOT machine learning.
Nothing here is trained, and nothing here predicts anything.

Proficiency scale (both for students and for career targets):
    1 = Beginner   2 = Basic   3 = Intermediate   4 = Advanced   5 = Expert
A skill the student has not rated yet is counted as level 0 ("Not assessed").

Rules:
    Gap       = max(0, target - current)
    Status    = gap 0 -> Achieved | gap 1 -> Needs Improvement | gap 2+ -> Skill Gap
    Readiness = sum of min(current, target) / sum of targets x 100   (rounded to a whole number)

Readiness is an indicator based on the skills the student rated.
It is NOT a validated measure of employability or job readiness.
"""
from typing import Dict, List, Optional

# ---------- The proficiency scale ----------
LEVEL_NAMES = {1: "Beginner", 2: "Basic", 3: "Intermediate", 4: "Advanced", 5: "Expert"}
MIN_LEVEL = 1
MAX_LEVEL = 5
MISSING_LEVEL = 0  # used for a skill the student has not rated

# ---------- Status names ----------
STATUS_ACHIEVED = "Achieved"
STATUS_IMPROVE = "Needs Improvement"
STATUS_GAP = "Skill Gap"

METHOD_TEXT = "Rule-based comparison of current and target levels (not machine learning)"
READINESS_NOTE = (
    "Readiness is an indicator based on the skills you rated. "
    "It is not a validated measure of employability or job readiness."
)


class SkillAnalysisError(ValueError):
    """Raised when the data given to the engine is not valid."""


# ======================================================================
# Validation
# ======================================================================
def is_valid_level(value) -> bool:
    """True only for whole numbers from 1 to 5. (True/False, 3.5 and "4" are rejected.)"""
    return isinstance(value, int) and not isinstance(value, bool) and MIN_LEVEL <= value <= MAX_LEVEL


def validate_level(value, description: str) -> int:
    if not is_valid_level(value):
        raise SkillAnalysisError(
            f"{description} must be a whole number from 1 (Beginner) to 5 (Expert), but got {value!r}."
        )
    return value


def level_name(level: int) -> str:
    return LEVEL_NAMES.get(level, "Not assessed")


# ======================================================================
# The rules
# ======================================================================
def calculate_gap(target: int, current: int) -> int:
    """Skill Gap = max(0, Target Level - Current Level)."""
    return max(0, target - current)


def get_status(gap: int) -> str:
    """Gap 0 -> Achieved, gap 1 -> Needs Improvement, gap greater than 1 -> Skill Gap."""
    if gap == 0:
        return STATUS_ACHIEVED
    if gap == 1:
        return STATUS_IMPROVE
    return STATUS_GAP


def calculate_readiness(points_earned: int, points_possible: int) -> int:
    """
    Readiness (%) = points_earned / points_possible x 100, rounded half up.
    If there are no points to earn (empty requirements) the answer is 0, never a crash.

    Whole-number maths is used so rounding is exact:
    (earned x 200 + possible) // (possible x 2)  equals  round-half-up(earned x 100 / possible)
    """
    if points_possible <= 0:
        return 0
    return (points_earned * 200 + points_possible) // (points_possible * 2)


def _explain(name: str, current: int, target: int, gap: int, assessed: bool) -> str:
    """One plain-English sentence that shows how the result was reached."""
    if not assessed:
        return (
            f"{name}: not assessed yet, so it counts as 0. "
            f"The target is level {target} ({level_name(target)})."
        )
    if gap == 0:
        return (
            f"{name}: your level {current} ({level_name(current)}) "
            f"meets the target of level {target} ({level_name(target)})."
        )
    unit = "level" if gap == 1 else "levels"
    return (
        f"{name}: your level {current} ({level_name(current)}) is {gap} {unit} below "
        f"the target of level {target} ({level_name(target)})."
    )


# ======================================================================
# The engine
# ======================================================================
def analyze_skill_gap(skills: List[dict], ratings: Optional[Dict[str, int]]) -> dict:
    """
    skills  = the career's required skills. Each needs: id, name, target, priority
              (this is the shape crud.get_career_skills() returns).
    ratings = the student's ratings, like {"html": 4, "css": 3}.
              A skill that is missing from this dictionary counts as level 0.
              Ratings for skills outside this career are ignored.

    Raises SkillAnalysisError if a rating or a target is not a whole number from 1 to 5,
    or if the same skill is listed twice.
    An empty skills list is safe: it returns a readiness of 0 and no skills.
    """
    ratings = ratings or {}

    skill_ids = [skill["id"] for skill in skills]
    repeated = sorted({skill_id for skill_id in skill_ids if skill_ids.count(skill_id) > 1})
    if repeated:
        raise SkillAnalysisError("These skills are listed twice: " + ", ".join(repeated) + ".")

    items = []
    points_earned = 0
    points_possible = 0

    for skill in skills:
        name = skill["name"]
        target = validate_level(skill["target"], f"The target level for {name}")

        rating = ratings.get(skill["id"])
        if rating is None:
            current, assessed = MISSING_LEVEL, False
        else:
            current = validate_level(rating, f"Your rating for {name}")
            assessed = True

        gap = calculate_gap(target, current)
        points_earned += min(current, target)  # being above the target earns no extra points
        points_possible += target

        items.append(
            {
                "skill_id": skill["id"],
                "name": name,
                "priority": skill["priority"],
                "current": current,
                "target": target,
                "gap": gap,
                "status": get_status(gap),
                "assessed": assessed,
                "current_name": level_name(current),
                "target_name": level_name(target),
                "explanation": _explain(name, current, target, gap, assessed),
            }
        )

    assessed_count = sum(1 for item in items if item["assessed"])

    return {
        "readiness_score": calculate_readiness(points_earned, points_possible),
        "points_earned": points_earned,
        "points_possible": points_possible,
        "total_skills": len(items),
        "assessed_count": assessed_count,
        "unassessed_count": len(items) - assessed_count,
        "assessment_complete": len(items) > 0 and assessed_count == len(items),
        "achieved_count": sum(1 for item in items if item["status"] == STATUS_ACHIEVED),
        "needs_improvement_count": sum(1 for item in items if item["status"] == STATUS_IMPROVE),
        "skill_gap_count": sum(1 for item in items if item["status"] == STATUS_GAP),
        "skills": items,
        "method": METHOD_TEXT,
        "readiness_note": READINESS_NOTE,
    }
