"""Wellness endpoints: check-ins, scores, trends."""

from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.wellness import DailyCheckin, WellnessScore
from app.schemas.wellness import (
    DailyCheckinCreate,
    DailyCheckinResponse,
    WellnessScoreResponse,
    WellnessTrend,
    ConversationalCheckin,
)

router = APIRouter()


@router.post("/checkin", response_model=DailyCheckinResponse, status_code=201)
async def create_checkin(
    data: DailyCheckinCreate,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit a daily wellness check-in."""
    # Classify emotional state using AI
    from app.services.ai_service import classify_emotional_state

    emotional_state = await classify_emotional_state(
        mood=data.mood_score,
        stress=data.stress_score,
        sleep=data.sleep_hours,
        journal=data.journal_entry,
    )

    checkin = DailyCheckin(
        user_id=user_id,
        date=data.date,
        mood_score=data.mood_score,
        stress_score=data.stress_score,
        sleep_hours=data.sleep_hours,
        meals_skipped=data.meals_skipped,
        water_glasses=data.water_glasses,
        study_hours=data.study_hours,
        exercise_minutes=data.exercise_minutes,
        journal_entry=data.journal_entry,
        gratitude_note=data.gratitude_note,
        emotional_state=emotional_state,
    )
    db.add(checkin)
    await db.flush()
    await db.refresh(checkin)

    # Trigger wellness score recalculation
    from app.services.wellness_service import update_wellness_score
    await update_wellness_score(user_id, data.date, db)

    # Trigger notification engine
    from app.services.notification_engine import generate_notifications
    await generate_notifications(user_id, db)

    return checkin


@router.get("/checkins", response_model=List[DailyCheckinResponse])
async def get_checkins(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(default=30, le=90),
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get recent check-ins."""
    query = select(DailyCheckin).where(DailyCheckin.user_id == user_id)

    if start_date:
        query = query.where(DailyCheckin.date >= start_date)
    if end_date:
        query = query.where(DailyCheckin.date <= end_date)

    query = query.order_by(DailyCheckin.date.desc()).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/score", response_model=WellnessScoreResponse)
async def get_wellness_score(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the latest wellness score."""
    result = await db.execute(
        select(WellnessScore)
        .where(WellnessScore.user_id == user_id)
        .order_by(WellnessScore.date.desc())
        .limit(1)
    )
    score = result.scalar_one_or_none()
    if not score:
        return WellnessScoreResponse(
            overall_wellness=50.0,
            sleep_quality=50.0,
            stress_management=50.0,
            nutrition_score=50.0,
            activity_score=50.0,
            mood_stability=50.0,
            burnout_risk="low",
        )
    return score


@router.get("/trends", response_model=WellnessTrend)
async def get_wellness_trends(
    days: int = Query(default=30, le=90),
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get wellness trends over time."""
    from app.services.wellness_service import get_trend_data
    return await get_trend_data(user_id, days, db)


@router.post("/checkin/conversational", response_model=DailyCheckinResponse)
async def log_conversational_checkin(
    data: ConversationalCheckin,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Log wellness data from natural language."""
    from app.services.ai_service import parse_conversational_checkin
    checkin_data = await parse_conversational_checkin(data.message, user_id)

    checkin = DailyCheckin(
        user_id=user_id,
        date=checkin_data.get("date", date.today()),
        mood_score=checkin_data["mood_score"],
        stress_score=checkin_data["stress_score"],
        sleep_hours=checkin_data["sleep_hours"],
        meals_skipped=checkin_data.get("meals_skipped", 0),
        water_glasses=checkin_data.get("water_glasses", 0),
        study_hours=checkin_data.get("study_hours", 0),
        exercise_minutes=checkin_data.get("exercise_minutes", 0),
        emotional_state=checkin_data.get("emotional_state"),
    )
    db.add(checkin)
    await db.flush()
    await db.refresh(checkin)
    return checkin
