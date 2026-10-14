"""
main.py - The FastAPI application (Phase 7: progress tracking and dashboard).

Start it with:   uvicorn main:app --reload --host 127.0.0.1 --port 8000
Swagger UI:      http://127.0.0.1:8000/docs

Normal "def" endpoints are used on purpose: the database library is not async,
and FastAPI runs normal functions in a separate thread safely.
"""
from database import Base, engine
import models
import roadmap_models  # registers the roadmap tables before create_all

Base.metadata.create_all(bind=engine)

import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

import auth
import crud
import schemas
from database import SessionLocal, get_db, init_db
from routers import progress as progress_router
from routers import roadmap as roadmap_router
from seed import seed_database
from services.skill_analyzer import SkillAnalysisError, analyze_skill_gap

APP_TITLE = "AI Personalized Learning & Skill-Gap Platform API"


# ======================================================================
# Startup: create tables, then add starter data (without duplicates)
# ======================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    with SessionLocal() as db:
        added = seed_database(db)
    if any(added.values()):
        print(
            f"Database seeded: {added['careers']} careers, {added['skills']} skills, "
            f"{added['career_skills']} career-skill links added."
        )
    else:
        print("Database ready: starter data already exists, nothing new was added.")
    yield


app = FastAPI(
    title=APP_TITLE,
    version="0.7.0",
    description=(
        "Phase 7 backend. Data is saved in the SQLite file learning.db and stays after restarts. "
        "The skill-gap engine and roadmap generator are rule-based (not machine learning). "
        "To use protected endpoints: call POST /login, copy the access_token, "
        "click the Authorize button, and paste it."
    ),
    lifespan=lifespan,
)

# ======================================================================
# CORS: lets the React dev server (a different address) call this API
# ======================================================================
# Only these addresses may call the API from a browser. We never use "*".
# To allow other addresses, set CORS_ORIGINS="http://example.com,http://other.com"
DEFAULT_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"
allowed_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", DEFAULT_ORIGINS).split(",")
    if origin.strip()
]
if "*" in allowed_origins:
    raise RuntimeError("CORS_ORIGINS must list exact addresses. '*' is not allowed.")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)



# ======================================================================
# Friendly validation errors
# ======================================================================
@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Turns FastAPI's technical 422 error into a short, readable list."""
    problems = []
    for error in exc.errors():
        if error["type"] == "json_invalid":
            problems.append({"field": "body", "message": "The request body is not valid JSON."})
            continue
        parts = [str(part) for part in error["loc"] if part not in ("body", "query", "path")]
        problems.append(
            {
                "field": ".".join(parts) or "request",
                "message": error["msg"].removeprefix("Value error, "),
            }
        )
    return JSONResponse(
        status_code=422,
        content={"detail": "Some of the information you sent is not valid.", "errors": problems},
    )


# ======================================================================
# Helper functions
# ======================================================================
def require_career(db: Session, student: models.Student) -> models.Career:
    """Return the student's chosen career, or explain what to do first."""
    if student.career_id is None:
        raise HTTPException(
            status_code=400,
            detail="Please choose a career goal first (PUT /profile/career).",
        )
    career = crud.get_career_by_id(db, student.career_id)
    if career is None:  # PHASE 5: unknown career
        raise HTTPException(
            status_code=404,
            detail="Your selected career could not be found. Please choose a career again (PUT /profile/career).",
        )
    return career


def require_assessed_career(db: Session, student: models.Student):
    """Return (career, skills, ratings) once every skill is rated, or explain what to do first."""
    career = require_career(db, student)
    skills = crud.get_career_skills(career)
    if not skills:  # PHASE 5: missing career requirements
        raise HTTPException(
            status_code=404,
            detail=f"No skill requirements are set up for {career.career_name}.",
        )
    ratings = crud.get_ratings(db, student)
    if not all(skill["id"] in ratings for skill in skills):
        raise HTTPException(
            status_code=400,
            detail="Please complete your skill assessment first (POST /assessment).",
        )
    return career, skills, ratings


def get_career_for_analysis(db: Session, student: models.Student, career_slug: Optional[str]):
    """
    PHASE 5: which career is analyzed?
      - normally the student's selected career
      - another career ONLY if the student explicitly asks for it (?career_id=...)
    """
    if career_slug:
        career = crud.get_career_by_slug(db, career_slug)
        if career is None:
            raise HTTPException(
                status_code=404,
                detail=f"Career '{career_slug}' was not found. Use GET /careers to see the supported careers.",
            )
    else:
        career = require_career(db, student)

    skills = crud.get_career_skills(career)
    if not skills:
        raise HTTPException(
            status_code=404,
            detail=f"No skill requirements are set up for {career.career_name}.",
        )
    return career, skills


# ======================================================================
# General endpoints
# ======================================================================
@app.get("/", tags=["General"])
def root():
    """Welcome message with useful links."""
    return {
        "message": f"Welcome to the {APP_TITLE}",
        "version": app.version,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["General"])
def health_check(db: Session = Depends(get_db)):
    """Checks that the server AND the database are working."""
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(status_code=503, detail="The database is not available.")
    return {
        "status": "ok",
        "service": APP_TITLE,
        "storage": "SQLite (learning.db)",
        "database": "connected",
        "time": datetime.now(timezone.utc).isoformat(),
    }


# ======================================================================
# Authentication
# ======================================================================
@app.post("/register", response_model=schemas.ProfileResponse, status_code=201, tags=["Authentication"])
def register(data: schemas.RegisterRequest, db: Session = Depends(get_db)):
    """Create a new student account. The password is stored only as a bcrypt hash."""
    student = crud.create_student(
        db,
        name=data.name,
        email=data.email.lower(),
        password_hash=auth.hash_password(data.password),
    )
    if student is None:
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists. Please log in instead.",
        )
    return crud.profile_to_dict(db, student)


@app.post("/login", response_model=schemas.TokenResponse, tags=["Authentication"])
def login(data: schemas.LoginRequest, db: Session = Depends(get_db)):
    """Check email and password. On success, returns a token valid for 60 minutes."""
    student = crud.get_student_by_email(db, data.email.lower())

    # Always do one password check, so wrong-email and wrong-password look the same
    stored_hash = student.password_hash if student else auth.DUMMY_HASH
    password_ok = auth.verify_password(data.password, stored_hash)

    if student is None or not password_ok:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "access_token": auth.create_access_token(student.id),
        "token_type": "bearer",
        "expires_in_minutes": auth.ACCESS_TOKEN_MINUTES,
    }


@app.post("/demo-login", response_model=schemas.TokenResponse, tags=["Authentication"])
def demo_login(db: Session = Depends(get_db)):
    """Authenticate as the demo student (Pravin). Creates demo student in SQLite if needed."""
    demo_email = "pravin@example.com"
    student = crud.get_student_by_email(db, demo_email)
    if student is None:
        student = crud.create_student(
            db,
            name="Pravin",
            email=demo_email,
            password_hash=auth.hash_password("DemoPassword123"),
        )
        if student is None:
            student = crud.get_student_by_email(db, demo_email)

    if student is None:
        raise HTTPException(status_code=500, detail="Could not create demo account.")

    if student.education is None:
        crud.update_profile(db, student, student.name, "Undergraduate - Year 2", 10)

    if student.career_id is None:
        career = crud.get_career_by_slug(db, "full-stack")
        if career:
            crud.set_career(db, student, career)

    return {
        "access_token": auth.create_access_token(student.id),
        "token_type": "bearer",
        "expires_in_minutes": auth.ACCESS_TOKEN_MINUTES,
    }


# ======================================================================
# Student profile and career selection (protected)
# ======================================================================
@app.get("/profile", response_model=schemas.ProfileResponse, tags=["Student Profile"])
def get_profile(db: Session = Depends(get_db), student: models.Student = Depends(auth.get_current_user)):
    """Return the logged-in student's own profile."""
    return crud.profile_to_dict(db, student)


@app.put("/profile", response_model=schemas.ProfileResponse, tags=["Student Profile"])
def update_profile(
    data: schemas.ProfileUpdateRequest,
    db: Session = Depends(get_db),
    student: models.Student = Depends(auth.get_current_user),
):
    """Update name, education level, and weekly study hours."""
    crud.update_profile(db, student, data.name, data.education, data.study_hours_per_week)
    return crud.profile_to_dict(db, student)


@app.put("/profile/career", response_model=schemas.ProfileResponse, tags=["Student Profile"])
def select_career(
    data: schemas.CareerSelectRequest,
    db: Session = Depends(get_db),
    student: models.Student = Depends(auth.get_current_user),
):
    """Choose (or change) the career goal."""
    career = crud.get_career_by_slug(db, data.career_id)
    if career is None:
        raise HTTPException(status_code=404, detail="Career not found.")
    crud.set_career(db, student, career)
    return crud.profile_to_dict(db, student)


# ======================================================================
# Careers (public: this is general information, not personal data)
# ======================================================================
@app.get("/careers", response_model=List[schemas.CareerSummary], tags=["Careers"])
def get_careers(db: Session = Depends(get_db)):
    """List the three supported careers."""
    return [crud.career_summary(career) for career in crud.list_careers(db)]


@app.get("/careers/{career_id}", response_model=schemas.CareerDetail, tags=["Careers"])
def get_career_detail(career_id: str, db: Session = Depends(get_db)):
    """One career with its required skills, target levels, hours, and resources."""
    career = crud.get_career_by_slug(db, career_id)
    if career is None:
        raise HTTPException(
            status_code=404,
            detail=f"Career '{career_id}' was not found. Use GET /careers to see the supported careers.",
        )
    return crud.career_detail(career)


# ======================================================================
# Skill assessment (protected)
# ======================================================================
@app.post("/assessment", response_model=schemas.AssessmentResponse, tags=["Assessment"])
def save_assessment(
    data: schemas.AssessmentRequest,
    db: Session = Depends(get_db),
    student: models.Student = Depends(auth.get_current_user),
):
    """
    Save ratings (1-5) for every skill of the chosen career.
    Calling it again is a reassessment: the new ratings replace the old ones
    (the old ones stay in assessment_history).
    Sending exactly the same ratings again changes nothing.
    """
    career = require_career(db, student)
    required_ids = [skill["id"] for skill in crud.get_career_skills(career)]
    if not required_ids:
        raise HTTPException(
            status_code=404,
            detail=f"No skill requirements are set up for {career.career_name}.",
        )
    sent = {rating.skill_id: rating.level for rating in data.ratings}

    unknown = [skill_id for skill_id in sent if skill_id not in required_ids]
    if unknown:
        raise HTTPException(
            status_code=422,
            detail=f"These skills do not belong to {career.career_name}: {', '.join(unknown)}.",
        )

    missing = [skill_id for skill_id in required_ids if skill_id not in sent]
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Please rate every skill. Missing: {', '.join(missing)}.",
        )

    ordered = [{"skill_id": skill_id, "level": sent[skill_id]} for skill_id in required_ids]

    # PHASE 5: duplicate submission. If nothing changed, do not write anything.
    saved = crud.get_ratings(db, student)
    if all(saved.get(skill_id) == level for skill_id, level in sent.items()):
        return {
            "career_id": career.slug,
            "assessed": True,
            "ratings": ordered,
            "message": "No changes: these ratings are already saved.",
        }

    crud.save_assessment(db, student, sent)
    return {
        "career_id": career.slug,
        "assessed": True,
        "ratings": ordered,
        "message": "Assessment saved.",
    }


@app.get("/assessment", response_model=schemas.AssessmentResponse, tags=["Assessment"])
def get_assessment(db: Session = Depends(get_db), student: models.Student = Depends(auth.get_current_user)):
    """Saved ratings for the chosen career's skills (empty if never assessed)."""
    career = require_career(db, student)
    skills = crud.get_career_skills(career)
    ratings = crud.get_ratings(db, student)
    saved = [
        {"skill_id": skill["id"], "level": ratings[skill["id"]]}
        for skill in skills
        if skill["id"] in ratings
    ]
    return {
        "career_id": career.slug,
        "assessed": len(skills) > 0 and len(saved) == len(skills),
        "ratings": saved,
    }


# ======================================================================
# Skill-gap analysis (protected)
# ======================================================================
@app.get("/skill-gap", response_model=schemas.SkillGapResponse, tags=["Skill-Gap Analysis"])
def get_skill_gap(
    career_id: Optional[str] = Query(
        default=None,
        max_length=50,
        description="Optional. Leave empty to analyze your selected career. "
        "Or name ONE career (full-stack, data-analyst, ai-ml) to compare it with your own ratings.",
    ),
    db: Session = Depends(get_db),
    student: models.Student = Depends(auth.get_current_user),
):
    """
    Rule-based skill-gap analysis of the LOGGED-IN student's own ratings.
    Skills that are not rated yet count as level 0.
    Readiness = sum of min(current, target) / sum of targets x 100.
    """
    career, skills = get_career_for_analysis(db, student, career_id)
    ratings = crud.get_ratings(db, student)  # only THIS student's ratings

    if not any(skill["id"] in ratings for skill in skills):
        raise HTTPException(
            status_code=400,
            detail=(
                f"You have not rated any {career.career_name} skills yet. "
                "Choose this career (PUT /profile/career) and complete the skill assessment (POST /assessment) first."
            ),
        )

    try:
        result = analyze_skill_gap(skills, ratings)
    except SkillAnalysisError as error:
        # Should not happen: the database only allows levels 1-5. This guards against bad data.
        raise HTTPException(status_code=500, detail=f"Saved skill data is not valid: {error}")

    return {"career_id": career.slug, "career_name": career.career_name, **result}


# ======================================================================
# Phase 6 + 7 routers (all protected by login)
#   Roadmap:   POST /roadmap, GET /roadmap/{student_id}, PATCH /roadmap/activities/{id}
#   Progress:  GET /progress/me, GET /dashboard/me, POST /assessments/reassess
# The old POST /roadmap and GET/POST /progress endpoints were replaced by these.
# ======================================================================
app.include_router(roadmap_router.router)
app.include_router(progress_router.router)
