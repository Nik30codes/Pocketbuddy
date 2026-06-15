"""Financial Wellness Agent - Analyzes spending and provides financial guidance."""

from typing import Any, Dict
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.agents.base_agent import BaseAgent
from app.models.financial import Expense, Income, Budget
from app.models.user import User


class FinancialWellnessAgent(BaseAgent):
    """Agent responsible for financial analysis and wellness scoring."""

    def __init__(self):
        super().__init__(
            name="FinancialWellnessAgent",
            description="Analyzes expenses, categorizes spending, detects overspending, and generates financial wellness scores.",
        )

    def _get_system_prompt(self) -> str:
        return """You are a Financial Wellness Agent for PocketBuddy, an AI assistant for college students.
Your role is to:
- Analyze spending patterns and categorize expenses
- Detect overspending and budget violations
- Calculate financial wellness scores
- Provide actionable, student-friendly financial advice
- Consider the student's income constraints (allowance, part-time work)
- Be encouraging but honest about financial habits
- Use INR (₹) as currency unless specified otherwise

Always be supportive and avoid judgmental language. Students are learning financial management.
Provide specific, actionable recommendations they can implement immediately."""

    async def process(self, user_id: str, data: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Process financial data and generate insights."""
        financial_data = await self._gather_financial_data(user_id, db)
        analysis = await self._analyze_spending(financial_data)
        return analysis

    async def _gather_financial_data(self, user_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Gather all financial data for the user."""
        today = date.today()
        month_start = today.replace(day=1)
        last_30_days = today - timedelta(days=30)

        # Get expenses for current month
        expenses_result = await db.execute(
            select(Expense)
            .where(Expense.user_id == user_id, Expense.date >= month_start)
        )
        expenses = expenses_result.scalars().all()

        # Get income
        income_result = await db.execute(
            select(Income)
            .where(Income.user_id == user_id, Income.date >= month_start)
        )
        incomes = income_result.scalars().all()

        # Get budgets
        budget_result = await db.execute(
            select(Budget)
            .where(Budget.user_id == user_id, Budget.month == today.strftime("%Y-%m"))
        )
        budgets = budget_result.scalars().all()

        # Get user profile
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()

        return {
            "expenses": [
                {"amount": e.amount, "category": e.category.value if hasattr(e.category, 'value') else e.category, "date": str(e.date), "merchant": e.merchant}
                for e in expenses
            ],
            "incomes": [{"amount": i.amount, "source": i.source} for i in incomes],
            "budgets": [
                {"category": b.category.value if hasattr(b.category, 'value') else b.category, "limit": b.monthly_limit}
                for b in budgets
            ],
            "monthly_budget": user.monthly_budget if user else None,
            "total_spent": sum(e.amount for e in expenses),
            "total_income": sum(i.amount for i in incomes),
        }

    async def _analyze_spending(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Use AI to analyze spending patterns."""
        prompt = f"""Analyze this student's financial data for the current month:

Total Spent: ₹{data['total_spent']}
Total Income: ₹{data['total_income']}
Monthly Budget: ₹{data.get('monthly_budget', 'Not set')}

Expenses by category: {data['expenses'][:20]}
Budgets set: {data['budgets']}

Provide a JSON response with:
{{
    "financial_wellness_score": <0-100>,
    "savings_rate": <percentage>,
    "budget_adherence": <percentage>,
    "overspending_categories": [<list of categories over budget>],
    "spending_insights": [<3-5 specific insights>],
    "recommendations": [<3-5 actionable recommendations>],
    "risk_flags": [<any financial risks detected>]
}}"""

        return await self.call_ai_json(prompt)

    async def calculate_financial_score(self, user_id: str, db: AsyncSession) -> float:
        """Calculate a financial wellness score (0-100)."""
        data = await self._gather_financial_data(user_id, db)

        total_income = data["total_income"]
        total_spent = data["total_spent"]
        monthly_budget = data.get("monthly_budget") or total_income

        if monthly_budget == 0:
            return 50.0

        # Scoring components
        savings_rate = max(0, (total_income - total_spent) / total_income * 100) if total_income > 0 else 0
        budget_adherence = max(0, 100 - (total_spent / monthly_budget * 100 - 100)) if monthly_budget > 0 else 50

        # Weighted score
        score = (savings_rate * 0.3) + (min(100, budget_adherence) * 0.4) + (50 * 0.3)  # base stability
        return min(100, max(0, score))
