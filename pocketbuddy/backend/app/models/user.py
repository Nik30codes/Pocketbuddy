"""User model."""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class LivingSituation(str, enum.Enum):
    HOSTELLER = "hosteller"
    DAY_SCHOLAR = "day_scholar"
    RENTED = "rented"
    HOME = "home"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=True)  # Null for OAuth users
    full_name = Column(String, nullable=False)
    avatar_url = Column(String, nullable=True)

    # Profile Data
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)
    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    college_name = Column(String, nullable=True)
    living_situation = Column(Enum(LivingSituation), nullable=True)
    monthly_budget = Column(Float, nullable=True)
    food_preferences = Column(String, nullable=True)  # JSON string
    fitness_goals = Column(String, nullable=True)
    sleep_goal_hours = Column(Float, default=7.0)
    has_kitchen_access = Column(Boolean, default=False)

    # Schedule
    college_start_time = Column(String, nullable=True)  # "09:00"
    college_end_time = Column(String, nullable=True)  # "17:00"

    # Auth
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    auth_provider = Column(String, default="local")  # local, google

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Relationships
    expenses = relationship("Expense", back_populates="user", lazy="dynamic")
    incomes = relationship("Income", back_populates="user", lazy="dynamic")
    budgets = relationship("Budget", back_populates="user", lazy="dynamic")
    checkins = relationship("DailyCheckin", back_populates="user", lazy="dynamic")
    insights = relationship("AIInsight", back_populates="user", lazy="dynamic")
    routines = relationship("Routine", back_populates="user", lazy="dynamic")
