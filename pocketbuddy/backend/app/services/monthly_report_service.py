"""Monthly report service - generates end-of-month reports."""

from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.financial import Expense, Income
from app.models.wellness import DailyCheckin
from app.models.monthly_report import MonthlyReport
from app.models.user import User


async def generate_monthly_report(user_id: str, month: str, db: AsyncSession) -> dict:
    """Generate a monthly report for the given month (format: 2026-06)."""
    year, month_num = map(int, month.split("-"))
    month_start = date(year, month_num, 1)
    if month_num == 12:
        month_end = date(year + 1, 1, 1)
    else:
        month_end = date(year, month_num + 1, 1)

    # Check if report already exists
    existing = await db.execute(
        select(MonthlyReport).where(
            MonthlyReport.user_id == user_id, MonthlyReport.month == month
        )
    )
    if existing.scalar_one_or_none():
        # Return existing
        result = await db.execute(
            select(MonthlyReport).where(
                MonthlyReport.user_id == user_id, MonthlyReport.month == month
            )
        )
        report = result.scalar_one()
        return _report_to_dict(report)

    # Gather financial data
    expenses_result = await db.execute(
        select(Expense).where(
            Expense.user_id == user_id,
            Expense.date >= month_start,
            Expense.date < month_end,
        )
    )
    expenses = expenses_result.scalars().all()

    income_result = await db.execute(
        select(Income).where(
            Income.user_id == user_id,
            Income.date >= month_start,
            Income.date < month_end,
        )
    )
    incomes = income_result.scalars().all()

    total_income = sum(i.amount for i in incomes)
    total_expenses = sum(e.amount for e in expenses)
    savings = total_income - total_expenses
    savings_rate = (savings / total_income * 100) if total_income > 0 else 0

    # Category breakdown
    category_breakdown = {}
    for e in expenses:
        cat = e.category.value if hasattr(e.category, 'value') else str(e.category)
        category_breakdown[cat] = category_breakdown.get(cat, 0) + e.amount

    top_category = max(category_breakdown, key=category_breakdown.get) if category_breakdown else None

    # Financial score
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    budget = user.monthly_budget if user and user.monthly_budget else total_income
    budget_adherence = max(0, min(100, (1 - total_expenses / budget) * 100)) if budget > 0 else 50
    financial_score = min(100, max(0, savings_rate * 0.4 + budget_adherence * 0.4 + 20))

    # Gather wellness data
    checkins_result = await db.execute(
        select(DailyCheckin).where(
            DailyCheckin.user_id == user_id,
            DailyCheckin.date >= month_start,
            DailyCheckin.date < month_end,
        )
    )
    checkins = checkins_result.scalars().all()

    avg_mood = sum(c.mood_score for c in checkins) / len(checkins) if checkins else None
    avg_stress = sum(c.stress_score for c in checkins) / len(checkins) if checkins else None
    avg_sleep = sum(c.sleep_hours for c in checkins) / len(checkins) if checkins else None
    avg_exercise = sum(c.exercise_minutes for c in checkins) / len(checkins) if checkins else None

    # Wellness score
    if checkins:
        mood_s = (avg_mood / 10) * 100
        stress_s = ((10 - avg_stress) / 10) * 100
        sleep_s = min(100, (avg_sleep / 8) * 100)
        wellness_score = mood_s * 0.3 + stress_s * 0.3 + sleep_s * 0.4
    else:
        wellness_score = 50

    # Burnout risk
    burnout_risk = "low"
    if avg_stress and avg_sleep:
        if avg_stress >= 8 and avg_sleep < 5:
            burnout_risk = "critical"
        elif avg_stress >= 7 or avg_sleep < 5:
            burnout_risk = "high"
        elif avg_stress >= 5 and avg_sleep < 6:
            burnout_risk = "medium"

    # Generate summaries
    financial_summary = f"You spent ₹{total_expenses:,.0f} and earned ₹{total_income:,.0f} this month. "
    if savings >= 0:
        financial_summary += f"You saved ₹{savings:,.0f} ({savings_rate:.0f}% savings rate). "
    else:
        financial_summary += f"You overspent by ₹{abs(savings):,.0f}. "
    if top_category:
        financial_summary += f"Top spending: {top_category} (₹{category_breakdown[top_category]:,.0f})."

    wellness_summary = ""
    if checkins:
        wellness_summary = f"You logged {len(checkins)} check-ins. Avg mood: {avg_mood:.1f}/10, stress: {avg_stress:.1f}/10, sleep: {avg_sleep:.1f}h."
    else:
        wellness_summary = "No wellness check-ins this month."

    # Highlights & improvements
    highlights = []
    areas_to_improve = []
    if savings_rate > 20:
        highlights.append("Great savings rate!")
    if avg_mood and avg_mood >= 7:
        highlights.append("Maintained good mood throughout the month")
    if avg_sleep and avg_sleep >= 7:
        highlights.append("Consistent sleep schedule")
    if len(checkins) >= 20:
        highlights.append(f"Logged {len(checkins)} daily check-ins — great consistency!")

    if savings_rate < 0:
        areas_to_improve.append("Reduce spending to stay within budget")
    if avg_stress and avg_stress > 6:
        areas_to_improve.append("Stress management — try daily breaks")
    if avg_sleep and avg_sleep < 6:
        areas_to_improve.append("Prioritize sleep — aim for 7+ hours")
    if len(checkins) < 10:
        areas_to_improve.append("Log more daily check-ins for better insights")

    # Save report
    report = MonthlyReport(
        user_id=user_id,
        month=month,
        total_income=total_income,
        total_expenses=total_expenses,
        savings=savings,
        savings_rate=round(savings_rate, 1),
        category_breakdown=category_breakdown,
        top_expense_category=top_category,
        financial_score=round(financial_score, 1),
        avg_mood=round(avg_mood, 1) if avg_mood else None,
        avg_stress=round(avg_stress, 1) if avg_stress else None,
        avg_sleep=round(avg_sleep, 1) if avg_sleep else None,
        avg_exercise=round(avg_exercise, 0) if avg_exercise else None,
        total_checkins=len(checkins),
        wellness_score=round(wellness_score, 1),
        burnout_risk=burnout_risk,
        financial_summary=financial_summary,
        wellness_summary=wellness_summary,
        highlights=highlights,
        areas_to_improve=areas_to_improve,
        next_month_goals=[
            "Set a daily spending limit",
            "Log check-ins every day",
            "Maintain 7+ hours of sleep",
        ],
    )
    db.add(report)
    await db.flush()
    await db.refresh(report)

    return _report_to_dict(report)


async def get_all_monthly_reports(user_id: str, db: AsyncSession) -> list:
    """Get all monthly reports for a user."""
    result = await db.execute(
        select(MonthlyReport)
        .where(MonthlyReport.user_id == user_id)
        .order_by(MonthlyReport.month.desc())
    )
    reports = result.scalars().all()
    return [_report_to_dict(r) for r in reports]


def _report_to_dict(report: MonthlyReport) -> dict:
    return {
        "id": report.id,
        "month": report.month,
        "total_income": report.total_income,
        "total_expenses": report.total_expenses,
        "savings": report.savings,
        "savings_rate": report.savings_rate,
        "category_breakdown": report.category_breakdown,
        "top_expense_category": report.top_expense_category,
        "financial_score": report.financial_score,
        "avg_mood": report.avg_mood,
        "avg_stress": report.avg_stress,
        "avg_sleep": report.avg_sleep,
        "avg_exercise": report.avg_exercise,
        "total_checkins": report.total_checkins,
        "wellness_score": report.wellness_score,
        "burnout_risk": report.burnout_risk,
        "financial_summary": report.financial_summary,
        "wellness_summary": report.wellness_summary,
        "highlights": report.highlights,
        "areas_to_improve": report.areas_to_improve,
        "next_month_goals": report.next_month_goals,
    }
