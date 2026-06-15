"""Notification model for AI-powered notifications."""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text

from app.core.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String, nullable=False)  # financial, wellness, burnout, routine, prediction, achievement, exam_mode, ai_insight
    priority = Column(String, nullable=False, default="medium")  # low, medium, high, critical
    action_url = Column(String, nullable=True)  # e.g., /financial, /wellness, /routine
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
