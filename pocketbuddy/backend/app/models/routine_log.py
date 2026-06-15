"""Routine log - tracks which activities the user actually completed."""

from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Date, JSON, Boolean

from app.core.database import Base


class RoutineLog(Base):
    __tablename__ = "routine_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False, index=True)
    date = Column(Date, nullable=False)
    routine_id = Column(Integer, nullable=True)
    completed_activities = Column(JSON, nullable=False)  # List of completed activity names
    skipped_activities = Column(JSON, nullable=False)  # List of skipped activity names
    completion_rate = Column(Integer, default=0)  # percentage 0-100
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
