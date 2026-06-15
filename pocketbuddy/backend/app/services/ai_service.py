"""AI Service - Common AI operations used across the application."""

import json
from datetime import date
from typing import Dict, Any, Optional

from app.core.config import settings


async def parse_conversational_expense(message: str, user_id: str) -> Dict[str, Any]:
    """Parse a natural language expense message into structured data."""
    import httpx

    prompt = f"""Parse this expense message into structured data.
Message: "{message}"

Extract:
- amount (number, in INR)
- category (one of: food, shopping, travel, entertainment, education, health, rent, utilities, groceries, subscriptions, other)
- description (brief description)
- merchant (if mentioned)
- is_essential (essential or discretionary)

Return ONLY valid JSON:
{{"amount": <number>, "category": "<string>", "description": "<string>", "merchant": null, "is_essential": "<string>"}}"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.3}}

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                if text.startswith("```"):
                    text = text.split("\n", 1)[1].rsplit("```", 1)[0]
                return json.loads(text)
    except Exception:
        pass
    return {}


async def parse_conversational_checkin(message: str, user_id: str) -> Dict[str, Any]:
    """Parse a natural language wellness check-in into structured data."""
    import httpx

    prompt = f"""Parse this wellness message into structured check-in data.
Message: "{message}"

Extract what you can infer:
- mood_score (1-10, where 10 is excellent)
- stress_score (1-10, where 10 is extremely stressed)
- sleep_hours (number)
- meals_skipped (0-3)
- exercise_minutes (number)
- study_hours (number)
- emotional_state (one word: happy, anxious, stressed, calm, tired, motivated, sad, neutral)

Only include fields you can reasonably infer from the message.
Return ONLY valid JSON."""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.3}}

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                if text.startswith("```"):
                    text = text.split("\n", 1)[1].rsplit("```", 1)[0]
                return json.loads(text)
    except Exception:
        pass
    return {}


async def classify_emotional_state(
    mood: int, stress: int, sleep: float, journal: Optional[str] = None
) -> str:
    """Classify emotional state based on metrics."""
    # Rule-based classification (works without API key)
    if mood >= 8 and stress <= 3:
        return "happy"
    elif mood >= 6 and stress <= 4:
        return "calm"
    elif stress >= 8:
        return "overwhelmed"
    elif stress >= 6:
        return "stressed"
    elif mood <= 3:
        return "sad"
    elif sleep < 5:
        return "tired"
    elif mood >= 5:
        return "neutral"
    else:
        return "anxious"
