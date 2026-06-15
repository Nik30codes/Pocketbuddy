"""Burnout Detection Agent - Detects patterns indicating burnout risk."""

from typing import Any, Dict
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.agents.base_agent import BaseAgent
from app.models.wellness import DailyCheckin
from app.models.ai_insights import BurnoutAlert


class BurnoutDetectionAgent(BaseAgent):
    """Agent responsible for detecting burnout patterns and generating alerts."""

    def __init__(self):
        super().__init__(
            name="BurnoutDetectionAgent",
            description="Detects burnout patterns: high stress, low sleep, academic overload, irregular meals, negative sentiment.",
        )

    def _get_system_prompt(self) -> str:
        return """You are a Burnout Detection Agent for PocketBuddy.
Your role is to identify early warning signs of burnout in college students.

IMPORTANT DISCLAIMERS:
- You do NOT provide medical diagnoses
- You only identify risk indicators
- You provide supportive recommendations
- You always encourage professional help for serious concerns

Burnout indicators you monitor:
- Consistently high stress (7+ for multiple days)
- Sleep deprivation (< 5 hours for multiple days)
- Declining mood trends
- Skipped meals frequently
- Excessive study hours without breaks
- Lack of physical activity
- Negative emotional patterns

Risk Levels:
- Low: Minor fluctuations, generally healthy patterns
- Medium: Some concerning patterns emerging, worth monitoring
- High: Multiple red flags, immediate self-care needed
- Critical: Severe patterns detected, professional support recommended"""

    async def process(self, user_id: str, data: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Process data for burnout detection."""
        return await self.assess_burnout_risk(user_id, db)

    async def assess_burnout_risk(self, user_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Assess current burnout risk level."""
        # Get last 14 days of check-ins
        since = date.today() - timedelta(days=14)
        result = await db.execute(
            select(DailyCheckin)
            .where(DailyCheckin.user_id == user_id, DailyCheckin.date >= since)
            .order_by(DailyCheckin.date.desc())
        )
        checkins = result.scalars().all()

        if not checkins:
            return {
                "risk_level": "low",
                "risk_score": 15.0,
                "contributing_factors": ["Insufficient data for accurate assessment"],
                "recommendations": [
                    "Start logging daily check-ins for personalized burnout monitoring",
                    "Maintain a regular sleep schedule",
                    "Take breaks between study sessions",
                ],
            }

        # Calculate risk factors
        risk_factors = self._calculate_risk_factors(checkins)
        risk_score = self._calculate_risk_score(risk_factors)
        risk_level = self._determine_risk_level(risk_score)

        # Generate AI-powered recommendations
        recommendations = await self._generate_recommendations(
            risk_level, risk_factors, checkins
        )

        # Store alert if medium or higher
        if risk_level in ("medium", "high", "critical"):
            alert = BurnoutAlert(
                user_id=user_id,
                risk_level=risk_level,
                risk_score=risk_score,
                contributing_factors=risk_factors["factors"],
                recommendations=recommendations,
            )
            db.add(alert)

        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "contributing_factors": risk_factors["factors"],
            "recommendations": recommendations,
        }

    def _calculate_risk_factors(self, checkins) -> Dict[str, Any]:
        """Calculate individual risk factor scores."""
        factors = []
        scores = {}

        # Stress analysis
        avg_stress = sum(c.stress_score for c in checkins) / len(checkins)
        high_stress_days = sum(1 for c in checkins if c.stress_score >= 7)
        if avg_stress >= 7:
            factors.append("Consistently high stress levels")
            scores["stress"] = min(100, avg_stress * 12)
        elif high_stress_days >= 5:
            factors.append(f"High stress on {high_stress_days} of last {len(checkins)} days")
            scores["stress"] = min(100, high_stress_days * 15)

        # Sleep analysis
        avg_sleep = sum(c.sleep_hours for c in checkins) / len(checkins)
        low_sleep_days = sum(1 for c in checkins if c.sleep_hours < 5)
        if avg_sleep < 5:
            factors.append("Severe sleep deprivation")
            scores["sleep"] = 90
        elif avg_sleep < 6:
            factors.append("Insufficient sleep pattern")
            scores["sleep"] = 65
        elif low_sleep_days >= 3:
            factors.append(f"Low sleep on {low_sleep_days} days")
            scores["sleep"] = 50

        # Mood decline
        if len(checkins) >= 5:
            recent_mood = sum(c.mood_score for c in checkins[:3]) / 3
            older_mood = sum(c.mood_score for c in checkins[-3:]) / 3
            if recent_mood < older_mood - 2:
                factors.append("Declining mood trend")
                scores["mood"] = 60

        # Meal skipping
        avg_meals_skipped = sum(c.meals_skipped for c in checkins) / len(checkins)
        if avg_meals_skipped >= 1.5:
            factors.append("Frequently skipping meals")
            scores["nutrition"] = 55

        # Overwork
        avg_study = sum(c.study_hours for c in checkins) / len(checkins)
        if avg_study > 10:
            factors.append("Excessive study hours without adequate rest")
            scores["overwork"] = 70

        # Low activity
        avg_exercise = sum(c.exercise_minutes for c in checkins) / len(checkins)
        if avg_exercise < 10:
            factors.append("Minimal physical activity")
            scores["activity"] = 40

        return {"factors": factors, "scores": scores}

    def _calculate_risk_score(self, risk_factors: Dict) -> float:
        """Calculate overall burnout risk score (0-100)."""
        scores = risk_factors["scores"]
        if not scores:
            return 10.0

        # Weighted average of risk factors
        weights = {
            "stress": 0.30,
            "sleep": 0.25,
            "mood": 0.20,
            "nutrition": 0.10,
            "overwork": 0.10,
            "activity": 0.05,
        }

        total_weight = sum(weights.get(k, 0.1) for k in scores)
        weighted_sum = sum(scores[k] * weights.get(k, 0.1) for k in scores)

        return round(weighted_sum / total_weight if total_weight > 0 else 10.0, 1)

    def _determine_risk_level(self, score: float) -> str:
        """Determine risk level from score."""
        if score >= 80:
            return "critical"
        elif score >= 60:
            return "high"
        elif score >= 40:
            return "medium"
        return "low"

    async def _generate_recommendations(
        self, risk_level: str, risk_factors: Dict, checkins
    ) -> list:
        """Generate personalized recommendations."""
        if risk_level == "low":
            return [
                "Keep up the good work! Your patterns look healthy.",
                "Consider setting up a consistent routine for even better results.",
                "Remember to celebrate your small wins.",
            ]

        prompt = f"""A college student has a burnout risk level of '{risk_level}'.
Contributing factors: {risk_factors['factors']}

Generate 5 specific, actionable recommendations to help reduce burnout risk.
Focus on immediate, practical steps a student can take today.
Be supportive and encouraging, not prescriptive.

Return as a JSON array of strings."""

        result = await self.call_ai_json(prompt)
        if isinstance(result, list):
            return result
        return result.get("recommendations", [
            "Take a 15-minute break every hour during study sessions",
            "Prioritize 7-8 hours of sleep tonight",
            "Have a proper meal - your body needs fuel",
            "Try a 10-minute walk outside for fresh air",
            "Consider talking to a counselor if stress persists",
        ])
