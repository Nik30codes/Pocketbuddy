"""Financial schemas."""

from typing import Optional, List
from datetime import date
from pydantic import BaseModel


class ExpenseCreate(BaseModel):
    amount: float
    category: str
    description: Optional[str] = None
    merchant: Optional[str] = None
    date: date
    is_essential: Optional[str] = "unknown"


class ExpenseResponse(BaseModel):
    id: int
    amount: float
    category: str
    description: Optional[str] = None
    merchant: Optional[str] = None
    date: date
    source: str
    is_essential: str

    class Config:
        from_attributes = True


class IncomeCreate(BaseModel):
    amount: float
    source: str
    description: Optional[str] = None
    date: date
    is_recurring: Optional[str] = "no"


class IncomeResponse(BaseModel):
    id: int
    amount: float
    source: str
    description: Optional[str] = None
    date: date
    is_recurring: str

    class Config:
        from_attributes = True


class BudgetCreate(BaseModel):
    category: str
    monthly_limit: float
    month: str  # "2024-01"


class BudgetResponse(BaseModel):
    id: int
    category: str
    monthly_limit: float
    month: str

    class Config:
        from_attributes = True


class FinancialSummary(BaseModel):
    total_income: float
    total_expenses: float
    savings: float
    savings_rate: float
    budget_adherence: float
    category_breakdown: dict
    top_spending_categories: List[dict]
    financial_wellness_score: float


class ConversationalExpense(BaseModel):
    """For natural language expense logging."""
    message: str  # e.g., "Spent ₹250 on lunch at cafe"
