"""
schemas.py - Pydantic schemas.

A schema describes what data looks like. FastAPI uses them to:
  - check incoming data (and send a clear error if it is wrong)
  - shape outgoing data
  - build the Swagger UI page automatically
"""
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

# ---------- Allowed values ----------
CareerId = Literal["full-stack", "data-analyst", "ai-ml"]
EducationLevel = Literal[
    "High School",
    "Diploma",
    "Undergraduate - Year 1",
    "Undergraduate - Year 2",
    "Undergraduate - Year 3",
    "Undergraduate - Year 4",
    "Postgraduate",
    "Working Professional",
]
Priority = Literal["High", "Medium", "Low"]
GapStatus = Literal["Achieved", "Needs Improvement", "Skill Gap"]
ActivityStatus = Literal["Not Started", "In Progress", "Completed"]


def _clean_name(value: str) -> str:
    value = " ".join(value.split())  # remove extra spaces
    if len(value) < 2:
        raise ValueError("Name must have at least 2 characters.")
    return value


# ======================================================================
# 1. Registration and login
# ======================================================================
class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100, examples=["Priya Sharma"])
    email: EmailStr = Field(examples=["priya.sharma@example.com"])
    password: str = Field(min_length=8, max_length=72, examples=["StrongPass123"])

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        return _clean_name(value)

    @field_validator("password")
    @classmethod
    def check_password(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password is too long (maximum 72 bytes).")
        has_letter = any(char.isalpha() for char in value)
        has_number = any(char.isdigit() for char in value)
        if not (has_letter and has_number):
            raise ValueError("Password must contain at least one letter and one number.")
        return value


class LoginRequest(BaseModel):
    email: EmailStr = Field(examples=["priya.sharma@example.com"])
    password: str = Field(min_length=1, max_length=128, examples=["StrongPass123"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int


# ======================================================================
# 2. Student profile and career selection
# ======================================================================
class ProfileResponse(BaseModel):
    id: int
    name: str
    email: str
    education: Optional[EducationLevel] = None
    study_hours_per_week: int
    career_id: Optional[str] = None
    assessed_careers: List[str] = Field(default_factory=list)


class ProfileUpdateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100, examples=["Priya Sharma"])
    education: EducationLevel = Field(examples=["Undergraduate - Year 2"])
    study_hours_per_week: int = Field(ge=1, le=60, examples=[10])

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        return _clean_name(value)


class CareerSelectRequest(BaseModel):
    career_id: CareerId = Field(examples=["full-stack"])


# ======================================================================
# 3. Careers
# ======================================================================
class Resource(BaseModel):
    title: str
    url: str


class CareerSummary(BaseModel):
    id: str
    name: str
    icon: str
    description: str
    skill_count: int
    top_skills: List[str]


class CareerSkill(BaseModel):
    id: str
    name: str
    target: int
    priority: Priority
    prerequisite: Optional[str] = None
    order: int
    hours_per_level: int
    objective: str
    resource: Resource


class CareerDetail(BaseModel):
    id: str
    name: str
    icon: str
    description: str
    skills: List[CareerSkill]


# ======================================================================
# 4. Skill assessment
# ======================================================================
class SkillRating(BaseModel):
    skill_id: str = Field(min_length=1, max_length=50, examples=["react"])
    level: int = Field(ge=1, le=5, description="1=Beginner, 2=Basic, 3=Intermediate, 4=Advanced, 5=Expert")

    # PHASE 5: one clear message for every invalid level (6, 0, 3.5, "high", true ...)
    @field_validator("level", mode="before")
    @classmethod
    def check_level(cls, value):
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 5:
            raise ValueError("Level must be a whole number from 1 (Beginner) to 5 (Expert).")
        return value


class AssessmentRequest(BaseModel):
    ratings: List[SkillRating] = Field(min_length=1)

    # Fills the Swagger "Try it out" box with a ready-to-use example (Full Stack Developer)
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "ratings": [
                        {"skill_id": "html", "level": 4},
                        {"skill_id": "css", "level": 3},
                        {"skill_id": "javascript", "level": 3},
                        {"skill_id": "git", "level": 3},
                        {"skill_id": "react", "level": 1},
                        {"skill_id": "sql", "level": 1},
                        {"skill_id": "node", "level": 1},
                        {"skill_id": "rest", "level": 1},
                        {"skill_id": "auth", "level": 1},
                        {"skill_id": "testing", "level": 2},
                    ]
                }
            ]
        }
    )

    @field_validator("ratings")
    @classmethod
    def no_duplicates(cls, ratings: List[SkillRating]) -> List[SkillRating]:
        ids = [rating.skill_id for rating in ratings]
        repeated = sorted({skill_id for skill_id in ids if ids.count(skill_id) > 1})
        if repeated:
            raise ValueError("Each skill can only be rated once. Repeated: " + ", ".join(repeated))
        return ratings


class AssessmentResponse(BaseModel):
    career_id: str
    assessed: bool
    ratings: List[SkillRating]
    message: Optional[str] = None


# ======================================================================
# 5. Skill-gap results (PHASE 5: extended)
# ======================================================================
class SkillGapItem(BaseModel):
    skill_id: str
    name: str
    priority: Priority
    current: int                 # 0 means "not assessed yet"
    target: int
    gap: int
    status: GapStatus
    assessed: bool               # PHASE 5
    current_name: str            # PHASE 5, e.g. "Basic" (or "Not assessed")
    target_name: str             # PHASE 5, e.g. "Advanced"
    explanation: str             # PHASE 5, one sentence showing how the result was reached


class SkillGapResponse(BaseModel):
    career_id: str
    career_name: str
    readiness_score: int
    points_earned: int           # PHASE 5: sum of min(current, target)
    points_possible: int         # PHASE 5: sum of targets
    total_skills: int            # PHASE 5
    assessed_count: int          # PHASE 5
    unassessed_count: int        # PHASE 5
    assessment_complete: bool    # PHASE 5: False if some skills are still unrated
    achieved_count: int
    needs_improvement_count: int
    skill_gap_count: int
    skills: List[SkillGapItem]
    method: str = "Rule-based comparison of current and target levels (not machine learning)"
    readiness_note: str          # PHASE 5: honest description of what readiness means


# ======================================================================
# 6. Learning roadmap
# ======================================================================
class RoadmapItem(BaseModel):
    step: int
    skill_id: str
    name: str
    objective: str
    priority: Priority
    current_level: int
    target_level: int
    gap: int
    estimated_hours: int
    prerequisite: Optional[str] = None
    resource: Resource
    status: ActivityStatus


class RoadmapResponse(BaseModel):
    career_id: str
    career_name: str
    study_hours_per_week: int
    total_steps: int
    total_hours: int
    estimated_weeks: int
    items: List[RoadmapItem]
    method: str = "Starter rule-based roadmap (the full generator is built in Phase 6)"


# ======================================================================
# 7. Learning progress
# ======================================================================
class ProgressUpdateRequest(BaseModel):
    skill_id: str = Field(min_length=1, max_length=50, examples=["css"])
    status: ActivityStatus = Field(examples=["Completed"])


class ProgressActivity(BaseModel):
    skill_id: str
    name: str
    estimated_hours: int
    status: ActivityStatus


class ProgressResponse(BaseModel):
    career_id: str
    total_activities: int
    completed: int
    in_progress: int
    not_started: int
    completion_percent: int
    total_hours: int
    completed_hours: int
    hours_percent: int
    activities: List[ProgressActivity]
