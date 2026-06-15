"""Notifications API endpoint."""

from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.notification import Notification

router = APIRouter()


@router.get("")
async def get_notifications(
    unread_only: bool = False,
    notification_type: str = None,
    limit: int = Query(default=30, le=100),
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user notifications."""
    query = select(Notification).where(Notification.user_id == user_id)

    if unread_only:
        query = query.where(Notification.is_read == False)
    if notification_type:
        query = query.where(Notification.notification_type == notification_type)

    query = query.order_by(Notification.created_at.desc()).limit(limit)
    result = await db.execute(query)
    notifications = result.scalars().all()

    return [
        {
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "notification_type": n.notification_type,
            "priority": n.priority,
            "action_url": n.action_url,
            "is_read": n.is_read,
            "created_at": str(n.created_at),
        }
        for n in notifications
    ]


@router.get("/unread-count")
async def get_unread_count(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get count of unread notifications."""
    from sqlalchemy import func
    result = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == user_id, Notification.is_read == False
        )
    )
    count = result.scalar() or 0
    return {"count": count}


@router.post("/{notification_id}/read")
async def mark_as_read(
    notification_id: int,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a notification as read."""
    await db.execute(
        update(Notification)
        .where(Notification.id == notification_id, Notification.user_id == user_id)
        .values(is_read=True)
    )
    return {"status": "ok"}


@router.post("/mark-all-read")
async def mark_all_read(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark all notifications as read."""
    await db.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read == False)
        .values(is_read=True)
    )
    return {"status": "ok"}


@router.post("/generate")
async def trigger_notification_generation(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger the notification engine (also runs automatically on key actions)."""
    from app.services.notification_engine import generate_notifications
    new = await generate_notifications(user_id, db)
    return {"generated": len(new), "message": f"{len(new)} new notifications generated"}
