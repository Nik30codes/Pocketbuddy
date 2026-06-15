"""Routine Planning Agent - Generates personalized daily/weekly routines."""

from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.agents.base_agent import BaseAgent
from app.models.user import User
from app.models.ai_insights import Routine
from app.models.wellness import DailyCheckin


class RoutinePlanningAgent(BaseAgent):
    """Agent responsible for generating personalized routines."""

    def __init__(self):
        super().__init__(
            name="RoutinePlanningAgent",
            description="Generates personalized daily, weekly, exam, and budget-friendly routines.",
        )

    def _get_system_prompt(self) -> str:
        return """You are a Routine Planning Agent for PocketBuddy.
Your role is to create highly personalized routines for college students.

CONSTRAINTS TO CONSIDER:
- Budget limitations
- Living situation (hostel/day scholar/rented)
- College timings
- Sleep goals
- Academic workload
- Food preferences and kitchen availability
- Physical fitness goals

ROUTINE TYPES:
- Daily: Standard day-to-day routine
- Weekly: Week overview with variety
- Exam: Intensive study-focused routine with wellness breaks
- Budget-friendly: Cost-optimized daily plan

RULES:
- All routines must be realistic and achievable
- Include proper sleep time (aim for user's sleep goal)
- Include meals and hydration reminders
- Include short breaks and movement
- Balance study with recreation
- Be specific with time slots
- Consider travel time for day scholars
- Adapt to the student's actual constraints"""

    async def process(self, user_id: str, data: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Generate a routine."""
        routine_type = data.get("routine_type", "daily")
        constraints = data.get("constraints", {})
        return await self.generate_routine(user_id, routine_type, constraints, db)

    async def generate_routine(
        self,
        user_id: str,
        routine_type: str,
        constraints: Optional[Dict[str, Any]],
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """Generate a personalized routine."""
        # Get user profile
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        # Get recent wellness data for context
        from datetime import date, timedelta
        recent_date = date.today() - timedelta(days=7)
        checkins_result = await db.execute(
            select(DailyCheckin)
            .where(DailyCheckin.user_id == user_id, DailyCheckin.date >= recent_date)
        )
        recent_checkins = checkins_result.scalars().all()

        # Build context
        user_context = {
            "living_situation": user.living_situation.value if user and user.living_situation else "unknown",
            "college_start": user.college_start_time if user else "09:00",
            "college_end": user.college_end_time if user else "17:00",
            "monthly_budget": user.monthly_budget if user else None,
            "sleep_goal": user.sleep_goal_hours if user else 7.0,
            "has_kitchen": user.has_kitchen_access if user else False,
            "food_preferences": user.food_preferences if user else None,
            "fitness_goals": user.fitness_goals if user else None,
            "avg_stress": (
                sum(c.stress_score for c in recent_checkins) / len(recent_checkins)
                if recent_checkins else 5
            ),
            "avg_sleep": (
                sum(c.sleep_hours for c in recent_checkins) / len(recent_checkins)
                if recent_checkins else 7
            ),
        }

        prompt = f"""Generate a {routine_type} routine for a college student with these constraints:

Student Profile:
- Living: {user_context['living_situation']}
- College: {user_context['college_start']} to {user_context['college_end']}
- Budget: ₹{user_context['monthly_budget'] or 'Not specified'}/month
- Sleep goal: {user_context['sleep_goal']} hours
- Kitchen access: {user_context['has_kitchen']}
- Food preferences: {user_context['food_preferences'] or 'No restrictions'}
- Fitness goals: {user_context['fitness_goals'] or 'General wellness'}
- Current stress level: {user_context['avg_stress']}/10
- Current avg sleep: {user_context['avg_sleep']} hours

Additional constraints: {constraints or 'None'}

Return a JSON response with:
{{
    "name": "<descriptive routine name>",
    "schedule": [
        {{"time": "07:00", "activity": "Wake Up", "category": "wellness", "notes": "..."}},
        {{"time": "07:15", "activity": "Morning hygiene + glass of water", "category": "wellness"}},
        ...
    ],
    "tips": [<3-5 tips for following this routine>],
    "estimated_daily_cost": <if applicable>
}}"""

        ai_response = await self.call_ai_json(prompt)

        if not ai_response or "schedule" not in ai_response:
            ai_response = self._default_routine(routine_type)

        # Save routine to database
        routine = Routine(
            user_id=user_id,
            routine_type=routine_type,
            name=ai_response.get("name", f"My {routine_type.title()} Routine"),
            schedule=ai_response["schedule"],
            constraints=constraints,
            is_active="yes",
        )
        db.add(routine)
        await db.flush()
        await db.refresh(routine)

        return {
            "id": routine.id,
            "routine_type": routine.routine_type,
            "name": routine.name,
            "schedule": routine.schedule,
            "constraints": routine.constraints,
            "is_active": routine.is_active,
        }

    def _default_routine(self, routine_type: str) -> Dict[str, Any]:
        """Provide a sensible default routine."""
        if routine_type == "exam":
            return {
                "name": "Exam Survival Routine",
                "schedule": [
                    {"time": "06:30", "activity": "Wake Up", "category": "wellness"},
                    {"time": "06:45", "activity": "Light stretching + hydration", "category": "fitness"},
                    {"time": "07:00", "activity": "Breakfast", "category": "nutrition"},
                    {"time": "07:30", "activity": "Study Block 1 (hardest subject)", "category": "academic"},
                    {"time": "09:30", "activity": "10-min break + snack", "category": "wellness"},
                    {"time": "09:45", "activity": "Study Block 2", "category": "academic"},
                    {"time": "11:45", "activity": "Short walk", "category": "fitness"},
                    {"time": "12:00", "activity": "Lunch", "category": "nutrition"},
                    {"time": "12:45", "activity": "Power nap (20 min)", "category": "wellness"},
                    {"time": "13:15", "activity": "Study Block 3", "category": "academic"},
                    {"time": "15:15", "activity": "Break + healthy snack", "category": "wellness"},
                    {"time": "15:30", "activity": "Study Block 4 (revision)", "category": "academic"},
                    {"time": "17:30", "activity": "Exercise (30 min walk/jog)", "category": "fitness"},
                    {"time": "18:00", "activity": "Dinner", "category": "nutrition"},
                    {"time": "19:00", "activity": "Light review / flashcards", "category": "academic"},
                    {"time": "20:30", "activity": "Relaxation time", "category": "wellness"},
                    {"time": "21:30", "activity": "Prepare for bed", "category": "wellness"},
                    {"time": "22:00", "activity": "Sleep", "category": "wellness"},
                ],
            }

        if routine_type == "weekly":
            return {
                "name": "Weekly Plan",
                "schedule": [
                    {"time": "06:30", "activity": "Wake Up + Morning Yoga (Mon/Wed/Fri)", "category": "fitness"},
                    {"time": "07:00", "activity": "Breakfast + Plan the day", "category": "nutrition"},
                    {"time": "08:00", "activity": "Travel / Commute", "category": "commute"},
                    {"time": "09:00", "activity": "Classes / Work (Mon-Fri)", "category": "academic"},
                    {"time": "12:30", "activity": "Lunch break + short walk", "category": "nutrition"},
                    {"time": "13:30", "activity": "Afternoon study/projects", "category": "academic"},
                    {"time": "16:00", "activity": "Sports/Gym (Tue/Thu) or Free time", "category": "fitness"},
                    {"time": "17:30", "activity": "Errands / Grocery shopping (Wed)", "category": "commute"},
                    {"time": "18:30", "activity": "Dinner + Socialize", "category": "nutrition"},
                    {"time": "19:30", "activity": "Study / Assignments (Mon-Thu)", "category": "academic"},
                    {"time": "20:30", "activity": "Hobby / Entertainment (Fri-Sun)", "category": "social"},
                    {"time": "22:00", "activity": "Wind down + Sleep prep", "category": "wellness"},
                    {"time": "22:30", "activity": "Sleep", "category": "wellness"},
                ],
            }

        if routine_type == "budget_friendly":
            return {
                "name": "Budget-Friendly Routine",
                "schedule": [
                    {"time": "06:30", "activity": "Wake Up + Free home workout", "category": "fitness"},
                    {"time": "07:00", "activity": "Cook breakfast at home (₹20-30)", "category": "nutrition"},
                    {"time": "08:00", "activity": "Walk/bike to college (save transport)", "category": "commute"},
                    {"time": "09:00", "activity": "Classes", "category": "academic"},
                    {"time": "12:30", "activity": "Packed lunch from home (₹30-50)", "category": "nutrition"},
                    {"time": "13:30", "activity": "Library study (free AC + wifi)", "category": "academic"},
                    {"time": "16:00", "activity": "Free campus activities / walk", "category": "fitness"},
                    {"time": "17:30", "activity": "Cook dinner at home (₹40-60)", "category": "nutrition"},
                    {"time": "19:00", "activity": "Study / Free online courses", "category": "academic"},
                    {"time": "20:30", "activity": "Free entertainment (YouTube/books)", "category": "social"},
                    {"time": "21:30", "activity": "Track today's expenses", "category": "wellness"},
                    {"time": "22:00", "activity": "Sleep (free & essential!)", "category": "wellness"},
                ],
            }

        return {
            "name": "Balanced Daily Routine",
            "schedule": [
                {"time": "07:00", "activity": "Wake Up", "category": "wellness"},
                {"time": "07:15", "activity": "Morning routine + breakfast", "category": "nutrition"},
                {"time": "08:00", "activity": "Travel to college", "category": "commute"},
                {"time": "09:00", "activity": "Classes", "category": "academic"},
                {"time": "13:00", "activity": "Lunch", "category": "nutrition"},
                {"time": "14:00", "activity": "Afternoon classes/study", "category": "academic"},
                {"time": "17:00", "activity": "Exercise/Walk", "category": "fitness"},
                {"time": "18:00", "activity": "Dinner", "category": "nutrition"},
                {"time": "19:00", "activity": "Study/Assignments", "category": "academic"},
                {"time": "21:00", "activity": "Free time / Socialize", "category": "wellness"},
                {"time": "22:30", "activity": "Wind down", "category": "wellness"},
                {"time": "23:00", "activity": "Sleep", "category": "wellness"},
            ],
        }
