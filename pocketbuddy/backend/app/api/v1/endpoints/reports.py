"""Reports endpoints: weekly reports, PDF export."""

from typing import List
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.ai_insights import WeeklyReport
from app.schemas.ai_schemas import WeeklyReportResponse

router = APIRouter()


@router.get("/weekly", response_model=List[WeeklyReportResponse])
async def get_weekly_reports(
    limit: int = 10,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get weekly reports."""
    result = await db.execute(
        select(WeeklyReport)
        .where(WeeklyReport.user_id == user_id)
        .order_by(WeeklyReport.week_start.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/monthly")
async def get_monthly_reports(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all monthly reports."""
    from app.services.monthly_report_service import get_all_monthly_reports
    return await get_all_monthly_reports(user_id, db)


@router.post("/monthly/generate")
async def generate_monthly_report_endpoint(
    month: str = None,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate monthly report. Defaults to previous month if not specified."""
    from app.services.monthly_report_service import generate_monthly_report
    from datetime import date

    if not month:
        today = date.today()
        # Default to previous month
        if today.month == 1:
            month = f"{today.year - 1}-12"
        else:
            month = f"{today.year}-{today.month - 1:02d}"

    return await generate_monthly_report(user_id, month, db)


@router.post("/weekly/generate", response_model=WeeklyReportResponse)
async def generate_weekly_report(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a new weekly report."""
    from app.agents.coach_agent import StudentLifeCoachAgent

    coach = StudentLifeCoachAgent()
    report = await coach.generate_weekly_report(user_id, db)
    return report


@router.get("/weekly/{report_id}/pdf")
async def export_report_pdf(
    report_id: int,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export weekly report as PDF."""
    from app.services.report_service import generate_report_pdf

    result = await db.execute(
        select(WeeklyReport).where(
            WeeklyReport.id == report_id,
            WeeklyReport.user_id == user_id,
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Report not found")

    pdf_buffer = await generate_report_pdf(report)
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=weekly_report_{report_id}.pdf"},
    )
