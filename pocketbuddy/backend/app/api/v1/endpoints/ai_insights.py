"""AI Insights endpoints: routines, burnout, predictions."""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.ai_insights import AIInsight, BurnoutAlert, Routine
from app.schemas.ai_schemas import (
    RoutineRequest,
    RoutineResponse,
    InsightResponse,
    BurnoutAlertResponse,
    PredictiveAnalytics,
)

router = APIRouter()


@router.post("/routine/generate", response_model=RoutineResponse)
async def generate_routine(
    data: RoutineRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a personalized routine using AI."""
    from app.agents.routine_agent import RoutinePlanningAgent

    agent = RoutinePlanningAgent()
    routine = await agent.generate_routine(user_id, data.routine_type, data.constraints, db)
    return routine


@router.get("/routines", response_model=List[RoutineResponse])
async def get_routines(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's saved routines."""
    result = await db.execute(
        select(Routine)
        .where(Routine.user_id == user_id)
        .order_by(Routine.created_at.desc())
    )
    return result.scalars().all()


@router.get("/insights", response_model=List[InsightResponse])
async def get_insights(
    agent_type: str = None,
    limit: int = 20,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get AI-generated insights."""
    query = select(AIInsight).where(AIInsight.user_id == user_id)
    if agent_type:
        query = query.where(AIInsight.agent_type == agent_type)
    query = query.order_by(AIInsight.created_at.desc()).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/burnout/status", response_model=BurnoutAlertResponse)
async def get_burnout_status(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current burnout risk assessment."""
    from app.agents.burnout_agent import BurnoutDetectionAgent

    agent = BurnoutDetectionAgent()
    return await agent.assess_burnout_risk(user_id, db)


@router.get("/predictions", response_model=PredictiveAnalytics)
async def get_predictions(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get predictive analytics."""
    from app.services.prediction_service import generate_predictions
    return await generate_predictions(user_id, db)


@router.post("/exam-mode/activate")
async def activate_exam_mode(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Activate exam survival mode."""
    from app.agents.routine_agent import RoutinePlanningAgent
    from app.agents.coach_agent import StudentLifeCoachAgent

    routine_agent = RoutinePlanningAgent()
    coach_agent = StudentLifeCoachAgent()

    exam_routine = await routine_agent.generate_routine(
        user_id, "exam", {"mode": "survival"}, db
    )
    exam_plan = await coach_agent.generate_exam_plan(user_id, db)

    return {
        "routine": exam_routine,
        "plan": exam_plan,
        "message": "Exam survival mode activated. Stay focused and take care of yourself!",
    }


@router.get("/routine/yesterday-review")
async def get_yesterday_review(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get yesterday's routine activities for review checkboxes."""
    from datetime import date, timedelta
    yesterday = date.today() - timedelta(days=1)

    # Get the most recent active routine
    result = await db.execute(
        select(Routine)
        .where(Routine.user_id == user_id, Routine.is_active == "yes")
        .order_by(Routine.created_at.desc())
        .limit(1)
    )
    routine = result.scalar_one_or_none()

    if not routine or not routine.schedule:
        return {"activities": [], "routine_id": None, "date": str(yesterday)}

    activities = [item.get("activity", "") for item in routine.schedule if item.get("activity")]
    return {"activities": activities, "routine_id": routine.id, "date": str(yesterday)}


from pydantic import BaseModel as PydanticBaseModel
from typing import Optional as Opt, List as Lst

class RoutineLogInput(PydanticBaseModel):
    completed: list = []
    skipped: list = []
    routine_id: Opt[int] = None
    date: Opt[str] = None

    class Config:
        extra = "allow"

@router.post("/routine/log-completion")
async def log_routine_completion(
    data: RoutineLogInput,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save which activities the user completed yesterday."""
    from datetime import date as date_mod, timedelta
    from app.models.routine_log import RoutineLog

    completed = data.completed
    skipped = data.skipped
    routine_id = data.routine_id
    log_date = data.date or str(date_mod.today() - timedelta(days=1))

    total = len(completed) + len(skipped)
    rate = int((len(completed) / total) * 100) if total > 0 else 0

    from datetime import datetime as dt
    log = RoutineLog(
        user_id=user_id,
        date=date_mod.fromisoformat(log_date),
        routine_id=routine_id,
        completed_activities=completed,
        skipped_activities=skipped,
        completion_rate=rate,
    )
    db.add(log)
    await db.flush()

    return {"status": "saved", "completion_rate": rate, "message": f"Great! You completed {len(completed)}/{total} activities ({rate}%)."}


@router.get("/routine/logs")
async def get_routine_logs(
    limit: int = 7,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get recent routine completion logs."""
    from app.models.routine_log import RoutineLog

    result = await db.execute(
        select(RoutineLog)
        .where(RoutineLog.user_id == user_id)
        .order_by(RoutineLog.date.desc())
        .limit(limit)
    )
    logs = result.scalars().all()
    return [
        {"date": str(l.date), "completed": l.completed_activities, "skipped": l.skipped_activities, "completion_rate": l.completion_rate}
        for l in logs
    ]
