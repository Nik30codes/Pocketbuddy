"""Base agent class for all AI agents."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import json
import structlog

from app.core.config import settings
from app.core.redis import cache_get, cache_set

logger = structlog.get_logger()


class BaseAgent(ABC):
    """Abstract base class for all PocketBuddy AI agents."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.logger = logger.bind(agent=name)

    @abstractmethod
    async def process(self, user_id: str, data: Dict[str, Any], db: Any) -> Dict[str, Any]:
        """Process data and return insights."""
        pass

    async def call_gemini(self, prompt: str, system_instruction: str = "") -> str:
        """Call AI API for processing. Uses free Hugging Face Inference API."""
        import httpx

        # Use HuggingFace free inference API (no key needed for some models)
        # Or Gemini if key is available
        if settings.GEMINI_API_KEY:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2000}
            }
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(url, json=payload)
                    if response.status_code == 200:
                        data = response.json()
                        return data["candidates"][0]["content"]["parts"][0]["text"]
            except Exception as e:
                self.logger.error("Gemini API error", error=str(e))

        # Fallback: use local rule-based responses
        return self._generate_local_response(prompt)

    def _generate_local_response(self, prompt: str) -> str:
        """Generate intelligent responses without external API using rule-based logic."""
        prompt_lower = prompt.lower()
        
        # Financial responses
        if any(w in prompt_lower for w in ['spend', 'budget', 'money', 'expense', 'income', 'save', 'cost']):
            if 'how' in prompt_lower and 'save' in prompt_lower:
                return ("Here are some tips to save more:\n\n"
                        "1. Track every expense — awareness is the first step\n"
                        "2. Use the 50/30/20 rule: 50% needs, 30% wants, 20% savings\n"
                        "3. Cook meals at home when possible — eating out adds up fast\n"
                        "4. Cancel unused subscriptions\n"
                        "5. Set a daily spending limit and stick to it\n\n"
                        "Would you like me to analyze your spending patterns?")
            elif 'left' in prompt_lower or 'remain' in prompt_lower:
                return ("I can see your budget situation. Here's what I suggest:\n\n"
                        "1. Prioritize essentials — food, transport, academic supplies\n"
                        "2. Look for free entertainment — campus events, library, parks\n"
                        "3. Meal prep for the rest of the month to control food costs\n"
                        "4. Avoid impulse purchases — wait 24 hours before buying\n\n"
                        "Log your expenses here and I'll track your daily budget for you!")
            else:
                return ("I'm tracking your financial health! Here's what you can do:\n\n"
                        "• Add expenses using the Financial tab or just tell me naturally\n"
                        "• Set monthly budgets per category\n"
                        "• Check your Financial Wellness Score on the dashboard\n\n"
                        "Try saying something like 'Spent ₹200 on lunch' and I'll log it for you.")

        # Wellness/stress responses  
        if any(w in prompt_lower for w in ['stress', 'anxious', 'overwhelm', 'tired', 'exhaust', 'burnout']):
            return ("I hear you, and it's okay to feel this way. College can be intense.\n\n"
                    "Here are some things that might help right now:\n\n"
                    "🫁 Try box breathing: Inhale 4s → Hold 4s → Exhale 4s → Hold 4s\n"
                    "🚶 Take a 10-minute walk outside\n"
                    "📝 Write down 3 things you're grateful for today\n"
                    "💤 Prioritize sleep tonight — everything feels harder when tired\n\n"
                    "Remember: taking breaks isn't lazy, it's strategic. "
                    "Would you like me to generate a balanced routine for you?")

        # Sleep responses
        if any(w in prompt_lower for w in ['sleep', 'insomnia', 'cant sleep', 'tired']):
            return ("Sleep is crucial for everything — memory, mood, and focus.\n\n"
                    "Tips for better sleep:\n"
                    "• Set a consistent bedtime (even on weekends)\n"
                    "• No screens 30 minutes before bed\n"
                    "• Keep your room cool and dark\n"
                    "• Try the 4-7-8 breathing technique\n"
                    "• Avoid caffeine after 2 PM\n\n"
                    "Log your sleep hours in the daily check-in so I can track patterns!")

        # Routine responses
        if any(w in prompt_lower for w in ['routine', 'schedule', 'plan', 'timetable']):
            return ("I can generate a personalized routine for you! "
                    "Head to the Routine tab and choose:\n\n"
                    "📅 Daily — balanced everyday schedule\n"
                    "📚 Exam Mode — study-focused with wellness breaks\n"
                    "💰 Budget-Friendly — cost-optimized day plan\n"
                    "📋 Weekly — variety throughout the week\n\n"
                    "The more profile info you fill in, the better I can personalize it!")

        # Mood/feeling responses
        if any(w in prompt_lower for w in ['happy', 'good', 'great', 'awesome', 'excited']):
            return ("That's wonderful to hear! 🎉 Keep that positive energy going.\n\n"
                    "Quick tip: Log your mood in the daily check-in when you're feeling good too — "
                    "it helps identify what patterns lead to your best days!\n\n"
                    "Is there anything else I can help you with?")

        if any(w in prompt_lower for w in ['sad', 'lonely', 'depress', 'down', 'bad']):
            return ("I'm sorry you're going through this. Your feelings are valid.\n\n"
                    "Some things that might help:\n"
                    "• Reach out to a friend or family member — connection helps\n"
                    "• Go for a short walk, even just 5 minutes\n"
                    "• Do one small thing you enjoy today\n"
                    "• Remember: bad days don't mean a bad life\n\n"
                    "If these feelings persist, please consider talking to a counselor. "
                    "Most colleges offer free counseling services. 💙")

        # Food/eating responses
        if any(w in prompt_lower for w in ['food', 'eat', 'meal', 'hungry', 'lunch', 'dinner', 'breakfast']):
            return ("Nutrition matters for your energy and focus! Here are budget-friendly tips:\n\n"
                    "🍳 Don't skip breakfast — even a banana + peanut butter works\n"
                    "🥗 Try to get protein and veggies in each meal\n"
                    "💧 Stay hydrated — aim for 8 glasses of water daily\n"
                    "🍱 Meal prep on weekends to save money and time\n\n"
                    "Track your meals skipped in the daily check-in!")

        # Exam responses
        if any(w in prompt_lower for w in ['exam', 'test', 'study', 'assignment']):
            return ("Exam time! Here's how to stay on top:\n\n"
                    "📚 Use active recall — test yourself instead of re-reading\n"
                    "⏰ Study in 45-minute blocks with 10-minute breaks\n"
                    "🧠 Sleep well — your brain consolidates memory during sleep\n"
                    "🍎 Eat brain food — nuts, fruits, dark chocolate\n"
                    "📅 Try Exam Mode in the Routine tab for a study-optimized schedule\n\n"
                    "You've got this! 💪")

        # Default/greeting
        if any(w in prompt_lower for w in ['hello', 'hi', 'hey', 'help', 'what can you']):
            return ("Hey! I'm your PocketBuddy AI companion. Here's what I can help with:\n\n"
                    "💰 **Financial** — Track expenses, analyze spending, budget advice\n"
                    "🧘 **Wellness** — Monitor mood, sleep, stress patterns\n"
                    "📅 **Routines** — Generate personalized daily schedules\n"
                    "💜 **Support** — Chat about stress, motivation, or anything\n"
                    "📊 **Reports** — Weekly life summaries with action plans\n\n"
                    "Try asking me something like:\n"
                    "• 'I spent ₹300 on groceries'\n"
                    "• 'I only slept 4 hours last night'\n"
                    "• 'Generate an exam routine for me'\n"
                    "• 'I'm feeling overwhelmed'")

        # Generic helpful response
        return ("I'm here to help! You can:\n\n"
                "• Tell me about expenses and I'll track them\n"
                "• Share how you're feeling for wellness insights\n"
                "• Ask for routines, financial advice, or study tips\n"
                "• Do a daily check-in for personalized scoring\n\n"
                "The more you interact with me, the better I get at helping you!")

    async def call_openai_fallback(self, prompt: str, system_instruction: str = "") -> str:
        """Fallback to OpenAI if Gemini fails."""
        if not settings.OPENAI_API_KEY:
            return await self._fallback_response(prompt)

        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_instruction or self._get_system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=2000,
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error("OpenAI fallback error", error=str(e))
            return await self._fallback_response(prompt)

    async def _fallback_response(self, prompt: str) -> str:
        """Provide a helpful response when no AI API is configured."""
        return ("I'm your PocketBuddy assistant! To get personalized AI responses, "
                "please add your Gemini API key to the .env file. "
                "You can get a free key at https://aistudio.google.com/apikey. "
                "In the meantime, try logging expenses, doing wellness check-ins, "
                "or exploring the dashboard — those all work without an API key!")

    async def call_ai_json(self, prompt: str, system_instruction: str = "") -> Dict[str, Any]:
        """Call AI and parse JSON response."""
        if not settings.GEMINI_API_KEY and not settings.OPENAI_API_KEY:
            return {}

        full_prompt = f"{prompt}\n\nRespond ONLY with valid JSON. No markdown, no explanation."
        response = await self.call_gemini(full_prompt, system_instruction)

        # Clean up response
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]

        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            self.logger.error("Failed to parse AI JSON response", response=response[:200])
            return {}

    async def get_cached_or_compute(
        self, cache_key: str, compute_fn, ttl: int = 3600
    ) -> Any:
        """Get from cache or compute and cache."""
        cached = await cache_get(cache_key)
        if cached:
            return cached

        result = await compute_fn()
        await cache_set(cache_key, result, ttl)
        return result

    @abstractmethod
    def _get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        pass
