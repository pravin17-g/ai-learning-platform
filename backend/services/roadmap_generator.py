"""
Rule-based roadmap generator (Phase 6).

Pure functions only: no database, no network. Persistence lives in roadmap_service.py.
"""
import heapq
import json
import math
from pathlib import Path
from typing import Dict, List, Optional

MAX_LEVEL = 5
DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "career_skills.json"

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
# Spread study days sensibly across the week
STUDY_DAY_PATTERNS = {
    1: [0], 2: [0, 3], 3: [0, 2, 4], 4: [0, 1, 3, 4],
    5: [0, 1, 2, 3, 4], 6: [0, 1, 2, 3, 4, 5], 7: [0, 1, 2, 3, 4, 5, 6],
}
SEVERITY_LEVELS = [(0.75, "critical"), (0.5, "high"), (0.25, "moderate"), (0.0, "low")]
PLAN_SLOWDOWN = 1.25  # upper estimate: real learning is slower than planned
LONG_PLAN_WEEKS = 26


class CircularDependencyError(ValueError):
    pass


class UnknownCareerError(KeyError):
    pass


# ---------------------------------------------------------------- data loading
def load_career_data(path: Path = DATA_FILE) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


SLUG_TO_CAREER_NAME = {
    "full-stack": "Full Stack Developer",
    "data-analyst": "Data Analyst",
    "ai-ml": "AI/ML Engineer",
}


def get_career(name: str, data: Optional[dict] = None) -> dict:
    data = data or load_career_data()
    wanted = (name or "").strip().lower()
    if wanted in SLUG_TO_CAREER_NAME:
        wanted = SLUG_TO_CAREER_NAME[wanted].lower()
    for key, value in data["careers"].items():
        if key.lower() == wanted:
            return {"name": key, **value}
    raise UnknownCareerError(f"Unsupported career: {name!r}. Supported: {list(data['careers'])}")


def validate_dependencies(skills: List[dict]) -> None:
    """Raise if a prerequisite is unknown or the prerequisite graph has a cycle."""
    graph = {s["name"]: list(s.get("prerequisites", [])) for s in skills}
    for name, prereqs in graph.items():
        for p in prereqs:
            if p not in graph:
                raise ValueError(f"Skill {name!r} has unknown prerequisite {p!r}")

    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in graph}

    def visit(node: str, path: List[str]) -> None:
        color[node] = GRAY
        for p in graph[node]:
            if color[p] == GRAY:
                cycle = path[path.index(p):] + [p]
                raise CircularDependencyError("Circular prerequisites: " + " -> ".join(cycle))
            if color[p] == WHITE:
                visit(p, path + [p])
        color[node] = BLACK

    for n in graph:
        if color[n] == WHITE:
            visit(n, [n])


# --------------------------------------------------------------------- helpers
def _clamp_level(v) -> int:
    return int(max(0, min(MAX_LEVEL, round(float(v)))))


def _round_up_half(hours: float) -> float:
    return max(0.5, math.ceil(hours * 2) / 2)


def _severity_label(ratio: float) -> str:
    for threshold, label in SEVERITY_LEVELS:
        if ratio >= threshold:
            return label
    return "low"


def _normalize(levels: Optional[Dict[str, Optional[float]]]) -> Dict[str, Optional[int]]:
    out: Dict[str, Optional[int]] = {}
    for k, v in (levels or {}).items():
        out[k.strip().lower()] = None if v is None else _clamp_level(v)
    return out


# ------------------------------------------------------------ weekly scheduler
def build_weekly_schedule(activities: List[dict], hours_per_day: float,
                          days_per_week: int, max_weeks: int = 104) -> dict:
    """Fill study days in order. Never schedules more than hours_per_day on a day."""
    day_cap = int(round(hours_per_day * 60))  # minutes avoid float drift
    queue = [[a["skill_name"], int(round(a["estimated_hours"] * 60))] for a in activities]
    idx, weeks, truncated = 0, [], False

    while idx < len(queue):
        if len(weeks) >= max_weeks:
            truncated = True
            break
        days, week_minutes = [], 0
        for d in STUDY_DAY_PATTERNS[days_per_week]:
            cap, sessions = day_cap, []
            while cap > 0 and idx < len(queue):
                name, remaining = queue[idx]
                take = min(cap, remaining)
                sessions.append({"skill": name, "hours": round(take / 60, 2)})
                cap -= take
                queue[idx][1] -= take
                if queue[idx][1] == 0:
                    idx += 1
            if sessions:
                used = day_cap - cap
                week_minutes += used
                days.append({"day": DAY_NAMES[d], "hours": round(used / 60, 2), "sessions": sessions})
        weeks.append({
            "week": len(weeks) + 1,
            "total_hours": round(week_minutes / 60, 2),
            "focus": list(dict.fromkeys(s["skill"] for day in days for s in day["sessions"])),
            "days": days,
        })
    return {"weeks": weeks, "truncated": truncated}


# ------------------------------------------------------------------- generator
def generate_roadmap(career_name: str,
                     current_levels: Dict[str, Optional[float]],
                     hours_per_day: float,
                     days_per_week: int = 7,
                     completed_levels: Optional[Dict[str, int]] = None,
                     career_data: Optional[dict] = None) -> dict:
    """
    current_levels  : assessed level per skill (missing key or None = not assessed)
    completed_levels: highest level reached through previously completed roadmap activities
    """
    if not (0 < hours_per_day <= 24):
        raise ValueError("hours_per_day must be between 0 and 24")
    if days_per_week not in STUDY_DAY_PATTERNS:
        raise ValueError("days_per_week must be between 1 and 7")

    career = get_career(career_name, career_data)
    skills = career["skills"]
    validate_dependencies(skills)  # prevents circular / unknown prerequisites

    assessed = _normalize(current_levels)
    completed = _normalize(completed_levels)

    # 1-2. Skill-gap per skill, using the better of assessment and completed learning
    info: Dict[str, dict] = {}
    for i, s in enumerate(skills):
        key = s["name"].lower()
        a, c = assessed.get(key), completed.get(key)
        unassessed = a is None and c is None
        effective = max(a or 0, c or 0)
        target = s["target_level"]
        gap = max(target - effective, 0)
        info[s["name"]] = {"skill": s, "index": i, "effective": effective, "gap": gap,
                           "target": target, "unassessed": unassessed}

    # 3. Exclude skills already at target
    needed = [n for n, v in info.items() if v["gap"] > 0]
    needed_set = set(needed)

    # 4. Dependency graph restricted to needed skills (satisfied prereqs impose no ordering)
    prereqs = {n: [p for p in dict.fromkeys(info[n]["skill"].get("prerequisites", [])) if p in needed_set]
               for n in needed}
    dependents: Dict[str, List[str]] = {n: [] for n in needed}
    for n, ps in prereqs.items():
        for p in ps:
            dependents[p].append(n)

    def reachable(n: str) -> set:
        seen, stack = set(), list(dependents[n])
        while stack:
            d = stack.pop()
            if d not in seen:
                seen.add(d)
                stack.extend(dependents[d])
        return seen

    # 5. Priority: gap severity + how many other needed skills this one unlocks
    score = {}
    for n in needed:
        ratio = info[n]["gap"] / info[n]["target"]
        info[n]["ratio"] = ratio
        score[n] = round(ratio * 100 + 5 * len(reachable(n)), 1)

    # Topological order (Kahn) choosing the highest-priority ready skill each step
    indeg = {n: len(prereqs[n]) for n in needed}
    heap = [(-score[n], info[n]["index"], n) for n in needed if indeg[n] == 0]
    heapq.heapify(heap)
    order: List[str] = []
    while heap:
        _, _, n = heapq.heappop(heap)
        order.append(n)
        for d in dependents[n]:
            indeg[d] -= 1
            if indeg[d] == 0:
                heapq.heappush(heap, (-score[d], info[d]["index"], d))
    if len(order) != len(needed):  # defensive; validate_dependencies should catch this first
        raise CircularDependencyError("Circular prerequisites detected while ordering skills")

    # 6-8. Build ordered activities with time estimate, objectives, resource
    activities = []
    for seq, n in enumerate(order, start=1):
        v, s = info[n], info[n]["skill"]
        eff, target, gap = v["effective"], v["target"], v["gap"]
        hours = _round_up_half(s["estimated_hours"] / target * gap)
        objectives = [o["text"] for o in s["learning_objectives"] if eff < o["level"] <= target]
        unlocks = [d for d in dependents[n]]
        reason = f"Gap of {gap} level(s): {eff} -> {target}."
        if v["unassessed"]:
            reason += " No assessment found, so planned from the beginning."
        if unlocks:
            reason += " Unlocks: " + ", ".join(unlocks) + "."
        activities.append({
            "sequence": seq,
            "skill_name": n,
            "current_level": eff,
            "target_level": target,
            "gap": gap,
            "severity": _severity_label(v["ratio"]),
            "priority_score": score[n],
            "estimated_hours": hours,
            "prerequisites": list(s.get("prerequisites", [])),
            "unmet_prerequisites": prereqs[n],
            "learning_objectives": objectives,
            "start_with": objectives[0] if objectives else None,
            "introductory_skipped": eff >= 1,
            "resource": s["resource"],
            "unassessed": v["unassessed"],
            "reason": reason,
            "status": "not_started",
            "hours_completed": 0,
        })

    schedule = build_weekly_schedule(activities, hours_per_day, days_per_week)
    total_hours = round(sum(a["estimated_hours"] for a in activities), 2)
    weekly_hours = round(hours_per_day * days_per_week, 2)
    weeks_min = math.ceil(total_hours / weekly_hours) if total_hours else 0
    weeks_max = math.ceil(total_hours * PLAN_SLOWDOWN / weekly_hours) if total_hours else 0

    missing = [n for n, v in info.items() if v["unassessed"]]
    warnings = []
    if len(missing) == len(skills):
        warnings.append("No skill assessments were found. This roadmap starts every skill from zero; "
                        "complete the assessment for a more accurate plan.")
    elif missing:
        warnings.append("Not assessed (planned from zero): " + ", ".join(missing) + ".")
    if weeks_min > LONG_PLAN_WEEKS:
        warnings.append(f"This plan needs about {weeks_min}+ weeks at {weekly_hours} h/week. "
                        "Consider more weekly study time or focusing on the first few skills.")
    if schedule["truncated"]:
        warnings.append("Schedule is shown for the first 104 weeks only.")

    message = None
    if not activities:
        message = "All target skills for this career are already achieved. No roadmap activities needed."

    return {
        "career": career["name"],
        "hours_per_day": hours_per_day,
        "days_per_week": days_per_week,
        "activities": activities,
        "recommended_skills": order,
        "suggested_sequence": order,
        "summary": {
            "total_hours": total_hours,
            "weekly_hours": weekly_hours,
            "estimated_weeks_min": weeks_min,
            "estimated_weeks_max": weeks_max,
            "estimate_note": ("Estimates assume you study every planned day. "
                              "Allow up to ~25% extra time for revision and slower topics."),
        },
        "weekly_schedule": schedule["weeks"],
        "missing_assessments": missing,
        "warnings": warnings,
        "message": message,
    }
