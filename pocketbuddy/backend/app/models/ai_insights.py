"""AI Insights models: Insights, Burnout Alerts, Weekly Reports, Routines."""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Date, Text, JSON

from app.core.database import Base
from sqlalchemy.orm import relationship


class AIInsight(Base):
    __tablename__ = "ai_insights"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    agent_type = Column(String, nullable=False)  # financial, wellness, burnout, routine, emotional, coach
    insight_type = Column(String, nullable=False)  # recommendation, alert, summary, plan
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    priority = Column(String, default="medium")  # low, medium, high, critical
    extra_data = Column(JSON, nullable=True)
    is_read = Column(String, default="no")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="insights")


class BurnoutAlert(Base):
    __tablename__ = "burnout_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    risk_level = Column(String, nullable=False)  # low, medium, high, critical
    risk_score = Column(Float, nullable=False)  # 0-100
    contributing_factors = Column(JSON, nullable=False)  # List of factors
    recommendations = Column(JSON, nullable=False)  # List of recommendations
    is_acknowledged = Column(String, default="no")
    created_at = Column(DateTime, default=datetime.utcnow)


class WeeklyReport(Base):
    __tablename__ = "weekly_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    week_start = Column(Date, nullable=False)
    week_end = Column(Date, nullable=False)

    # Scores
    financial_score = Column(Float, nullable=False)
    wellness_score = Column(Float, nullable=False)
    burnout_risk = Column(String, nullable=False)

    # Summaries
    financial_summary = Column(Text, nullable=False)
    wellness_summary = Column(Text, nullable=False)
    action_plan = Column(JSON, nullable=False)  # List of action items

    # Report data
    total_spent = Column(Float, nullable=True)
    total_income = Column(Float, nullable=True)
    avg_mood = Column(Float, nullable=True)
    avg_sleep = Column(Float, nullable=True)
    avg_stress = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class Routine(Base):
    __tablename__ = "routines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    routine_type = Column(String, nullable=False)  # daily, weekly, exam, budget_friendly
    name = Column(String, nullable=False)
    schedule = Column(JSON, nullable=False)  # List of time-activity pairs
    constraints = Column(JSON, nullable=True)  # Budget, time, etc.
    is_active = Column(String, default="yes")
    effectiveness_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="routines")
