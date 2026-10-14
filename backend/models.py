"""
models.py - Database tables (SQLAlchemy models).

One class = one table. One attribute = one column.
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


# ======================================================================
# 1. Students
# ======================================================================
class Student(Base):
    __tablename__ = "students"
    __table_args__ = (
        CheckConstraint("study_hours_per_week BETWEEN 1 AND 60", name="ck_students_study_hours"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))  # NEVER the real password
    education: Mapped[Optional[str]] = mapped_column(String(50), default=None)
    study_hours_per_week: Mapped[int] = mapped_column(default=10)
    career_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("careers.id", ondelete="SET NULL"), default=None
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    career: Mapped[Optional["Career"]] = relationship()
    skill_ratings: Mapped[List["StudentSkill"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    progress_records: Mapped[List["LearningProgress"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )


# ======================================================================
# 2. Careers
# ======================================================================
class Career(Base):
    __tablename__ = "careers"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True)  # e.g. "full-stack"
    career_name: Mapped[str] = mapped_column(String(100), unique=True)
    icon: Mapped[str] = mapped_column(String(10), default="🎯")
    description: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    requirements: Mapped[List["CareerSkill"]] = relationship(
        back_populates="career",
        cascade="all, delete-orphan",
        order_by="CareerSkill.display_order",
    )


# ======================================================================
# 3. Skills (each skill is stored ONCE and shared by careers)
# ======================================================================
class Skill(Base):
    __tablename__ = "skills"
    __table_args__ = (
        CheckConstraint("hours_per_level > 0", name="ck_skills_hours_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True)  # e.g. "react"
    skill_name: Mapped[str] = mapped_column(String(100), unique=True)
    category: Mapped[str] = mapped_column(String(50))
    objective: Mapped[str] = mapped_column(Text)
    hours_per_level: Mapped[int]
    resource_title: Mapped[str] = mapped_column(String(150))
    resource_url: Mapped[str] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ======================================================================
# 4. Career Skills (which skills a career needs, and the target level)
# ======================================================================
# Small helper table: "to learn this career skill, learn these skills first"
career_skill_prerequisites = Table(
    "career_skill_prerequisites",
    Base.metadata,
    Column("career_skill_id", ForeignKey("career_skills.id", ondelete="CASCADE"), primary_key=True),
    Column("prerequisite_skill_id", ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)


class CareerSkill(Base):
    __tablename__ = "career_skills"
    __table_args__ = (
        UniqueConstraint("career_id", "skill_id", name="uq_career_skill"),
        CheckConstraint("target_level BETWEEN 1 AND 5", name="ck_career_skills_target"),
        CheckConstraint("priority IN ('High', 'Medium', 'Low')", name="ck_career_skills_priority"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    career_id: Mapped[int] = mapped_column(ForeignKey("careers.id", ondelete="CASCADE"))
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"))
    target_level: Mapped[int]
    priority: Mapped[str] = mapped_column(String(10))
    display_order: Mapped[int]
    label: Mapped[Optional[str]] = mapped_column(String(100), default=None)  # career-specific name

    career: Mapped["Career"] = relationship(back_populates="requirements")
    skill: Mapped["Skill"] = relationship()
    prerequisites: Mapped[List["Skill"]] = relationship(secondary=career_skill_prerequisites)


# ======================================================================
# 5. Student Skills (current level of each rated skill)
# ======================================================================
class StudentSkill(Base):
    __tablename__ = "student_skills"
    __table_args__ = (
        CheckConstraint("current_level BETWEEN 1 AND 5", name="ck_student_skills_level"),
    )

    # student_id + skill_id together are the primary key: one rating per student per skill
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), primary_key=True
    )
    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True
    )
    current_level: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    student: Mapped["Student"] = relationship(back_populates="skill_ratings")
    skill: Mapped["Skill"] = relationship()


# ======================================================================
# 6. Learning Progress (status of each learning activity)
# ======================================================================
class LearningProgress(Base):
    __tablename__ = "learning_progress"
    __table_args__ = (
        CheckConstraint(
            "status IN ('Not Started', 'In Progress', 'Completed')", name="ck_progress_status"
        ),
        CheckConstraint("progress BETWEEN 0 AND 100", name="ck_progress_percent"),
    )

    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), primary_key=True
    )
    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True
    )
    status: Mapped[str] = mapped_column(String(20), default="Not Started")
    progress: Mapped[int] = mapped_column(default=0)  # 0, 50, or 100 (set from status)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    student: Mapped["Student"] = relationship(back_populates="progress_records")
    skill: Mapped["Skill"] = relationship()


# ======================================================================
# 7. Assessment History (every submitted rating is kept, never overwritten)
# ======================================================================
class AssessmentHistory(Base):
    __tablename__ = "assessment_history"
    __table_args__ = (
        CheckConstraint("level BETWEEN 1 AND 5", name="ck_assessment_history_level"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), index=True
    )
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"))
    level: Mapped[int]
    assessed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

