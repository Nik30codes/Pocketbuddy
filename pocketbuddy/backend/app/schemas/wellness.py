"""Wellness schemas."""

from typing import Optional, List
from datetime import date
from pydantic import BaseModel, Field


class DailyCheckinCreate(BaseModel):
    date: date
    mood_score: int = Field(ge=1, le=10)
    stress_score: int = Field(ge=1, le=10)
    sleep_hours: float = Field(ge=0, le=24)
    meals_skipped: int = Field(ge=0, le=3, default=0)
    water_glasses: int = Field(ge=0, default=0)
    study_hours: float = Field(ge=0, le=24, default=0)
    exercise_minutes: int = Field(ge=0, default=0)
    journal_entry: Optional[str] = None
    gratitude_note: Optional[str] = None


class DailyCheckinResponse(BaseModel):
    id: int
    date: date
    mood_score: int
    stress_score: int
    sleep_hours: float
    meals_skipped: int
    water_glasses: int
    study_hours: float
    exercise_minutes: int
    emotional_state: Optional[str] = None
    journal_entry: Optional[str] = None

    class Config:
        from_attributes = True


class WellnessScoreResponse(BaseModel):
    overall_wellness: float
    sleep_quality: float
    stress_management: float
    nutrition_score: float
    activity_score: float
    mood_stability: float
    financial_wellness: Optional[float] = None
    burnout_risk: str

    class Config:
        from_attributes = True


class WellnessTrend(BaseModel):
    dates: List[str]
    mood_scores: List[float]
    stress_scores: List[float]
    sleep_hours: List[float]
    overall_wellness: List[float]


class ConversationalCheckin(BaseModel):
    """For natural language wellness logging."""
    message: str  # e.g., "Had only 4 hours of sleep, feeling stressed"
