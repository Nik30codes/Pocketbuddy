"""Student Life Coach Agent - Orchestrates all agent outputs into actionable plans."""

from typing import Any, Dict
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.agents.base_agent import BaseAgent
from app.agents.financial_agent import FinancialWellnessAgent
from app.agents.wellness_agent import WellnessAgent
from app.agents.burnout_agent import BurnoutDetectionAgent
from app.models.ai_insights import WeeklyReport
from app.models.user import User


class StudentLifeCoachAgent(BaseAgent):
    """Master agent that combines outputs from all agents into unified guidance."""

    def __init__(self):
        super().__init__(
            name="StudentLifeCoachAgent",
            description="Combines all agent outputs to generate weekly action plans, wellness summaries, and academic balance recommendations.",
        )
        self.financial_agent = FinancialWellnessAgent()
        self.wellness_agent = WellnessAgent()
        self.burnout_agent = BurnoutDetectionAgent()

    def _get_system_prompt(self) -> str:
        return """You are the Student Life Coach Agent for PocketBuddy - the final decision-maker.

YOUR ROLE:
- Synthesize insights from Financial, Wellness, and Burnout agents
- Generate comprehensive weekly action plans
- Provide holistic life management guidance
- Balance academic demands with personal wellbeing
- Act as a student's intelligent life operating system

OUTPUT PRIORITIES:
1. Address any critical burnout risks immediately
2. Financial stability and budget adherence
3. Physical and mental wellness
4. Academic performance optimization
5. Social and recreational balance

COMMUNICATION STYLE:
- Direct and actionable
- Supportive but honest
- Prioritized (most important first)
- Time-bound (specific deadlines/times)
- Encouraging of progress"""

    async def process(self, user_id: str, data: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Generate comprehensive life coaching insights."""
        return await self.generate_weekly_report(user_id, db)

    async def generate_weekly_report(self, user_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Generate a comprehensive weekly report combining all agent insights."""
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        # Gather data from all agents
        financial_analysis = await self.financial_agent.process(user_id, {}, db)
        wellness_analysis = await self.wellness_agent.process(user_id, {}, db)
        burnout_assessment = await self.burnout_agent.assess_burnout_risk(user_id, db)

        # Calculate scores
        financial_score = financial_analysis.get("financial_wellness_score", 50)
        wellness_score = wellness_analysis.get("overall_wellness_score", 50)
        burnout_risk = burnout_assessment.get("risk_level", "low")

        # Generate unified action plan
        action_plan = await self._generate_action_plan(
            financial_analysis, wellness_analysis, burnout_assessment
        )

        # Generate summaries
        financial_summary = await self._summarize_financial(financial_analysis)
        wellness_summary = await self._summarize_wellness(wellness_analysis)

        # Save report
        report = WeeklyReport(
            user_id=user_id,
            week_start=week_start,
            week_end=week_end,
            financial_score=financial_score if isinstance(financial_score, (int, float)) else 50,
            wellness_score=wellness_score if isinstance(wellness_score, (int, float)) else 50,
            burnout_risk=burnout_risk,
            financial_summary=financial_summary,
            wellness_summary=wellness_summary,
            action_plan=action_plan,
            total_spent=financial_analysis.get("total_spent"),
            avg_mood=wellness_analysis.get("mood_stability_score"),
            avg_sleep=wellness_analysis.get("sleep_quality_score"),
        )
        db.add(report)
        await db.flush()
        await db.refresh(report)

        return {
            "id": report.id,
            "week_start": report.week_start,
            "week_end": report.week_end,
            "financial_score": report.financial_score,
            "wellness_score": report.wellness_score,
            "burnout_risk": report.burnout_risk,
            "financial_summary": report.financial_summary,
            "wellness_summary": report.wellness_summary,
            "action_plan": report.action_plan,
            "total_spent": report.total_spent,
            "avg_mood": report.avg_mood,
            "avg_sleep": report.avg_sleep,
        }

    async def _generate_action_plan(
        self, financial: Dict, wellness: Dict, burnout: Dict
    ) -> list:
        """Generate a prioritized weekly action plan."""
        prompt = f"""Based on these agent analyses for a college student:

FINANCIAL: Score {financial.get('financial_wellness_score', 50)}/100
- Insights: {financial.get('spending_insights', [])}
- Recommendations: {financial.get('recommendations', [])}

WELLNESS: Score {wellness.get('overall_wellness_score', 50)}/100
- Concerns: {wellness.get('concerns', [])}
- Recommendations: {wellness.get('recommendations', [])}

BURNOUT: Risk Level: {burnout.get('risk_level', 'low')}
- Factors: {burnout.get('contributing_factors', [])}
- Recommendations: {burnout.get('recommendations', [])}

Generate a prioritized weekly action plan with 5-7 items.
Return as a JSON array of objects:
[
    {{"priority": 1, "action": "...", "category": "wellness|financial|academic|social", "timeframe": "today|this_week"}},
    ...
]"""

        result = await self.call_ai_json(prompt)
        if isinstance(result, list):
            return result
        return result.get("action_plan", [
            {"priority": 1, "action": "Complete your daily wellness check-in", "category": "wellness", "timeframe": "today"},
            {"priority": 2, "action": "Review this week's spending", "category": "financial", "timeframe": "today"},
            {"priority": 3, "action": "Set a sleep schedule and stick to it", "category": "wellness", "timeframe": "this_week"},
        ])

    async def _summarize_financial(self, analysis: Dict) -> str:
        """Create a brief financial summary."""
        score = analysis.get("financial_wellness_score", 50)
        insights = analysis.get("spending_insights", [])
        return f"Financial wellness score: {score}/100. " + " ".join(insights[:2]) if insights else f"Financial wellness score: {score}/100."

    async def _summarize_wellness(self, analysis: Dict) -> str:
        """Create a brief wellness summary."""
        score = analysis.get("overall_wellness_score", 50)
        concerns = analysis.get("concerns", [])
        return f"Wellness score: {score}/100. " + " ".join(concerns[:2]) if concerns else f"Wellness score: {score}/100."

    async def generate_exam_plan(self, user_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Generate an exam survival plan."""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        prompt = f"""Generate an exam survival plan for a college student.
Student context:
- Monthly budget: ₹{user.monthly_budget if user else 'Not set'}
- Living: {user.living_situation.value if user and user.living_situation else 'Unknown'}
- Kitchen access: {user.has_kitchen_access if user else False}

Include:
1. Study schedule optimization tips
2. Budget-friendly brain food suggestions
3. Stress management techniques
4. Sleep optimization for exam weeks
5. Quick exercise routines (5-10 min)

Return as JSON with keys: study_tips, food_suggestions, stress_techniques, sleep_tips, exercise_routines"""

        return await self.call_ai_json(prompt)
