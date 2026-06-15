"""Monthly Report model - stores end-of-month snapshots."""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON

from app.core.database import Base


class MonthlyReport(Base):
    __tablename__ = "monthly_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False, index=True)
    month = Column(String, nullable=False)  # "2026-06"
    
    # Financial snapshot
    total_income = Column(Float, default=0)
    total_expenses = Column(Float, default=0)
    savings = Column(Float, default=0)
    savings_rate = Column(Float, default=0)
    category_breakdown = Column(JSON, nullable=True)
    top_expense_category = Column(String, nullable=True)
    financial_score = Column(Float, default=50)

    # Wellness snapshot
    avg_mood = Column(Float, nullable=True)
    avg_stress = Column(Float, nullable=True)
    avg_sleep = Column(Float, nullable=True)
    avg_exercise = Column(Float, nullable=True)
    total_checkins = Column(Integer, default=0)
    wellness_score = Column(Float, default=50)
    burnout_risk = Column(String, default="low")

    # AI Summary
    financial_summary = Column(Text, nullable=True)
    wellness_summary = Column(Text, nullable=True)
    highlights = Column(JSON, nullable=True)  # Key achievements
    areas_to_improve = Column(JSON, nullable=True)
    next_month_goals = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
