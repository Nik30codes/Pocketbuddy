"""API v1 router - combines all endpoint routers."""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, financial, wellness, ai_insights, chat, reports, notifications

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(financial.router, prefix="/financial", tags=["Financial"])
api_router.include_router(wellness.router, prefix="/wellness", tags=["Wellness"])
api_router.include_router(ai_insights.router, prefix="/ai", tags=["AI Insights"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
