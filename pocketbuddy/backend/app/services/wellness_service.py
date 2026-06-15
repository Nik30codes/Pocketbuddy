"""Wellness service - score calculations and trend data."""

from datetime import date, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.wellness import DailyCheckin, WellnessScore


async def update_wellness_score(user_id: str, checkin_date: date, db: AsyncSession):
    """Recalculate wellness score after a new check-in."""
    # Get last 7 days of check-ins
    since = checkin_date - timedelta(days=7)
    result = await db.execute(
        select(DailyCheckin)
        .where(DailyCheckin.user_id == user_id, DailyCheckin.date >= since)
        .order_by(DailyCheckin.date.desc())
    )
    checkins = result.scalars().all()

    if not checkins:
        return

    # Calculate scores
    avg_mood = sum(c.mood_score for c in checkins) / len(checkins)
    avg_stress = sum(c.stress_score for c in checkins) / len(checkins)
    avg_sleep = sum(c.sleep_hours for c in checkins) / len(checkins)
    avg_meals_skipped = sum(c.meals_skipped for c in checkins) / len(checkins)
    avg_exercise = sum(c.exercise_minutes for c in checkins) / len(checkins)

    # Normalize to 0-100
    mood_score = avg_mood * 10
    stress_score = (10 - avg_stress) * 10
    sleep_score = min(100, (avg_sleep / 8) * 100)
    nutrition_score = max(0, (3 - avg_meals_skipped) / 3 * 100)
    activity_score = min(100, (avg_exercise / 30) * 100)

    overall = (
        mood_score * 0.25
        + stress_score * 0.25
        + sleep_score * 0.20
        + nutrition_score * 0.15
        + activity_score * 0.15
    )

    # Determine burnout risk
    burnout_risk = "low"
    if avg_stress >= 8 and avg_sleep < 5:
        burnout_risk = "critical"
    elif avg_stress >= 7 or avg_sleep < 5:
        burnout_risk = "high"
    elif avg_stress >= 5 and avg_sleep < 6:
        burnout_risk = "medium"

    # Upsert wellness score
    existing = await db.execute(
        select(WellnessScore).where(
            WellnessScore.user_id == user_id, WellnessScore.date == checkin_date
        )
    )
    score_record = existing.scalar_one_or_none()

    if score_record:
        score_record.overall_wellness = round(overall, 1)
        score_record.sleep_quality = round(sleep_score, 1)
        score_record.stress_management = round(stress_score, 1)
        score_record.nutrition_score = round(nutrition_score, 1)
        score_record.activity_score = round(activity_score, 1)
        score_record.mood_stability = round(mood_score, 1)
        score_record.burnout_risk = burnout_risk
    else:
        score_record = WellnessScore(
            user_id=user_id,
            date=checkin_date,
            overall_wellness=round(overall, 1),
            sleep_quality=round(sleep_score, 1),
            stress_management=round(stress_score, 1),
            nutrition_score=round(nutrition_score, 1),
            activity_score=round(activity_score, 1),
            mood_stability=round(mood_score, 1),
            burnout_risk=burnout_risk,
        )
        db.add(score_record)


async def get_trend_data(user_id: str, days: int, db: AsyncSession) -> dict:
    """Get wellness trend data for charts."""
    since = date.today() - timedelta(days=days)
    result = await db.execute(
        select(DailyCheckin)
        .where(DailyCheckin.user_id == user_id, DailyCheckin.date >= since)
        .order_by(DailyCheckin.date.asc())
    )
    checkins = result.scalars().all()

    # Also get wellness scores
    scores_result = await db.execute(
        select(WellnessScore)
        .where(WellnessScore.user_id == user_id, WellnessScore.date >= since)
        .order_by(WellnessScore.date.asc())
    )
    scores = scores_result.scalars().all()

    return {
        "dates": [str(c.date) for c in checkins],
        "mood_scores": [float(c.mood_score) for c in checkins],
        "stress_scores": [float(c.stress_score) for c in checkins],
        "sleep_hours": [float(c.sleep_hours) for c in checkins],
        "overall_wellness": [float(s.overall_wellness) for s in scores],
    }
