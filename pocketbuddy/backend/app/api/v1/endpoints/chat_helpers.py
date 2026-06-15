"""Chat helper functions for image analysis and expense extraction."""

import re
import httpx
from datetime import date
from app.core.config import settings
from app.models.financial import Expense


async def analyze_image_with_ai(image_base64: str, content_type: str, message: str) -> str:
    """Analyze bill image using Groq Vision or Gemini."""
    if settings.GROQ_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}", "Content-Type": "application/json"},
                    json={
                        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
                        "messages": [{"role": "user", "content": [
                            {"type": "text", "text": f"Analyze this bill/receipt. Extract items with amounts in ₹. Categorize each. Give total. User note: {message}"},
                            {"type": "image_url", "image_url": {"url": f"data:{content_type};base64,{image_base64}"}}
                        ]}],
                        "temperature": 0.3, "max_tokens": 1000,
                    },
                )
                if response.status_code == 200:
                    return response.json()["choices"][0]["message"]["content"].strip()
        except Exception:
            pass

    if settings.GEMINI_API_KEY:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
            payload = {"contents": [{"parts": [
                {"text": f"Analyze this bill. Extract items, amounts in ₹, categories. Give total. Note: {message}"},
                {"inline_data": {"mime_type": content_type, "data": image_base64}}
            ]}], "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1000}}
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    return response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception:
            pass

    return "I received your bill! To process it, please type the expenses manually like: 'spent ₹200 on food'"


async def auto_save_expenses(ai_response: str, user_id: str, db) -> int:
    """Extract total from AI response and save as expense."""
    total_match = re.search(r'[Tt]otal[:\s]*₹?\s*([\d,]+(?:\.\d+)?)', ai_response)
    if not total_match:
        return 0

    try:
        amount = float(total_match.group(1).replace(',', ''))
        if amount <= 0:
            return 0
    except ValueError:
        return 0

    response_lower = ai_response.lower()
    category = "other"
    if any(w in response_lower for w in ["food", "restaurant", "meal", "lunch", "dinner"]):
        category = "food"
    elif any(w in response_lower for w in ["grocery", "groceries", "vegetable"]):
        category = "groceries"
    elif any(w in response_lower for w in ["shop", "cloth", "amazon"]):
        category = "shopping"

    expense = Expense(
        user_id=user_id, amount=amount, category=category,
        description="Bill upload", date=date.today(), source="bill_upload",
        is_essential="essential" if category in ["food", "groceries"] else "discretionary",
    )
    db.add(expense)
    return 1
