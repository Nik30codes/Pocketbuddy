"""Prediction service - forecasting and trend analysis."""

from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.financial import Expense, Income
from app.models.wellness import DailyCheckin, WellnessScore


async def generate_predictions(user_id: str, db: AsyncSession) -> dict:
    """Generate predictive analytics for the user."""
    today = date.today()
    month_start = today.replace(day=1)

    # Get spending data
    expenses_result = await db.execute(
        select(Expense).where(
            Expense.user_id == user_id, Expense.date >= month_start
        )
    )
    expenses = expenses_result.scalars().all()

    # Get income
    income_result = await db.execute(
        select(Income).where(
            Income.user_id == user_id, Income.date >= month_start
        )
    )
    incomes = income_result.scalars().all()

    # Get wellness trends
    week_ago = today - timedelta(days=14)
    wellness_result = await db.execute(
        select(WellnessScore)
        .where(WellnessScore.user_id == user_id, WellnessScore.date >= week_ago)
        .order_by(WellnessScore.date.asc())
    )
    wellness_scores = wellness_result.scalars().all()

    # Calculate predictions
    total_spent = sum(e.amount for e in expenses)
    total_income = sum(i.amount for i in incomes)
    days_elapsed = (today - month_start).days + 1
    days_in_month = 30

    # Month-end spending forecast (linear projection)
    daily_avg_spend = total_spent / days_elapsed if days_elapsed > 0 else 0
    month_end_forecast = daily_avg_spend * days_in_month

    # Savings projection
    savings_projection = total_income - month_end_forecast

    # Burnout risk trend
    burnout_trend = "stable"
    if len(wellness_scores) >= 4:
        recent = wellness_scores[-2:]
        older = wellness_scores[:2]
        recent_avg = sum(
            1 for s in recent if s.burnout_risk in ("high", "critical")
        )
        older_avg = sum(
            1 for s in older if s.burnout_risk in ("high", "critical")
        )
        if recent_avg > older_avg:
            burnout_trend = "increasing"
        elif recent_avg < older_avg:
            burnout_trend = "decreasing"

    # Generate recommendations
    recommendations = []
    if month_end_forecast > total_income:
        overshoot = month_end_forecast - total_income
        recommendations.append(
            f"At current pace, you'll overspend by ₹{overshoot:.0f} this month. Consider reducing discretionary spending."
        )
    if burnout_trend == "increasing":
        recommendations.append(
            "Your burnout risk is trending upward. Prioritize rest and breaks this week."
        )
    if daily_avg_spend > 0:
        safe_daily = (total_income - total_spent) / max(1, days_in_month - days_elapsed)
        recommendations.append(
            f"To stay on budget, keep daily spending under ₹{max(0, safe_daily):.0f} for the rest of the month."
        )
    if not recommendations:
        recommendations.append("You're on track! Keep maintaining your current habits.")

    return {
        "month_end_spending_forecast": round(month_end_forecast, 2),
        "burnout_risk_trend": burnout_trend,
        "savings_projection": round(savings_projection, 2),
        "recommendations": recommendations,
    }
