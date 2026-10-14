import pytest
from fastapi import FastAPI, Header, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from auth_deps import get_current_student_id
from database import Base, get_db
from routers.progress import router as progress_router
from routers.roadmap import router as roadmap_router
from services import roadmap_service as rs
from services.student_data import StudentData, get_student_data

FS = "Full Stack Developer"
TARGETS = {"HTML & CSS": 3, "JavaScript": 4, "Git & Version Control": 3, "React": 4,
           "Python": 3, "SQL & Databases": 3, "REST API Development": 4}


class FakeData(StudentData):
    """Student 1 and 2 are beginners; student 3 has achieved every target."""

    def __init__(self):
        self.store = {1: {k: 0 for k in TARGETS}, 2: {k: 0 for k in TARGETS}, 3: dict(TARGETS)}
        self.profiles = {1: {"name": "Asha", "career": FS}, 2: {"name": "Ravi", "career": FS},
                         3: {"name": "Meena", "career": FS}}

    def levels(self, db, student_id, career):
        return dict(self.store.get(student_id, {}))

    def save_levels(self, db, student_id, career, levels):
        self.store.setdefault(student_id, {}).update(levels)

    def profile(self, db, student_id):
        return self.profiles.get(student_id)


def H(student_id):
    return {"X-Test-Student": str(student_id)}


def _who(x_test_student: int = Header(1)):
    return x_test_student


def _deny():
    raise HTTPException(status_code=401, detail="Not authenticated")


@pytest.fixture()
def factory():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


@pytest.fixture()
def fake():
    return FakeData()


def build_client(factory, fake, anonymous=False):
    app = FastAPI()
    app.include_router(roadmap_router)
    app.include_router(progress_router)

    def override_db():
        s = factory()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_student_data] = lambda: fake
    app.dependency_overrides[get_current_student_id] = _deny if anonymous else _who
    return TestClient(app)


@pytest.fixture()
def client(factory, fake):
    return build_client(factory, fake)


def make_roadmap(client, student=1, hours=2):
    r = client.post("/roadmap", json={"career": FS, "hours_per_day": hours}, headers=H(student))
    assert r.status_code in (200, 201), r.text
    return r.json()


# ----------------------------------------------------- roadmap API (moved from Phase 6)
def test_api_post_get_patch_flow(client):
    body = {"career": FS, "hours_per_day": 2, "days_per_week": 5}
    r = client.post("/roadmap", json=body, headers=H(1))
    assert r.status_code == 201
    data = r.json()
    for key in ["career", "activities", "recommended_skills", "suggested_sequence",
                "weekly_schedule", "summary", "progress"]:
        assert key in data
    first = data["activities"][0]
    for key in ["learning_objectives", "estimated_hours", "resource", "status"]:
        assert key in first

    assert client.post("/roadmap", json=body, headers=H(1)).status_code == 200  # no duplicate
    got = client.get("/roadmap/1", params={"career": FS}, headers=H(1))
    assert got.status_code == 200 and got.json()["roadmap_id"] == data["roadmap_id"]

    patched = client.patch(f"/roadmap/activities/{first['id']}", json={"status": "completed"}, headers=H(1))
    assert patched.status_code == 200
    assert patched.json()["activities"][0]["status"] == "completed"


def test_api_all_targets_achieved(client):
    data = make_roadmap(client, student=3)
    assert data["activities"] == []
    assert "already achieved" in data["message"]
    assert data["progress"]["percent"] == 0.0 and data["progress"]["is_empty"] is True


def test_api_validation_errors(client):
    assert client.post("/roadmap", json={"career": "Chef", "hours_per_day": 1}, headers=H(1)).status_code == 400
    assert client.post("/roadmap", json={"career": FS, "hours_per_day": 0}, headers=H(1)).status_code == 422
    assert client.post("/roadmap", json={"career": FS, "hours_per_day": 1, "days_per_week": 9},
                       headers=H(1)).status_code == 422


# --------------------------------------------- 1 + 4. completing activities, completion math
def test_compute_progress_math_and_empty_roadmap():
    assert rs.compute_progress([]) == {"total": 0, "completed": 0, "in_progress": 0, "not_started": 0,
                                       "remaining": 0, "percent": 0.0, "is_empty": True}
    p = rs.compute_progress(["completed", "completed", "completed", "in_progress"])
    assert (p["percent"], p["remaining"], p["in_progress"], p["not_started"]) == (75.0, 1, 1, 0)
    assert rs.compute_progress(["completed", "not_started", "not_started"])["percent"] == 33.3


def test_student_can_complete_activity_and_counts_update(client):
    rm = make_roadmap(client)
    first, second = rm["activities"][0], rm["activities"][1]

    r = client.patch(f"/roadmap/activities/{first['id']}", json={"status": "completed"}, headers=H(1))
    assert r.status_code == 200
    prog = r.json()["progress"]
    assert (prog["total"], prog["completed"], prog["percent"]) == (7, 1, 14.3)  # 1/7*100

    client.patch(f"/roadmap/activities/{second['id']}",
                 json={"status": "in_progress", "hours_completed": 2}, headers=H(1))
    me = client.get("/progress/me", headers=H(1)).json()["progress"]
    assert (me["completed"], me["in_progress"], me["not_started"], me["remaining"]) == (1, 1, 5, 6)

    # Moving back to Not Started is allowed and resets hours
    client.patch(f"/roadmap/activities/{first['id']}", json={"status": "not_started"}, headers=H(1))
    assert client.get("/progress/me", headers=H(1)).json()["progress"]["completed"] == 0


# ---------------------------------------- 2. persistence across a simulated backend restart
def test_progress_survives_backend_restart(tmp_path):
    url = f"sqlite:///{tmp_path / 'restart.db'}"
    levels = lambda db, sid, career: {k: 0 for k in TARGETS}

    engine1 = create_engine(url)
    Base.metadata.create_all(engine1)
    s1 = sessionmaker(bind=engine1)()
    data, _ = rs.create_roadmap(s1, 1, FS, 2, 7, levels)
    rs.update_activity(s1, data["activities"][0]["id"], "completed", student_id=1)
    s1.close()
    engine1.dispose()

    engine2 = create_engine(url)  # new engine = new server process, same SQLite file
    s2 = sessionmaker(bind=engine2)()
    saved = rs.serialize_roadmap(rs.get_active_roadmap(s2, 1, FS))
    assert saved["progress"]["completed"] == 1
    assert saved["activities"][0]["status"] == "completed"
    s2.close()


# ------------------------------------------------- 3. dashboard shows actual stored data
def test_dashboard_reflects_stored_assessments(client, fake):
    fake.store[1] = {"HTML & CSS": 3, "JavaScript": 2}
    d = client.get("/dashboard/me", headers=H(1)).json()
    assert d["student"]["name"] == "Asha" and d["career"] == FS
    by = {s["name"]: s for s in d["skills"]}
    assert (by["JavaScript"]["current_level"], by["JavaScript"]["target_level"], by["JavaScript"]["gap"]) == (2, 4, 2)
    assert by["Python"]["assessed"] is False
    assert d["achieved_skills"] == ["HTML & CSS"]
    assert "JavaScript" in d["improvement_skills"]
    assert d["readiness_score"] == 20.8  # (3 + 2) / 24 total target levels
    assert d["roadmap"] is None


def test_dashboard_empty_states(client, fake):
    fake.store[1] = {}
    d = client.get("/dashboard/me", headers=H(1)).json()
    assert d["has_assessments"] is False and d["readiness_score"] == 0.0
    assert len(d["skills"]) == 7 and "assessment" in d["message"].lower()

    fake.profiles[1]["career"] = None
    d = client.get("/dashboard/me", headers=H(1)).json()
    assert d["career"] is None and d["skills"] == [] and "career" in d["message"].lower()


def test_dashboard_shows_roadmap_progress_and_recommendations(client):
    rm = make_roadmap(client)
    client.patch(f"/roadmap/activities/{rm['activities'][0]['id']}", json={"status": "completed"}, headers=H(1))
    d = client.get("/dashboard/me", headers=H(1)).json()
    assert d["roadmap"]["progress"]["percent"] == 14.3
    assert len(d["recommended_activities"]) == 3
    assert d["recommended_activities"][0]["sequence"] == 2  # the completed one is not recommended


# ------------------------------------------------------------------ 5. reassessment
def test_completing_activity_does_not_mark_skill_achieved(client, fake):
    rm = make_roadmap(client)
    js = next(a for a in rm["activities"] if a["skill_name"] == "JavaScript")
    client.patch(f"/roadmap/activities/{js['id']}", json={"status": "completed"}, headers=H(1))
    d = client.get("/dashboard/me", headers=H(1)).json()
    assert d["readiness_score"] == 0.0
    assert "JavaScript" not in d["achieved_skills"]
    assert "JavaScript" in d["needs_reassessment"]
    assert fake.store[1]["JavaScript"] == 0


def test_reassessment_updates_gap_readiness_and_roadmap(client, fake):
    fake.store[1] = {**{k: 0 for k in TARGETS}, "HTML & CSS": 3, "JavaScript": 2}
    before = client.get("/dashboard/me", headers=H(1)).json()
    assert before["readiness_score"] == 20.8
    names = [a["skill_name"] for a in make_roadmap(client)["activities"]]
    assert "JavaScript" in names

    r = client.post("/assessments/reassess", json={"levels": {"JavaScript": 4}}, headers=H(1))
    assert r.status_code == 200
    d = r.json()
    by = {s["name"]: s for s in d["skills"]}
    assert by["JavaScript"]["gap"] == 0 and "JavaScript" in d["achieved_skills"]
    assert d["readiness_score"] == 29.2  # (3 + 4) / 24
    assert d["roadmap_regenerated"] is True
    assert fake.store[1]["JavaScript"] == 4

    new_names = [a["skill_name"] for a in client.get("/progress/me", headers=H(1)).json()["activities"]]
    assert "JavaScript" not in new_names


def test_reassessment_with_unchanged_level_keeps_roadmap(client, fake):
    fake.store[1] = {**{k: 0 for k in TARGETS}, "JavaScript": 2}
    make_roadmap(client)
    r = client.post("/assessments/reassess", json={"levels": {"JavaScript": 2}}, headers=H(1))
    assert r.status_code == 200 and r.json()["roadmap_regenerated"] is False


@pytest.mark.parametrize("payload", [
    {"levels": {}}, {"levels": {"JavaScript": 9}}, {"levels": {"JavaScript": -1}}, {"levels": {"Cooking": 3}},
])
def test_invalid_reassessment_rejected(client, fake, payload):
    r = client.post("/assessments/reassess", json=payload, headers=H(1))
    assert r.status_code in (400, 422)
    assert fake.store[1]["JavaScript"] == 0  # nothing saved


# ------------------------------------------------------------------ 6. access control
def test_students_cannot_access_each_others_progress(client):
    rm = make_roadmap(client, 1)
    act_id = rm["activities"][0]["id"]

    assert client.patch(f"/roadmap/activities/{act_id}", json={"status": "completed"},
                        headers=H(2)).status_code == 404
    assert client.get("/roadmap/1", headers=H(2)).status_code == 403
    assert client.post("/roadmap", json={"student_id": 1, "career": FS, "hours_per_day": 1},
                       headers=H(2)).status_code == 403
    assert client.get("/progress/me", headers=H(2)).status_code == 404  # student 2 has no roadmap

    d2 = client.get("/dashboard/me", headers=H(2)).json()
    assert d2["student"]["name"] == "Ravi" and d2["roadmap"] is None
    assert client.get("/progress/me", headers=H(1)).json()["progress"]["completed"] == 0  # untouched


def test_unauthenticated_requests_are_rejected(factory, fake):
    anon = build_client(factory, fake, anonymous=True)
    calls = [
        ("get", "/dashboard/me", None), ("get", "/progress/me", None), ("get", "/roadmap/1", None),
        ("post", "/roadmap", {"career": FS, "hours_per_day": 1}),
        ("post", "/assessments/reassess", {"levels": {"JavaScript": 3}}),
        ("patch", "/roadmap/activities/1", {"status": "completed"}),
    ]
    for method, url, body in calls:
        r = getattr(anon, method)(url, **({"json": body} if body else {}))
        assert r.status_code == 401, (method, url)


# ------------------------------------------------- invalid updates and missing roadmaps
def test_invalid_progress_updates(client):
    assert client.get("/progress/me", headers=H(1)).status_code == 404  # missing roadmap
    rm = make_roadmap(client, hours=1)
    aid = rm["activities"][0]["id"]
    assert client.patch(f"/roadmap/activities/{aid}", json={"status": "done!"}, headers=H(1)).status_code == 422
    assert client.patch(f"/roadmap/activities/{aid}",
                        json={"status": "in_progress", "hours_completed": -2}, headers=H(1)).status_code == 422
    assert client.patch("/roadmap/activities/999999", json={"status": "completed"},
                        headers=H(1)).status_code == 404

    make_roadmap(client, hours=3)  # a new roadmap archives the old one
    assert client.patch(f"/roadmap/activities/{aid}", json={"status": "completed"},
                        headers=H(1)).status_code == 409
