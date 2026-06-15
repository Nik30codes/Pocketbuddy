"""Authentication endpoints."""

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, get_current_user
from app.models.user import User
from app.schemas.user import (
    UserRegister,
    UserLogin,
    UserProfile,
    UserResponse,
    TokenResponse,
    GoogleAuthRequest,
)

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    # Check if email exists
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        id=str(uuid.uuid4()),
        email=data.email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
    )
    db.add(user)
    await db.flush()

    token = create_access_token({"sub": user.id, "email": user.email})
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
        ),
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login with email and password."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token = create_access_token({"sub": user.id, "email": user.email})
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/google", response_model=TokenResponse)
async def google_auth(data: GoogleAuthRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate via Google OAuth."""
    from google.oauth2 import id_token
    from google.auth.transport import requests

    try:
        from app.core.config import settings
        idinfo = id_token.verify_oauth2_token(
            data.credential, requests.Request(), settings.GOOGLE_CLIENT_ID
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token",
        )

    email = idinfo["email"]
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            id=str(uuid.uuid4()),
            email=email,
            full_name=idinfo.get("name", ""),
            avatar_url=idinfo.get("picture"),
            auth_provider="google",
            is_verified=True,
        )
        db.add(user)
        await db.flush()

    token = create_access_token({"sub": user.id, "email": user.email})
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    profile: UserProfile,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update user profile."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    for field, value in profile.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    await db.flush()
    return UserResponse.model_validate(user)


@router.delete("/account")
async def delete_account(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Permanently delete user account and all associated data."""
    from sqlalchemy import delete as sql_delete
    from app.models.financial import Expense, Income, Budget, BankStatement
    from app.models.wellness import DailyCheckin, WellnessScore
    from app.models.ai_insights import AIInsight, BurnoutAlert, WeeklyReport, Routine
    from app.models.chat import ChatMessage

    # Delete all user data
    await db.execute(sql_delete(ChatMessage).where(ChatMessage.user_id == user_id))
    await db.execute(sql_delete(Expense).where(Expense.user_id == user_id))
    await db.execute(sql_delete(Income).where(Income.user_id == user_id))
    await db.execute(sql_delete(Budget).where(Budget.user_id == user_id))
    await db.execute(sql_delete(DailyCheckin).where(DailyCheckin.user_id == user_id))
    await db.execute(sql_delete(WellnessScore).where(WellnessScore.user_id == user_id))
    await db.execute(sql_delete(AIInsight).where(AIInsight.user_id == user_id))
    await db.execute(sql_delete(BurnoutAlert).where(BurnoutAlert.user_id == user_id))
    await db.execute(sql_delete(WeeklyReport).where(WeeklyReport.user_id == user_id))
    await db.execute(sql_delete(Routine).where(Routine.user_id == user_id))

    # Delete the user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user:
        await db.delete(user)

    return {"message": "Account deleted successfully"}
