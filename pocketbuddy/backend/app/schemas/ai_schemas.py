"""AI-related schemas."""

from typing import Optional, List, Dict, Any
from datetime import date
from pydantic import BaseModel


class RoutineRequest(BaseModel):
    routine_type: str = "daily"  # daily, weekly, exam, budget_friendly
    constraints: Optional[Dict[str, Any]] = None


class RoutineResponse(BaseModel):
    id: int
    routine_type: str
    name: str
    schedule: List[Dict[str, str]]
    constraints: Optional[Dict[str, Any]] = None
    is_active: str

    class Config:
        from_attributes = True


class InsightResponse(BaseModel):
    id: int
    agent_type: str
    insight_type: str
    title: str
    content: str
    priority: str
    created_at: str

    class Config:
        from_attributes = True


class BurnoutAlertResponse(BaseModel):
    risk_level: str
    risk_score: float
    contributing_factors: List[str]
    recommendations: List[str]

    class Config:
        from_attributes = True


class WeeklyReportResponse(BaseModel):
    id: int
    week_start: date
    week_end: date
    financial_score: float
    wellness_score: float
    burnout_risk: str
    financial_summary: str
    wellness_summary: str
    action_plan: List[Dict[str, Any]]
    total_spent: Optional[float] = None
    avg_mood: Optional[float] = None
    avg_sleep: Optional[float] = None

    class Config:
        from_attributes = True


class ChatMessage(BaseModel):
    message: str
    context: Optional[str] = None  # financial, wellness, routine, general


class ChatResponse(BaseModel):
    response: str
    agent: str
    actions_taken: Optional[List[str]] = None
    suggestions: Optional[List[str]] = None
    conversation_id: Optional[int] = None


class PredictiveAnalytics(BaseModel):
    month_end_spending_forecast: float
    burnout_risk_trend: str  # increasing, stable, decreasing
    savings_projection: float
    recommendations: List[str]
