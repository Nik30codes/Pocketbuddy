"""Financial service - calculations and summaries."""

from datetime import date
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.financial import Expense, Income, Budget


async def calculate_financial_summary(
    user_id: str, month: Optional[str], db: AsyncSession
) -> dict:
    """Calculate comprehensive financial summary."""
    today = date.today()
    target_month = month or today.strftime("%Y-%m")
    year, month_num = map(int, target_month.split("-"))
    month_start = date(year, month_num, 1)

    if month_num == 12:
        month_end = date(year + 1, 1, 1)
    else:
        month_end = date(year, month_num + 1, 1)

    # Get expenses
    expenses_result = await db.execute(
        select(Expense).where(
            Expense.user_id == user_id,
            Expense.date >= month_start,
            Expense.date < month_end,
        )
    )
    expenses = expenses_result.scalars().all()

    # Get income
    income_result = await db.execute(
        select(Income).where(
            Income.user_id == user_id,
            Income.date >= month_start,
            Income.date < month_end,
        )
    )
    incomes = income_result.scalars().all()

    # Get budgets
    budget_result = await db.execute(
        select(Budget).where(Budget.user_id == user_id, Budget.month == target_month)
    )
    budgets = budget_result.scalars().all()

    # Calculations
    total_income = sum(i.amount for i in incomes)
    total_expenses = sum(e.amount for e in expenses)
    savings = total_income - total_expenses
    savings_rate = (savings / total_income * 100) if total_income > 0 else 0

    # Category breakdown
    category_breakdown = {}
    for expense in expenses:
        cat = expense.category.value if hasattr(expense.category, 'value') else expense.category
        category_breakdown[cat] = category_breakdown.get(cat, 0) + expense.amount

    # Budget adherence
    total_budget = sum(b.monthly_limit for b in budgets)
    if not total_budget:
        from app.models.user import User
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        total_budget = user.monthly_budget if user and user.monthly_budget else total_income

    budget_adherence = max(0, min(100, (1 - total_expenses / total_budget) * 100)) if total_budget > 0 else 50

    # Top categories
    sorted_categories = sorted(category_breakdown.items(), key=lambda x: x[1], reverse=True)
    top_spending = [{"category": cat, "amount": amt} for cat, amt in sorted_categories[:5]]

    # Financial wellness score
    score = min(100, max(0,
        (savings_rate * 0.3) +
        (budget_adherence * 0.4) +
        (30 if total_expenses < total_income else 0)  # positive balance bonus
    ))

    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "savings": savings,
        "savings_rate": round(savings_rate, 1),
        "budget_adherence": round(budget_adherence, 1),
        "category_breakdown": category_breakdown,
        "top_spending_categories": top_spending,
        "financial_wellness_score": round(score, 1),
    }
