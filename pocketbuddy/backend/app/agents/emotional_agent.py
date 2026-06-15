"""Emotional Support Agent - Provides empathetic conversations and coping strategies."""

from typing import Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base_agent import BaseAgent


class EmotionalSupportAgent(BaseAgent):
    """Agent responsible for emotional support and guidance."""

    def __init__(self):
        super().__init__(
            name="EmotionalSupportAgent",
            description="Provides empathetic conversations, reflection prompts, stress coping techniques, and encouragement.",
        )

    def _get_system_prompt(self) -> str:
        return """You are an Emotional Support Agent for PocketBuddy, an AI companion for college students.

YOUR ROLE:
- Provide empathetic, warm conversations
- Offer reflection prompts for self-awareness
- Share evidence-based stress coping techniques
- Encourage productivity without pressure
- Validate feelings and experiences

CRITICAL GUIDELINES:
- NEVER diagnose mental health conditions
- NEVER replace professional therapists or counselors
- NEVER minimize someone's feelings
- ALWAYS maintain a supportive, understanding tone
- ALWAYS encourage professional help when patterns seem severe
- If someone expresses self-harm ideation, provide crisis hotline numbers immediately

APPROACH:
- Use active listening language ("It sounds like...", "That must feel...")
- Normalize the student experience
- Offer specific, actionable coping strategies
- Celebrate resilience and small victories
- Keep responses concise but meaningful
- Suggest when talking to a counselor might help (without being pushy)

COPING TECHNIQUES TO SHARE:
- Box breathing (4-4-4-4)
- Progressive muscle relaxation
- 5-4-3-2-1 grounding technique
- Journaling prompts
- Mindful movement
- Study break strategies
- Social connection reminders"""

    async def process(self, user_id: str, data: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Process emotional support request."""
        message = data.get("message", "")
        context = data.get("context", {})
        return await self.provide_support(message, context)

    async def provide_support(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Provide emotional support response."""
        context_str = ""
        if context:
            context_str = f"""
Recent context:
- Average mood: {context.get('avg_mood', 'unknown')}/10
- Average stress: {context.get('avg_stress', 'unknown')}/10
- Sleep pattern: {context.get('avg_sleep', 'unknown')} hours
- Burnout risk: {context.get('burnout_risk', 'unknown')}
"""

        prompt = f"""A college student said: "{message}"
{context_str}
Provide a supportive, empathetic response. Include:
1. Acknowledgment of their feelings
2. A relevant coping technique or perspective
3. A gentle suggestion or question for reflection

Keep the response warm but concise (3-5 sentences max).
Do not use bullet points - write naturally as a supportive companion would."""

        response = await self.call_gemini(prompt)

        return {
            "response": response,
            "agent": "emotional_support",
            "suggestions": await self._generate_suggestions(message),
        }

    async def _generate_suggestions(self, message: str) -> list:
        """Generate follow-up suggestions based on the conversation."""
        prompt = f"""Based on this student message: "{message}"
        
Generate 3 short follow-up actions or conversation starters.
Return as a JSON array of strings. Each should be under 10 words."""

        result = await self.call_ai_json(prompt)
        if isinstance(result, list):
            return result[:3]
        return [
            "Tell me more about how you're feeling",
            "Would a breathing exercise help right now?",
            "Want to set a small goal for today?",
        ]
