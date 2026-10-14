from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from database import Base


def _now():
    return datetime.now(timezone.utc)


class LearningRoadmap(Base):
    __tablename__ = "learning_roadmaps"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, nullable=False, index=True)
    career = Column(String(100), nullable=False)
    hours_per_day = Column(Float, nullable=False)
    days_per_week = Column(Integer, nullable=False)
    input_hash = Column(String(64), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    plan_json = Column(Text, nullable=False)  # summary, weekly schedule, warnings, message
    created_at = Column(DateTime(timezone=True), default=_now)

    activities = relationship("RoadmapActivity", back_populates="roadmap",
                              cascade="all, delete-orphan", order_by="RoadmapActivity.sequence")

    __table_args__ = (Index("ix_roadmap_student_career_active", "student_id", "career", "is_active"),)


class RoadmapActivity(Base):
    __tablename__ = "learning_roadmap_activities"

    id = Column(Integer, primary_key=True, index=True)
    roadmap_id = Column(Integer, ForeignKey("learning_roadmaps.id"), nullable=False, index=True)
    sequence = Column(Integer, nullable=False)
    skill_name = Column(String(100), nullable=False)
    current_level = Column(Integer, nullable=False)
    target_level = Column(Integer, nullable=False)
    gap = Column(Integer, nullable=False)
    severity = Column(String(20))
    priority_score = Column(Float)
    estimated_hours = Column(Float, nullable=False)
    hours_completed = Column(Float, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="not_started")  # not_started | in_progress | completed
    objectives_json = Column(Text, nullable=False, default="[]")
    prerequisites_json = Column(Text, nullable=False, default="[]")
    start_with = Column(Text)
    reason = Column(Text)
    resource_title = Column(String(200))
    resource_url = Column(String(500))
    unassessed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True))

    roadmap = relationship("LearningRoadmap", back_populates="activities")
