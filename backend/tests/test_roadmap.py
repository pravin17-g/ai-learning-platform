import random

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base
from roadmap_models import LearningRoadmap
from services import roadmap_service as svc
from services.roadmap_generator import (
    CircularDependencyError, generate_roadmap, load_career_data, validate_dependencies,
)

FS = "Full Stack Developer"
FS_TARGETS = {"HTML & CSS": 3, "JavaScript": 4, "Git & Version Control": 3, "React": 4,
              "Python": 3, "SQL & Databases": 3, "REST API Development": 4}
CAREERS = list(load_career_data()["careers"])


def order_of(plan):
    return [a["skill_name"] for a in plan["activities"]]


# ---------------------------------------------------------------- student types
def test_beginner_gets_all_skills_from_scratch():
    plan = generate_roadmap(FS, {k: 0 for k in FS_TARGETS}, 2)
    assert set(order_of(plan)) == set(FS_TARGETS)
    assert plan["summary"]["total_hours"] == 183
    assert not plan["missing_assessments"]


def test_intermediate_skips_intro_and_reduces_hours():
    levels = {"HTML & CSS": 3, "JavaScript": 2, "Git & Version Control": 2, "React": 1,
              "Python": 2, "SQL & Databases": 1, "REST API Development": 0}
    plan = generate_roadmap(FS, levels, 2)
    assert "HTML & CSS" not in order_of(plan)  # already at target
    js = next(a for a in plan["activities"] if a["skill_name"] == "JavaScript")
    assert js["estimated_hours"] == 20  # 40h * 2/4 levels remaining
    assert js["introductory_skipped"] is True
    assert "Use variables, data types, control flow and functions" not in js["learning_objectives"]
    assert len(js["learning_objectives"]) == 2  # only level 3 and 4 objectives remain


def test_advanced_student_has_short_roadmap():
    levels = dict(FS_TARGETS)
    levels["React"] = 3
    levels["REST API Development"] = 3
    plan = generate_roadmap(FS, levels, 1)
    assert set(order_of(plan)) == {"React", "REST API Development"}
    # React 35h/4 = 8.75 -> 9.0 ; REST 30h/4 = 7.5 (each rounded up to a half hour)
    assert plan["summary"]["total_hours"] == 16.5
    assert all(a["gap"] == 1 for a in plan["activities"])


def test_all_targets_achieved_returns_empty_roadmap():
    plan = generate_roadmap(FS, dict(FS_TARGETS), 2)
    assert plan["activities"] == []
    assert plan["weekly_schedule"] == []
    assert "already achieved" in plan["message"]
    assert plan["summary"]["total_hours"] == 0


def test_missing_assessments_flagged():
    plan = generate_roadmap(FS, {"HTML & CSS": 3}, 2)
    assert "HTML & CSS" not in order_of(plan)
    assert "JavaScript" in plan["missing_assessments"]
    assert any("Not assessed" in w for w in plan["warnings"])
    assert all(a["unassessed"] for a in plan["activities"])


def test_no_assessments_at_all_warns_but_still_generates():
    plan = generate_roadmap(FS, {}, 2)
    assert len(plan["activities"]) == len(FS_TARGETS)
    assert any("No skill assessments" in w for w in plan["warnings"])


# ------------------------------------------------------------------ study hours
def test_study_hours_change_duration_not_content():
    levels = {k: 0 for k in FS_TARGETS}
    slow = generate_roadmap(FS, levels, 1, 7)
    fast = generate_roadmap(FS, levels, 3, 7)
    assert order_of(slow) == order_of(fast)
    assert slow["summary"]["weekly_hours"] == 7  # 1h/day -> ~7h/week
    assert len(slow["weekly_schedule"]) > len(fast["weekly_schedule"])
    assert any("weeks" in w for w in slow["warnings"])  # 183h at 7h/week is a long plan


def test_schedule_never_exceeds_daily_capacity_and_covers_all_hours():
    plan = generate_roadmap(FS, {k: 0 for k in FS_TARGETS}, 1.5, 5)
    scheduled = 0
    for week in plan["weekly_schedule"]:
        assert len(week["days"]) <= 5
        for day in week["days"]:
            assert day["hours"] <= 1.5 + 1e-9
            scheduled += day["hours"]
    assert scheduled == pytest.approx(plan["summary"]["total_hours"])
    assert plan["summary"]["estimated_weeks_max"] >= plan["summary"]["estimated_weeks_min"]


def test_invalid_study_input_rejected():
    with pytest.raises(ValueError):
        generate_roadmap(FS, {}, 0)
    with pytest.raises(ValueError):
        generate_roadmap(FS, {}, 1, 8)


# ----------------------------------------------------------- prerequisite order
@pytest.mark.parametrize("career", CAREERS)
def test_prerequisites_always_before_dependents(career):
    skills = load_career_data()["careers"][career]["skills"]
    prereqs = {s["name"]: s["prerequisites"] for s in skills}
    rng = random.Random(42)
    for _ in range(200):
        levels = {s["name"]: rng.randint(0, 5) for s in skills}
        plan = generate_roadmap(career, levels, 2)
        position = {a["skill_name"]: i for i, a in enumerate(plan["activities"])}
        for name, i in position.items():
            for p in prereqs[name]:
                if p in position:  # prerequisite still needed
                    assert position[p] < i, f"{p} must come before {name} for levels {levels}"


def test_known_prerequisite_chain():
    plan = generate_roadmap("Data Analyst", {}, 2)
    pos = {n: i for i, n in enumerate(order_of(plan))}
    assert pos["Python"] < pos["Data Cleaning with pandas"] < pos["Data Visualization"]
    assert pos["Statistics & Probability"] < pos["Exploratory Data Analysis"]


def test_circular_dependency_detected():
    skills = [
        {"name": "A", "prerequisites": ["B"]},
        {"name": "B", "prerequisites": ["C"]},
        {"name": "C", "prerequisites": ["A"]},
    ]
    with pytest.raises(CircularDependencyError) as exc:
        validate_dependencies(skills)
    assert "A" in str(exc.value) and "->" in str(exc.value)


def test_self_dependency_and_unknown_prerequisite_detected():
    with pytest.raises(CircularDependencyError):
        validate_dependencies([{"name": "A", "prerequisites": ["A"]}])
    with pytest.raises(ValueError):
        validate_dependencies([{"name": "A", "prerequisites": ["Z"]}])


def test_generator_rejects_cyclic_career_data():
    skill = lambda n, p: {"name": n, "target_level": 2, "prerequisites": [p], "estimated_hours": 4,
                          "learning_objectives": [], "resource": {"title": "t", "url": "u"}}
    bad = {"careers": {"X": {"skills": [skill("A", "B"), skill("B", "A")]}}}
    with pytest.raises(CircularDependencyError):
        generate_roadmap("X", {}, 1, career_data=bad)


def test_all_shipped_career_data_is_valid():
    for name, career in load_career_data()["careers"].items():
        validate_dependencies(career["skills"])
        for s in career["skills"]:
            assert s["resource"]["url"].startswith("https://")
            assert 1 <= s["target_level"] <= 5
            assert s["estimated_hours"] > 0
            assert s["learning_objectives"], f"{name}/{s['name']} has no objectives"


# ------------------------------------------------------------------ persistence
@pytest.fixture()
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


def provider_for(levels):
    return lambda db, student_id, career: levels


def test_roadmap_saved_and_retrievable(db):
    levels = {k: 0 for k in FS_TARGETS}
    data, created = svc.create_roadmap(db, 1, FS, 2, 7, provider_for(levels))
    assert created is True
    saved = svc.serialize_roadmap(svc.get_active_roadmap(db, 1, FS))
    assert saved["roadmap_id"] == data["roadmap_id"]
    assert [a["skill_name"] for a in saved["activities"]] == data["suggested_sequence"]
    assert saved["weekly_schedule"] == data["weekly_schedule"]


def test_same_request_does_not_duplicate(db):
    levels = {k: 0 for k in FS_TARGETS}
    first, c1 = svc.create_roadmap(db, 1, FS, 2, 7, provider_for(levels))
    second, c2 = svc.create_roadmap(db, 1, FS, 2, 7, provider_for(levels))
    assert (c1, c2) == (True, False)
    assert first["roadmap_id"] == second["roadmap_id"]
    assert db.query(LearningRoadmap).count() == 1


def test_changed_hours_archives_old_and_keeps_single_active(db):
    levels = {k: 0 for k in FS_TARGETS}
    svc.create_roadmap(db, 1, FS, 1, 7, provider_for(levels))
    svc.create_roadmap(db, 1, FS, 3, 7, provider_for(levels))
    assert db.query(LearningRoadmap).count() == 2
    assert db.query(LearningRoadmap).filter_by(is_active=True).count() == 1
    assert svc.get_active_roadmap(db, 1, FS).hours_per_day == 3


def test_progress_preserved_and_completion_does_not_raise_skill_level(db):
    levels = {k: 0 for k in FS_TARGETS}
    data, _ = svc.create_roadmap(db, 1, FS, 2, 7, provider_for(levels))
    acts = {a["skill_name"]: a for a in data["activities"]}
    svc.update_activity(db, acts["Python"]["id"], "completed")
    svc.update_activity(db, acts["Git & Version Control"]["id"], "in_progress", 3)

    # Same assessments -> identical inputs -> nothing regenerated, nothing silently "achieved"
    same, created = svc.create_roadmap(db, 1, FS, 2, 7, provider_for(levels))
    assert created is False and same["roadmap_id"] == data["roadmap_id"]

    # Changing study hours regenerates; the unchanged assessed gap keeps progress
    again, created = svc.create_roadmap(db, 1, FS, 3, 7, provider_for(levels))
    assert created is True
    by = {a["skill_name"]: a for a in again["activities"]}
    assert by["Python"]["status"] == "completed"  # still listed: the assessment still shows a gap
    assert by["Git & Version Control"]["status"] == "in_progress"
    assert by["Git & Version Control"]["hours_completed"] == 3
    scheduled = {s["skill"] for w in again["weekly_schedule"] for d in w["days"] for s in d["sessions"]}
    assert "Python" not in scheduled  # finished work is not scheduled again
    assert again["progress"]["completed"] == 1


def test_force_regenerate_creates_new_record(db):
    levels = {k: 0 for k in FS_TARGETS}
    svc.create_roadmap(db, 1, FS, 2, 7, provider_for(levels))
    _, created = svc.create_roadmap(db, 1, FS, 2, 7, provider_for(levels), force=True)
    assert created is True
    assert db.query(LearningRoadmap).filter_by(is_active=True).count() == 1


def test_students_are_isolated(db):
    svc.create_roadmap(db, 1, FS, 2, 7, provider_for({}))
    assert svc.get_active_roadmap(db, 2, FS) is None
