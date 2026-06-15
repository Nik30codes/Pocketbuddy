"""Wellness Agent - Analyzes sleep, stress, mood, and lifestyle patterns."""

from typing import Any, Dict, List
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.agents.base_agent import BaseAgent
from app.models.wellness import DailyCheckin


class WellnessAgent(BaseAgent):
    """Agent responsible for wellness analysis and scoring."""

    def __init__(self):
        super().__init__(
            name="WellnessAgent",
            description="Analyzes sleep, stress, mood, meal consistency, and physical activity patterns.",
        )

    def _get_system_prompt(self) -> str:
        return """You are a Wellness Agent for PocketBuddy, an AI wellness assistant for college students.
Your role is to:
- Analyze sleep patterns and quality
- Monitor stress levels and trends
- Track mood patterns and emotional wellbeing
- Assess meal consistency and nutrition
- Evaluate physical activity levels
- Generate wellness scores and reports

IMPORTANT GUIDELINES:
- Never diagnose medical or mental health conditions
- Only provide risk indicators and supportive recommendations
- Encourage professional help when patterns are concerning
- Be empathetic, supportive, and non-judgmental
- Consider student lifestyle constraints (late nights, irregular schedules)
- Celebrate small wins and improvements"""

    async def process(self, user_id: str, data: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Process wellness data and generate insights."""
        checkins = await self._get_recent_checkins(user_id, db)
        if not checkins:
            return self._default_wellness_response()
        
        analysis = await self._analyze_wellness(checkins)
        return analysis

    async def _get_recent_checkins(self, user_id: str, db: AsyncSession, days: int = 14) -> List[Dict]:
        """Get recent check-in data."""
        since = date.today() - timedelta(days=days)
        result = await db.execute(
            select(DailyCheckin)
            .where(DailyCheckin.user_id == user_id, DailyCheckin.date >= since)
            .order_by(DailyCheckin.date.desc())
        )
        checkins = result.scalars().all()
        return [
            {
                "date": str(c.date),
                "mood": c.mood_score,
                "stress": c.stress_score,
                "sleep": c.sleep_hours,
                "meals_skipped": c.meals_skipped,
                "water": c.water_glasses,
                "study": c.study_hours,
                "exercise": c.exercise_minutes,
                "emotion": c.emotional_state,
            }
            for c in checkins
        ]

    async def _analyze_wellness(self, checkins: List[Dict]) -> Dict[str, Any]:
        """Use AI to analyze wellness patterns."""
        prompt = f"""Analyze this student's wellness data from the past {len(checkins)} days:

Check-in data: {checkins}

Calculate and provide a JSON response with:
{{
    "overall_wellness_score": <0-100>,
    "sleep_quality_score": <0-100>,
    "stress_management_score": <0-100>,
    "nutrition_score": <0-100>,
    "activity_score": <0-100>,
    "mood_stability_score": <0-100>,
    "trends": {{
        "mood": "improving|stable|declining",
        "sleep": "improving|stable|declining",
        "stress": "improving|stable|declining"
    }},
    "concerns": [<list of identified concerns>],
    "positive_patterns": [<list of positive patterns>],
    "recommendations": [<3-5 actionable recommendations>]
}}"""

        return await self.call_ai_json(prompt)

    def _default_wellness_response(self) -> Dict[str, Any]:
        """Return default response when no data is available."""
        return {
            "overall_wellness_score": 50,
            "sleep_quality_score": 50,
            "stress_management_score": 50,
            "nutrition_score": 50,
            "activity_score": 50,
            "mood_stability_score": 50,
            "trends": {"mood": "stable", "sleep": "stable", "stress": "stable"},
            "concerns": [],
            "positive_patterns": [],
            "recommendations": [
                "Start logging your daily check-ins to get personalized insights",
                "Try to maintain a consistent sleep schedule",
                "Stay hydrated - aim for 8 glasses of water daily",
            ],
        }

    async def calculate_wellness_score(self, user_id: str, db: AsyncSession) -> Dict[str, float]:
        """Calculate composite wellness scores."""
        checkins = await self._get_recent_checkins(user_id, db, days=7)
        
        if not checkins:
            return {
                "overall": 50.0,
                "sleep": 50.0,
                "stress": 50.0,
                "nutrition": 50.0,
                "activity": 50.0,
                "mood": 50.0,
            }

        # Calculate component scores
        avg_mood = sum(c["mood"] for c in checkins) / len(checkins)
        avg_stress = sum(c["stress"] for c in checkins) / len(checkins)
        avg_sleep = sum(c["sleep"] for c in checkins) / len(checkins)
        avg_meals_skipped = sum(c["meals_skipped"] for c in checkins) / len(checkins)
        avg_exercise = sum(c["exercise"] for c in checkins) / len(checkins)

        # Normalize to 0-100 scores
        mood_score = avg_mood * 10
        stress_score = (10 - avg_stress) * 10  # Lower stress = higher score
        sleep_score = min(100, (avg_sleep / 8) * 100)  # 8 hours = 100%
        nutrition_score = max(0, (3 - avg_meals_skipped) / 3 * 100)
        activity_score = min(100, (avg_exercise / 30) * 100)  # 30 min = 100%

        overall = (mood_score * 0.25 + stress_score * 0.25 + sleep_score * 0.2 +
                   nutrition_score * 0.15 + activity_score * 0.15)

        return {
            "overall": round(overall, 1),
            "sleep": round(sleep_score, 1),
            "stress": round(stress_score, 1),
            "nutrition": round(nutrition_score, 1),
            "activity": round(activity_score, 1),
            "mood": round(mood_score, 1),
        }
