"""Financial models: Expenses, Income, Budget, Bank Statements."""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Date, Text, Enum
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class ExpenseCategory(str, enum.Enum):
    FOOD = "food"
    SHOPPING = "shopping"
    TRAVEL = "travel"
    ENTERTAINMENT = "entertainment"
    EDUCATION = "education"
    HEALTH = "health"
    RENT = "rent"
    UTILITIES = "utilities"
    GROCERIES = "groceries"
    SUBSCRIPTIONS = "subscriptions"
    OTHER = "other"


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    category = Column(Enum(ExpenseCategory), nullable=False)
    description = Column(String, nullable=True)
    merchant = Column(String, nullable=True)
    date = Column(Date, nullable=False)
    source = Column(String, default="manual")  # manual, statement, conversational
    is_essential = Column(String, default="unknown")  # essential, discretionary, unknown
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="expenses")


class Income(Base):
    __tablename__ = "incomes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    source = Column(String, nullable=False)  # allowance, part-time, scholarship, freelance
    description = Column(String, nullable=True)
    date = Column(Date, nullable=False)
    is_recurring = Column(String, default="no")  # yes, no
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="incomes")


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    category = Column(Enum(ExpenseCategory), nullable=False)
    monthly_limit = Column(Float, nullable=False)
    month = Column(String, nullable=False)  # "2024-01"
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="budgets")


class BankStatement(Base):
    __tablename__ = "bank_statements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    processed = Column(String, default="pending")  # pending, processing, completed, failed
    transactions_extracted = Column(Integer, default=0)
    raw_text = Column(Text, nullable=True)
