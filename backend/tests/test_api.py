"""
test_api.py - End-to-end API tests (Phase 8).

Covers: registration, login, authentication, careers, profile, assessment,
skill-gap, roadmap, progress, database persistence, and student data isolation.
Also runs three student profiles (A beginner, B intermediate, C advanced).

Uses the temporary database from conftest.py. Your real learning.db is never touched.
Run from the backend folder:   python -m pytest tests/test_api.py -v
"""
import pytest
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import sessionmaker

import crud
import models
from database import Base
from seed import seed_database

PASSWORD = "StrongPass123"

# Full Stack Developer ratings. Targets: html4 css4 js4 git3 react4 sql3 node3 rest4 auth3 testing3 (sum 35)
PRIYA = {
    "html": 4, "css": 3, "javascript": 3, "git": 3, "react": 1,
    "sql": 1, "node": 1, "rest": 1, "auth": 1, "testing": 2,
}
STUDENT_A = {skill_id: 1 for skill_id in PRIYA}  # beginner, large gaps everywhere
STUDENT_B = {  # intermediate, some targets reached
    "html": 4, "css": 4, "javascript": 3, "git": 3, "react": 2,
    "sql": 3, "node": 2, "rest": 3, "auth": 2, "testing": 3,
}
STUDENT_C = {  # advanced, almost everything reached
    "html": 5, "css": 4, "javascript": 4, "git": 3, "react": 4,
    "sql": 3, "node": 3, "rest": 3, "auth": 3, "testing": 3,
}


# ======================================================================
# Helpers
# ======================================================================
def signup(client, name="Priya Sharma", email="priya.sharma@example.com"):
    """Register + login. Returns the Authorization header."""
    response = client.post("/register", json={"name": name, "email": email, "password": PASSWORD})
    assert response.status_code == 201, response.text
    response = client.post("/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def assess(client, headers, ratings):
    body = {"ratings": [{"skill_id": s, "level": level} for s, level in ratings.items()]}
    return client.post("/assessment", json=body, headers=headers)


def ready_student(client, ratings, career="full-stack", name="Priya Sharma", email="priya.sharma@example.com"):
    """A student who is registered, has chosen a career, and has finished the assessment."""
    headers = signup(client, name, email)
    assert client.put("/profile/career", json={"career_id": career}, headers=headers).status_code == 200
    assert assess(client, headers, ratings).status_code == 200
    return headers


def roadmap_of(client, headers):
    response = client.post("/roadmap", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def assert_prerequisites_first(items):
    """A skill must never appear before a prerequisite that is also in the roadmap."""
    step_of = {item["name"]: item["step"] for item in items}
    for item in items:
        text = item["prerequisite"] or ""
        for other_name, other_step in step_of.items():
            if other_name != item["name"] and other_name in text:
                assert other_step < item["step"], (
                    f"'{other_name}' (step {other_step}) must come before '{item['name']}' (step {item['step']})"
                )


def assert_steps_are_numbered(items):
    assert [item["step"] for item in items] == list(range(1, len(items) + 1))


# ======================================================================
# General endpoints and careers
# ======================================================================
def test_root_and_health(client):
    assert client.get("/").status_code == 200
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert health.json()["database"] == "connected"


def test_three_careers_with_the_right_skill_counts(client):
    careers = client.get("/careers").json()
    assert {c["id"]: c["skill_count"] for c in careers} == {
        "full-stack": 10, "data-analyst": 9, "ai-ml": 12,
    }


def test_career_detail_and_unknown_career(client):
    detail = client.get("/careers/full-stack").json()
    assert detail["name"] == "Full Stack Developer"
    assert len(detail["skills"]) == 10
    assert all(1 <= skill["target"] <= 5 for skill in detail["skills"])
    assert client.get("/careers/astronaut").status_code == 404


def test_seeding_twice_adds_no_duplicates(session_factory):
    with session_factory() as db:
        added = seed_database(db)
        assert added == {"careers": 0, "skills": 0, "career_skills": 0}
        assert db.scalar(select(func.count()).select_from(models.Career)) == 3
        assert db.scalar(select(func.count()).select_from(models.Skill)) == 25
        assert db.scalar(select(func.count()).select_from(models.CareerSkill)) == 31


# ======================================================================
# Registration, login, authentication
# ======================================================================
def test_register_stores_a_hash_not_the_password(client, session_factory):
    signup(client)
    with session_factory() as db:
        student = db.scalars(select(models.Student)).one()
        assert student.password_hash != PASSWORD
        assert student.password_hash.startswith("$2")  # bcrypt


def test_duplicate_email_is_rejected_even_with_different_capitals(client):
    signup(client)
    response = client.post(
        "/register", json={"name": "Other Person", "email": "PRIYA.SHARMA@example.com", "password": PASSWORD}
    )
    assert response.status_code == 409


@pytest.mark.parametrize(
    "body, field",
    [
        ({"name": "Priya", "email": "a@example.com", "password": "password"}, "password"),  # no number
        ({"name": "Priya", "email": "a@example.com", "password": "Ab1"}, "password"),        # too short
        ({"name": "Priya", "email": "not-an-email", "password": PASSWORD}, "email"),
        ({"name": "P", "email": "a@example.com", "password": PASSWORD}, "name"),
    ],
)
def test_registration_validation(client, body, field):
    response = client.post("/register", json=body)
    assert response.status_code == 422
    assert field in [error["field"] for error in response.json()["errors"]]


def test_login_failures_look_identical(client):
    signup(client)
    wrong_password = client.post("/login", json={"email": "priya.sharma@example.com", "password": "WrongPass999"})
    unknown_email = client.post("/login", json={"email": "nobody@example.com", "password": PASSWORD})
    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()


@pytest.mark.parametrize(
    "method, path",
    [
        ("get", "/profile"), ("put", "/profile"), ("put", "/profile/career"),
        ("get", "/assessment"), ("post", "/assessment"), ("get", "/skill-gap"),
        ("post", "/roadmap"), ("get", "/progress"), ("post", "/progress"),
    ],
)
def test_protected_endpoints_need_a_token(client, method, path):
    assert client.request(method, path, json={}).status_code == 401


def test_garbage_token_is_rejected(client):
    response = client.get("/profile", headers={"Authorization": "Bearer not.a.real.token"})
    assert response.status_code == 401


# ======================================================================
# Profile and career selection
# ======================================================================
def test_profile_read_and_update(client):
    headers = signup(client)
    profile = client.get("/profile", headers=headers).json()
    assert profile["email"] == "priya.sharma@example.com"
    assert profile["career_id"] is None

    update = {"name": "Priya  Sharma", "education": "Undergraduate - Year 2", "study_hours_per_week": 12}
    saved = client.put("/profile", json=update, headers=headers).json()
    assert saved["name"] == "Priya Sharma"  # extra space removed
    assert client.get("/profile", headers=headers).json()["study_hours_per_week"] == 12


@pytest.mark.parametrize(
    "bad",
    [
        {"name": "Priya", "education": "Undergraduate - Year 2", "study_hours_per_week": 0},
        {"name": "Priya", "education": "Undergraduate - Year 2", "study_hours_per_week": 61},
        {"name": "Priya", "education": "Wizard School", "study_hours_per_week": 10},
    ],
)
def test_profile_validation(client, bad):
    headers = signup(client)
    assert client.put("/profile", json=bad, headers=headers).status_code == 422


def test_career_selection(client):
    headers = signup(client)
    ok = client.put("/profile/career", json={"career_id": "data-analyst"}, headers=headers)
    assert ok.status_code == 200 and ok.json()["career_id"] == "data-analyst"
    assert client.put("/profile/career", json={"career_id": "astronaut"}, headers=headers).status_code == 422


# ======================================================================
# Assessment
# ======================================================================
def test_assessment_needs_a_career_first(client):
    headers = signup(client)
    assert assess(client, headers, PRIYA).status_code == 400


def test_assessment_must_cover_every_skill_and_only_that_careers_skills(client):
    headers = signup(client)
    client.put("/profile/career", json={"career_id": "full-stack"}, headers=headers)

    incomplete = {k: v for k, v in PRIYA.items() if k != "react"}
    response = assess(client, headers, incomplete)
    assert response.status_code == 422 and "Missing" in response.json()["detail"]

    response = assess(client, headers, {**PRIYA, "python": 3})  # python is not a Full Stack skill
    assert response.status_code == 422 and "do not belong" in response.json()["detail"]


@pytest.mark.parametrize("bad_level", [0, 6, -2, 3.5, "high", True, None])
def test_invalid_levels_are_rejected_and_nothing_is_saved(client, bad_level):
    headers = signup(client)
    client.put("/profile/career", json={"career_id": "full-stack"}, headers=headers)
    assert assess(client, headers, {**PRIYA, "react": bad_level}).status_code == 422
    assert client.get("/assessment", headers=headers).json()["ratings"] == []


def test_saved_assessment_is_returned(client):
    headers = ready_student(client, PRIYA)
    saved = client.get("/assessment", headers=headers).json()
    assert saved["assessed"] is True
    assert {r["skill_id"]: r["level"] for r in saved["ratings"]} == PRIYA


# ======================================================================
# Skill-gap and roadmap: three student profiles
# ======================================================================
@pytest.mark.parametrize(
    "ratings, readiness, achieved, improve, gaps",
    [
        (STUDENT_A, 29, 0, 0, 10),  # 10 / 35 points
        (STUDENT_B, 83, 5, 4, 1),   # 29 / 35 points
        (STUDENT_C, 97, 9, 1, 0),   # 34 / 35 points
    ],
    ids=["A-beginner", "B-intermediate", "C-advanced"],
)
def test_skill_gap_for_three_profiles(client, ratings, readiness, achieved, improve, gaps):
    headers = ready_student(client, ratings)
    data = client.get("/skill-gap", headers=headers).json()
    assert data["readiness_score"] == readiness
    assert (data["achieved_count"], data["needs_improvement_count"], data["skill_gap_count"]) == (
        achieved, improve, gaps,
    )
    assert "not machine learning" in data["method"]


def test_student_a_gets_a_long_foundational_roadmap(client):
    headers = ready_student(client, STUDENT_A)
    roadmap = roadmap_of(client, headers)
    assert roadmap["total_steps"] == 10
    assert roadmap["total_hours"] == 314  # 24+30+60+12+60+30+36+30+16+16
    assert_steps_are_numbered(roadmap["items"])
    assert_prerequisites_first(roadmap["items"])
    names = [item["name"] for item in roadmap["items"]]
    assert names.index("HTML") < names.index("CSS")
    assert names.index("HTML") < names.index("JavaScript") < names.index("React")
    assert names.index("JavaScript") < names.index("Node.js & Express") < names.index("REST APIs")
    assert names.index("REST APIs") < names.index("Authentication & Security Basics")


def test_student_b_gets_a_focused_roadmap(client):
    headers = ready_student(client, STUDENT_B)
    roadmap = roadmap_of(client, headers)
    assert roadmap["total_steps"] == 5
    assert {item["name"] for item in roadmap["items"]} == {
        "JavaScript", "React", "Node.js & Express", "REST APIs", "Authentication & Security Basics",
    }
    assert roadmap["total_hours"] == 96  # 20+40+18+10+8
    assert_steps_are_numbered(roadmap["items"])
    assert_prerequisites_first(roadmap["items"])


def test_student_c_gets_a_very_short_roadmap(client):
    headers = ready_student(client, STUDENT_C)
    roadmap = roadmap_of(client, headers)
    assert roadmap["total_steps"] == 1
    assert roadmap["items"][0]["name"] == "REST APIs"
    assert roadmap["total_hours"] == 10
    assert roadmap["estimated_weeks"] >= 1


def test_priya_roadmap(client):
    headers = ready_student(client, PRIYA)
    roadmap = roadmap_of(client, headers)
    assert roadmap["total_steps"] == 8
    assert roadmap["total_hours"] == 210
    assert_prerequisites_first(roadmap["items"])


def test_roadmap_hours_follow_gap_times_hours_per_level(client):
    headers = ready_student(client, STUDENT_A)
    hours_per_level = {s["name"]: s["hours_per_level"] for s in client.get("/careers/full-stack").json()["skills"]}
    roadmap = roadmap_of(client, headers)
    for item in roadmap["items"]:
        assert item["gap"] == item["target_level"] - item["current_level"]
        assert item["estimated_hours"] == item["gap"] * hours_per_level[item["name"]]
    assert roadmap["total_hours"] == sum(item["estimated_hours"] for item in roadmap["items"])


def test_beginner_ai_ml_roadmap_respects_prerequisites(client):
    skills = client.get("/careers/ai-ml").json()["skills"]
    ratings = {skill["id"]: 1 for skill in skills}
    headers = ready_student(client, ratings, career="ai-ml")
    roadmap = roadmap_of(client, headers)
    assert roadmap["total_steps"] == 12
    assert roadmap["total_hours"] == 450
    assert_steps_are_numbered(roadmap["items"])
    assert_prerequisites_first(roadmap["items"])


def test_student_who_reached_every_target_has_an_empty_roadmap(client):
    skills = client.get("/careers/full-stack").json()["skills"]
    headers = ready_student(client, {skill["id"]: skill["target"] for skill in skills})
    data = client.get("/skill-gap", headers=headers).json()
    assert data["readiness_score"] == 100
    roadmap = roadmap_of(client, headers)
    assert roadmap["total_steps"] == 0 and roadmap["total_hours"] == 0 and roadmap["items"] == []
    progress = client.get("/progress", headers=headers).json()
    assert progress["total_activities"] == 0 and progress["completion_percent"] == 100


def test_roadmap_and_progress_need_a_finished_assessment(client):
    headers = signup(client)
    client.put("/profile/career", json={"career_id": "full-stack"}, headers=headers)
    assert client.post("/roadmap", headers=headers).status_code == 400
    assert client.get("/progress", headers=headers).status_code == 400
    assert client.get("/skill-gap", headers=headers).status_code == 400


def test_reassessment_changes_gap_and_roadmap(client):
    headers = ready_student(client, PRIYA)
    before = roadmap_of(client, headers)
    assert assess(client, headers, {**PRIYA, "react": 4}).json()["message"] == "Assessment saved."
    after = roadmap_of(client, headers)
    assert after["total_steps"] == before["total_steps"] - 1  # React no longer has a gap
    assert after["total_hours"] == before["total_hours"] - 60
    assert client.get("/skill-gap", headers=headers).json()["readiness_score"] == 66


# ======================================================================
# Progress
# ======================================================================
def test_progress_update_and_totals(client):
    headers = ready_student(client, PRIYA)
    start = client.get("/progress", headers=headers).json()
    assert (start["total_activities"], start["completed"], start["not_started"]) == (8, 0, 8)

    response = client.post("/progress", json={"skill_id": "css", "status": "Completed"}, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert (data["completed"], data["in_progress"], data["not_started"]) == (1, 0, 7)
    assert (data["completion_percent"], data["completed_hours"], data["hours_percent"]) == (13, 10, 5)

    data = client.post("/progress", json={"skill_id": "react", "status": "In Progress"}, headers=headers).json()
    assert (data["completed"], data["in_progress"], data["not_started"]) == (1, 1, 6)

    # the same status shows up in the roadmap
    statuses = {item["skill_id"]: item["status"] for item in roadmap_of(client, headers)["items"]}
    assert statuses["css"] == "Completed" and statuses["react"] == "In Progress"


def test_progress_can_be_changed_back(client):
    headers = ready_student(client, PRIYA)
    client.post("/progress", json={"skill_id": "css", "status": "Completed"}, headers=headers)
    data = client.post("/progress", json={"skill_id": "css", "status": "Not Started"}, headers=headers).json()
    assert data["completed"] == 0


def test_progress_validation(client):
    headers = ready_student(client, PRIYA)
    bad_status = client.post("/progress", json={"skill_id": "css", "status": "Done"}, headers=headers)
    assert bad_status.status_code == 422
    no_gap = client.post("/progress", json={"skill_id": "html", "status": "Completed"}, headers=headers)
    assert no_gap.status_code == 404  # HTML already reached its target
    unknown = client.post("/progress", json={"skill_id": "cooking", "status": "Completed"}, headers=headers)
    assert unknown.status_code == 404


# ======================================================================
# Database persistence and student data isolation
# ======================================================================
def test_progress_percent_column_follows_status(client, session_factory):
    headers = ready_student(client, PRIYA)
    client.post("/progress", json={"skill_id": "css", "status": "Completed"}, headers=headers)
    client.post("/progress", json={"skill_id": "react", "status": "In Progress"}, headers=headers)
    with session_factory() as db:
        rows = {r.skill.slug: (r.status, r.progress) for r in db.scalars(select(models.LearningProgress))}
    assert rows == {"css": ("Completed", 100), "react": ("In Progress", 50)}


def test_assessment_rows_and_history_are_saved(client, session_factory):
    headers = ready_student(client, PRIYA)
    assess(client, headers, {**PRIYA, "react": 3})
    with session_factory() as db:
        assert db.scalar(select(func.count()).select_from(models.StudentSkill)) == 10
        assert db.scalar(select(func.count()).select_from(models.AssessmentHistory)) == 11  # 10 + 1 changed skill


def test_data_survives_a_new_database_connection(tmp_path):
    """Simulates stopping and restarting the backend, using a real database FILE."""
    url = f"sqlite:///{(tmp_path / 'restart_test.db').as_posix()}"

    def open_database():
        engine = create_engine(url, connect_args={"check_same_thread": False})

        @event.listens_for(engine, "connect")
        def foreign_keys_on(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        return engine, sessionmaker(bind=engine, autoflush=False, autocommit=False)

    engine, factory = open_database()
    Base.metadata.create_all(bind=engine)
    with factory() as db:
        seed_database(db)
        student = crud.create_student(db, "Persist Test", "persist@example.com", "fake-hash")
        crud.set_career(db, student, crud.get_career_by_slug(db, "full-stack"))
        crud.save_assessment(db, student, PRIYA)
        crud.set_progress(db, student, crud.get_skill_by_slug(db, "css"), "Completed")
    engine.dispose()  # "stop the server"

    engine, factory = open_database()  # "start the server again"
    with factory() as db:
        added = seed_database(db)  # the startup seed must not duplicate anything
        assert added == {"careers": 0, "skills": 0, "career_skills": 0}
        student = crud.get_student_by_email(db, "persist@example.com")
        assert student is not None
        assert crud.get_ratings(db, student) == PRIYA
        assert crud.get_activity_status(db, student) == {"css": "Completed"}
        assert student.career.slug == "full-stack"
        assert db.scalar(select(func.count()).select_from(models.Skill)) == 25
    engine.dispose()


def test_students_cannot_see_each_others_data(client, session_factory):
    priya = ready_student(client, PRIYA)
    other = ready_student(client, STUDENT_A, name="Second Student", email="second.student@example.com")
    client.post("/progress", json={"skill_id": "css", "status": "Completed"}, headers=priya)

    # different readiness, different roadmaps, different progress
    assert client.get("/skill-gap", headers=priya).json()["readiness_score"] == 57
    assert client.get("/skill-gap", headers=other).json()["readiness_score"] == 29
    assert client.get("/progress", headers=priya).json()["completed"] == 1
    assert client.get("/progress", headers=other).json()["completed"] == 0

    # a student id in the URL is ignored: the student always comes from the token
    me = client.get("/profile?student_id=1", headers=other).json()
    assert me["email"] == "second.student@example.com"
    assert client.get("/skill-gap?student_id=1", headers=other).json()["readiness_score"] == 29

    # in the database every row belongs to exactly one student
    with session_factory() as db:
        counts = dict(
            db.execute(
                select(models.StudentSkill.student_id, func.count()).group_by(models.StudentSkill.student_id)
            ).all()
        )
    assert counts == {1: 10, 2: 10}


def test_one_students_changes_do_not_affect_another(client):
    priya = ready_student(client, PRIYA)
    other = ready_student(client, STUDENT_A, name="Second Student", email="second.student@example.com")
    assess(client, other, STUDENT_C)  # the second student improves a lot
    assert client.get("/skill-gap", headers=priya).json()["readiness_score"] == 57