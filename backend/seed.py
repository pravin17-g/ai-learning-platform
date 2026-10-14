"""
seed.py - Loads the starter data from data/career_skills.json into the database.

The JSON can be in either of two layouts:
  OLD (Phase 3):  {"careers": [...], "skills": {...}, "requirements": {...}}
  NEW (Phase 6):  {"proficiency_scale": {...}, "careers": {"Career Name": {"skills": [...]}}}
normalize() turns the NEW layout into the OLD one, so the rest of this file
(and the database tables) stay the same.

Safe to run on every start:
  - a record that already exists (matched by its "slug") is UPDATED, not duplicated
  - a record that is missing is ADDED
Student data is never touched.
"""
import json
import re
from pathlib import Path

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

import models

DATA_FILE = Path(__file__).parent / "data" / "career_skills.json"

# The new JSON has no slug, icon, or description for careers, so they are kept here.
CAREER_META = {
    "Full Stack Developer": {
        "slug": "full-stack",
        "icon": "💻",
        "description": "Build complete web applications: the screens users see, the server that runs the logic, and the database that stores the data.",
    },
    "Data Analyst": {
        "slug": "data-analyst",
        "icon": "📊",
        "description": "Collect, clean, and analyze data, then turn it into charts and reports that help people make better decisions.",
    },
    "AI/ML Engineer": {
        "slug": "ai-ml",
        "icon": "🤖",
        "description": "Prepare data, train and evaluate machine learning models, and get them ready to be used in real applications.",
    },
}


def slugify(name: str) -> str:
    """'HTML & CSS' -> 'html-and-css'"""
    text = name.lower().replace("&", "and")
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def _objective_text(skill: dict) -> str:
    """The learning objective at the target level (or the highest one available)."""
    objectives = sorted(skill.get("learning_objectives") or [], key=lambda o: o["level"])
    if not objectives:
        return f"Learn {skill['name']} to level {skill['target_level']}."
    reachable = [o for o in objectives if o["level"] <= skill["target_level"]]
    return (reachable or objectives)[-1]["text"]


def normalize(raw: dict) -> dict:
    """Return the data in the OLD layout (careers list + skills dict + requirements dict)."""
    # Already the old layout: nothing to do
    if isinstance(raw.get("careers"), list) and "skills" in raw and "requirements" in raw:
        return raw

    careers_in = raw.get("careers")
    if not isinstance(careers_in, dict):
        raise RuntimeError(
            "career_skills.json has an unknown layout. Expected either "
            "'careers' + 'skills' + 'requirements', or 'careers' as a dictionary of career names."
        )

    careers, skills, requirements = [], {}, {}

    for career_name, body in careers_in.items():
        meta = CAREER_META.get(career_name)
        if meta is None:
            raise RuntimeError(
                f"Unknown career '{career_name}' in career_skills.json. "
                f"Add it to CAREER_META in seed.py. Known: {', '.join(CAREER_META)}."
            )
        career_slug = meta["slug"]
        careers.append(
            {
                "id": career_slug,
                "name": career_name,
                "icon": body.get("icon", meta["icon"]),
                "description": body.get("description", meta["description"]),
            }
        )

        rows = []
        for order, skill in enumerate(body.get("skills", []), start=1):
            skill_slug = slugify(skill["name"])
            if skill_slug not in skills:  # each skill is stored ONCE (first career wins)
                skills[skill_slug] = {
                    "name": skill["name"],
                    "category": skill.get("category", "General"),
                    "objective": _objective_text(skill),
                    "hours_per_level": max(1, round(skill["estimated_hours"] / skill["target_level"])),
                    "resource": {
                        "title": skill["resource"]["title"],
                        "url": skill["resource"]["url"],
                    },
                }
            rows.append(
                {
                    "skill_id": skill_slug,
                    "target": skill["target_level"],
                    "priority": skill.get("priority", "Medium"),
                    "order": order,
                    "prerequisites": [slugify(p) for p in skill.get("prerequisites", [])],
                }
            )
        requirements[career_slug] = rows

    return {"careers": careers, "skills": skills, "requirements": requirements}


def _load_json() -> dict:
    with open(DATA_FILE, encoding="utf-8") as file:
        return normalize(json.load(file))


def _check_data(data: dict) -> None:
    """Uses a Pandas table to catch mistakes in the JSON file before saving anything."""
    problems = []
    rows = []

    for career_slug, requirements in data["requirements"].items():
        for req in requirements:
            rows.append(
                {
                    "career": career_slug,
                    "skill": req["skill_id"],
                    "target": req["target"],
                    "priority": req["priority"],
                    "order": req["order"],
                }
            )
            for prerequisite in req.get("prerequisites", []):
                if prerequisite not in data["skills"]:
                    problems.append(f"Unknown prerequisite '{prerequisite}' in career '{career_slug}'.")

    if not rows:
        raise RuntimeError("career_skills.json has no skill requirements at all.")

    table = pd.DataFrame(rows)

    if table.duplicated(subset=["career", "skill"]).any():
        problems.append("A skill is listed twice inside one career.")
    if table.duplicated(subset=["career", "order"]).any():
        problems.append("Two skills share the same order number inside one career.")
    if not table["target"].between(1, 5).all():
        problems.append("A target level is outside the range 1 to 5.")
    if not table["priority"].isin(["High", "Medium", "Low"]).all():
        problems.append("A priority is not High, Medium, or Low.")

    for skill in sorted(set(table["skill"]) - set(data["skills"])):
        problems.append(f"Skill '{skill}' is used by a career but not defined in 'skills'.")
    for slug, info in data["skills"].items():
        if info["hours_per_level"] <= 0:
            problems.append(f"Skill '{slug}' has hours_per_level of 0 or less.")
    for career in data["careers"]:
        if career["id"] not in data["requirements"]:
            problems.append(f"Career '{career['id']}' has no requirements.")

    if problems:
        raise RuntimeError("career_skills.json has problems:\n- " + "\n- ".join(problems))


def seed_database(db: Session) -> dict:
    """Add or update careers, skills, and the career skill matrix. Returns how many rows were ADDED."""
    data = _load_json()
    _check_data(data)
    added = {"careers": 0, "skills": 0, "career_skills": 0}

    # ---------- Skills ----------
    skills = {skill.slug: skill for skill in db.scalars(select(models.Skill))}
    for slug, info in data["skills"].items():
        skill = skills.get(slug)
        if skill is None:
            skill = models.Skill(slug=slug)
            db.add(skill)
            skills[slug] = skill
            added["skills"] += 1
        skill.skill_name = info["name"]
        skill.category = info["category"]
        skill.objective = info["objective"]
        skill.hours_per_level = info["hours_per_level"]
        skill.resource_title = info["resource"]["title"]
        skill.resource_url = info["resource"]["url"]

    # ---------- Careers ----------
    careers = {career.slug: career for career in db.scalars(select(models.Career))}
    for info in data["careers"]:
        career = careers.get(info["id"])
        if career is None:
            career = models.Career(slug=info["id"])
            db.add(career)
            careers[info["id"]] = career
            added["careers"] += 1
        career.career_name = info["name"]
        career.icon = info["icon"]
        career.description = info["description"]

    db.flush()  # gives the new rows their ids

    # ---------- Career skill matrix (target levels, priorities, prerequisites) ----------
    for career_slug, requirements in data["requirements"].items():
        career = careers[career_slug]
        links = {
            link.skill_id: link
            for link in db.scalars(
                select(models.CareerSkill).where(models.CareerSkill.career_id == career.id)
            )
        }
        for req in requirements:
            skill = skills[req["skill_id"]]
            link = links.get(skill.id)
            if link is None:
                link = models.CareerSkill(career_id=career.id, skill_id=skill.id)
                db.add(link)
                added["career_skills"] += 1
            link.target_level = req["target"]
            link.priority = req["priority"]
            link.display_order = req["order"]
            link.label = req.get("label")
            link.prerequisites = [skills[p] for p in req.get("prerequisites", [])]

    db.commit()
    return added