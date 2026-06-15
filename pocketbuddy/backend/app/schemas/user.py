"""User schemas."""

from typing import Optional
from pydantic import BaseModel, EmailStr


class UserRegister(BaseModel):
    email: str
    password: str
    full_name: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserProfile(BaseModel):
    full_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    college_name: Optional[str] = None
    living_situation: Optional[str] = None
    monthly_budget: Optional[float] = None
    food_preferences: Optional[str] = None
    fitness_goals: Optional[str] = None
    sleep_goal_hours: Optional[float] = 7.0
    has_kitchen_access: Optional[bool] = False
    college_start_time: Optional[str] = None
    college_end_time: Optional[str] = None
    avatar_url: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    avatar_url: Optional[str] = None
    age: Optional[int] = None
    college_name: Optional[str] = None
    living_situation: Optional[str] = None
    monthly_budget: Optional[float] = None
    is_verified: bool = False

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class GoogleAuthRequest(BaseModel):
    credential: str
