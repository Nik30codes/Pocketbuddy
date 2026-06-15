"""Wellness models: Daily Check-ins, Wellness Scores."""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Date, Text

from app.core.database import Base
from sqlalchemy.orm import relationship


class DailyCheckin(Base):
    __tablename__ = "daily_checkins"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(Date, nullable=False)

    # Core metrics (1-10 scale)
    mood_score = Column(Integer, nullable=False)
    stress_score = Column(Integer, nullable=False)

    # Lifestyle metrics
    sleep_hours = Column(Float, nullable=False)
    meals_skipped = Column(Integer, default=0)
    water_glasses = Column(Integer, default=0)
    study_hours = Column(Float, default=0)
    exercise_minutes = Column(Integer, default=0)

    # Optional notes
    journal_entry = Column(Text, nullable=True)
    gratitude_note = Column(String, nullable=True)

    # AI-classified emotional state
    emotional_state = Column(String, nullable=True)  # happy, anxious, stressed, calm, etc.

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="checkins")


class WellnessScore(Base):
    __tablename__ = "wellness_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(Date, nullable=False)

    # Composite scores (0-100)
    overall_wellness = Column(Float, nullable=False)
    sleep_quality = Column(Float, nullable=False)
    stress_management = Column(Float, nullable=False)
    nutrition_score = Column(Float, nullable=False)
    activity_score = Column(Float, nullable=False)
    mood_stability = Column(Float, nullable=False)

    # Financial wellness (0-100)
    financial_wellness = Column(Float, nullable=True)
    savings_rate = Column(Float, nullable=True)
    budget_adherence = Column(Float, nullable=True)

    # Burnout Risk
    burnout_risk = Column(String, default="low")  # low, medium, high, critical

    created_at = Column(DateTime, default=datetime.utcnow)
