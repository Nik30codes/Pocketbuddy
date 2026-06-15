"""Agent Orchestrator - Intelligent chat with full user context."""

from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date, timedelta
import httpx

from app.agents.base_agent import BaseAgent
from app.models.wellness import DailyCheckin, WellnessScore
from app.models.financial import Expense, Income, Budget
from app.models.user import User
from app.core.config import settings
from app.schemas.ai_schemas import ChatResponse


class AgentOrchestrator(BaseAgent):
    """Intelligent chat agent with full user context."""

    def __init__(self):
        super().__init__(
            name="AgentOrchestrator",
            description="Processes messages with full user context for personalized responses.",
        )

    def _get_system_prompt(self) -> str:
        return ""

    async def process(self, user_id: str, data: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        return await self.process_message(
            user_id=user_id,
            message=data.get("message", ""),
            context=data.get("context"),
            db=db,
        )

    async def process_message(
        self,
        user_id: str,
        message: str,
        context: Optional[str],
        db: AsyncSession,
    ) -> ChatResponse:
        """Process message with AI using full user context."""
        # Gather user data
        user_context = await self._get_full_user_context(user_id, db)

        # Check if user is logging an expense conversationally
        expense_result = await self._try_save_expense(message, user_id, user_context, db)
        if expense_result:
            return expense_result

        # Determine which agent badge to show
        agent_type = self._determine_agent(message)

        # Try Gemini/Groq AI with full live context
        self.logger.info("CALLING_AI", message=message[:50], has_routine_logs=bool(user_context.get("routine_logs")), has_wellness=bool(user_context.get("wellness")), has_financial=bool(user_context.get("financial", {}).get("total_spent_this_month")))
        ai_response = await self._call_ai_with_context(message, user_context, user_id, db)
        self.logger.info("AI_RESPONSE", got_response=bool(ai_response), length=len(ai_response) if ai_response else 0)

        if ai_response:
            # If AI generated a routine, save it to the routines table
            if any(w in message.lower() for w in ["routine", "schedule", "plan", "generate", "timetable"]):
                await self._save_routine_from_ai(ai_response, user_id, message, db)

            return ChatResponse(
                response=ai_response,
                agent=agent_type,
                suggestions=self._get_suggestions(message),
            )

        # Fallback to smart local response
        local_response = self._generate_contextual_response(message, user_context)
        return ChatResponse(
            response=local_response,
            agent=agent_type,
            suggestions=self._get_suggestions(message),
        )

    async def _try_save_expense(self, message: str, user_id: str, ctx: Dict, db: AsyncSession) -> Optional[ChatResponse]:
        """Detect and save expenses from conversational messages."""
        import re
        from app.models.financial import Expense

        msg = message.lower()

        # DON'T save if it's a question or suggestion request
        question_words = ["suggest", "recommend", "what", "how", "why", "which", "can you", "should i", "tell me", "give me", "help me", "options", "tips", "ideas", "ways"]
        if any(w in msg for w in question_words):
            return None

        # DON'T save if it's future tense or planning
        if any(w in msg for w in ["want to", "planning", "going to", "will", "below", "within", "limit"]):
            return None

        # Only detect expense if user is clearly reporting a past spend
        action_words = ["spent", "paid", "bought", "cost me", "charged", "debited", "gave", "add", "added", "update", "log"]
        has_action = any(w in msg for w in action_words)
        
        # Also allow "X is spend" or "update financial" patterns
        is_update = "update" in msg and "financial" in msg
        is_spend_report = re.search(r'\d+.*(?:is\s*)?spend\b', msg)

        if not has_action and not is_update and not is_spend_report:
            return None

        # Extract amount
        amount = None
        amount_match = re.search(r'(?:₹|rs\.?|rupees?)\s*([\d,]+(?:\.\d+)?)', msg)
        if not amount_match:
            amount_match = re.search(r'([\d,]+(?:\.\d+)?)\s*(?:rupees?|rs)', msg)
        if not amount_match and has_action:
            amount_match = re.search(r'(?:spent|paid|cost|bought|charged|add|added|log|logged)\s*(?:₹|rs\.?)?\s*([\d,]+(?:\.\d+)?)', msg)
        if not amount_match and has_action:
            # Fallback: just find any number in the message
            amount_match = re.search(r'([\d]+(?:\.\d+)?)', msg)

        if not amount_match:
            return None

        try:
            amount = float(amount_match.group(1).replace(',', ''))
        except ValueError:
            return None

        if amount <= 0:
            return None

        # Detect category
        category = "other"
        if any(w in msg for w in ["food", "lunch", "dinner", "breakfast", "eat", "meal", "restaurant", "cafe", "canteen", "biryani", "pizza", "snack"]):
            category = "food"
        elif any(w in msg for w in ["grocery", "groceries", "vegetable", "fruit", "milk", "eggs"]):
            category = "groceries"
        elif any(w in msg for w in ["travel", "uber", "ola", "auto", "bus", "metro", "petrol", "fuel", "cab", "rick"]):
            category = "travel"
        elif any(w in msg for w in ["shop", "cloth", "shoes", "amazon", "flipkart", "online"]):
            category = "shopping"
        elif any(w in msg for w in ["movie", "game", "netflix", "subscription", "fun", "entertainment"]):
            category = "entertainment"
        elif any(w in msg for w in ["book", "course", "tuition", "fee", "college", "education", "stationary"]):
            category = "education"
        elif any(w in msg for w in ["medicine", "doctor", "hospital", "pharmacy", "health"]):
            category = "health"

        # Save to database
        expense = Expense(
            user_id=user_id,
            amount=amount,
            category=category,
            description=message[:100],
            date=date.today(),
            source="conversational",
            is_essential="essential" if category in ["food", "groceries", "health", "education"] else "discretionary",
        )
        db.add(expense)

        fin = ctx.get("financial", {})
        new_total = fin.get("total_spent_this_month", 0) + amount
        remaining = None
        profile = ctx.get("profile", {})
        if profile.get("monthly_budget"):
            remaining = profile["monthly_budget"] - new_total

        response = f"✅ Logged ₹{amount:,.1f} under **{category}**!\n\n"
        response += f"📊 Updated totals:\n"
        response += f"• Spent this month: ₹{new_total:,.0f}\n"
        if remaining is not None:
            response += f"• Budget remaining: ₹{remaining:,.0f}\n"
        response += f"\nCheck the Financial page to see your updated charts."

        return ChatResponse(
            response=response,
            agent="financial_wellness",
            actions_taken=[f"Saved ₹{amount:.1f} ({category}) to expenses"],
            suggestions=["Show spending breakdown", "How's my budget?", "Add more expenses"],
        )

    async def _call_ai_with_context(self, message: str, ctx: Dict, user_id: str = None, db: AsyncSession = None) -> Optional[str]:
        """Call AI with user context, memories, and chat history."""
        # Build context string
        context_parts = []
        profile = ctx.get("profile", {})
        financial = ctx.get("financial", {})
        wellness = ctx.get("wellness")
        scores = ctx.get("scores")

        if profile.get("name"):
            context_parts.append(f"Student: {profile['name']}, Age: {profile.get('age', 'unknown')}")
        if profile.get("college"):
            context_parts.append(f"College: {profile['college']}, Schedule: {profile.get('college_start','09:00')}-{profile.get('college_end','17:00')}")
        if profile.get("living"):
            context_parts.append(f"Living: {profile['living']}, Kitchen: {'Yes' if profile.get('has_kitchen') else 'No'}")
        if profile.get("monthly_budget"):
            context_parts.append(f"Monthly budget: ₹{profile['monthly_budget']}")

        if financial.get("total_spent_this_month") is not None:
            context_parts.append(f"This month - Spent: ₹{financial['total_spent_this_month']:.0f}, Income: ₹{financial['total_income_this_month']:.0f}")
            if financial.get("remaining_budget") is not None:
                context_parts.append(f"Budget remaining: ₹{financial['remaining_budget']:.0f}")
            if financial.get("top_categories"):
                cats = ", ".join([f"{c[0]}:₹{c[1]:.0f}" for c in financial['top_categories'][:3]])
                context_parts.append(f"Top spending: {cats}")
            context_parts.append(f"Daily avg spend: ₹{financial.get('daily_avg_spend', 0):.0f}")

        if wellness:
            context_parts.append(f"Wellness (7-day avg) - Mood: {wellness['avg_mood']}/10, Stress: {wellness['avg_stress']}/10, Sleep: {wellness['avg_sleep']}h")
            context_parts.append(f"Meals skipped/day: {wellness['avg_meals_skipped']}, Exercise: {wellness['avg_exercise']}min/day")

        if scores:
            context_parts.append(f"Scores - Wellness: {scores['overall_wellness']:.0f}/100, Burnout risk: {scores['burnout_risk']}")

        # Routine logs - what user actually does
        routine_logs = ctx.get("routine_logs")
        if routine_logs:
            context_parts.append(f"\nUSER'S ACTUAL DAILY ACTIVITIES (from their LATEST review - USE THESE EXACTLY):")
            if routine_logs.get("commonly_completed"):
                for i, act in enumerate(routine_logs['commonly_completed'], 1):
                    context_parts.append(f"  {i}. {act}")
            context_parts.append(f"\n⚠️ STRICT RULE: Use ONLY the activities listed above for routine generation. Do NOT use activities from chat history or memories — ONLY the numbered list above. Assign proper times to each.")

        system_context = "\n".join(context_parts) if context_parts else "No user data available yet."

        # DEBUG: Log the full context being sent to AI
        self.logger.info("AI_CONTEXT_DEBUG", context=system_context[:500], user=user_id[:8] if user_id else "none")

        # Get long-term memories
        memories_text = ""
        if user_id and db:
            from app.services.memory_engine import get_relevant_memories
            memories = await get_relevant_memories(user_id, message, db)
            if memories:
                memories_text = "\n\nLONG-TERM MEMORY (things you know about this user):\n" + "\n".join(f"• {m}" for m in memories)

        # Get recent chat history
        chat_history_messages = []
        if user_id and db:
            from app.services.memory_engine import get_conversation_context
            chat_history_messages = await get_conversation_context(user_id, db)

        system_prompt = f"""You are PocketBuddy, a persistent AI student life coach. You REMEMBER previous conversations and user goals across sessions.

STUDENT DATA:
{system_context}
{memories_text}

RULES:
- Be conversational, warm, and concise (max 200 words)
- REMEMBER the conversation context — refer to what was discussed previously
- Use the student's actual data in your response when relevant
- Give specific, actionable advice based on their numbers
- Use ₹ for currency
- Answer the question directly — don't redirect to other pages
- If they ask for recipes, routines, tips — give them directly
- For emotional messages, be empathetic first
- Never diagnose medical conditions
- Use emojis sparingly

IMPORTANT - ROUTINE FORMAT:
- When generating ANY routine (daily, weekly, budget, exam), ALWAYS use this exact format for each line:
  HH:MM AM/PM - Activity description
- Example: "6:00 AM - Wake up, morning meditation"
- ALWAYS include at least 8 time-activity pairs
- For weekly routines, still give a single day plan but note which days it applies to
- For budget routines, include cost-saving tips in the activity descriptions

IMPORTANT - EXPENSE LOGGING:
- You CANNOT directly modify the database. 
- If the user wants to add an expense, tell them to say it like: "spent ₹100 on food" or "paid ₹200 for groceries"
- That exact format will trigger the auto-save. Don't pretend you've saved something if they didn't use that format.
- If asked "add ₹33 to food", respond: "Got it! I've logged ₹33 under food." (the system will handle the actual save)
- Never say "I'll update" for vague messages — only confirm if there's a clear amount + category."""

        # Try Gemini first
        if settings.GEMINI_API_KEY:
            # Build conversation for Gemini (single prompt with history)
            history_text = ""
            if chat_history_messages:
                history_text = "\n\nRECENT CONVERSATION:\n"
                for msg in chat_history_messages[-6:]:  # Last 6 messages
                    role = "Student" if msg["role"] == "user" else "PocketBuddy"
                    history_text += f"{role}: {msg['content']}\n"

            prompt = f"{system_prompt}{history_text}\n\nStudent: {message}\n\nPocketBuddy:"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.8, "maxOutputTokens": 600}
            }
            try:
                async with httpx.AsyncClient(timeout=25.0) as client:
                    response = await client.post(url, json=payload)
                    if response.status_code == 200:
                        data = response.json()
                        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    else:
                        self.logger.error("Gemini failed", status=response.status_code)
            except Exception as e:
                self.logger.error("Gemini error", error=str(e))

        # Fallback to Groq with proper chat history
        if settings.GROQ_API_KEY:
            try:
                messages = [{"role": "system", "content": system_prompt}]
                # Add chat history
                for msg in chat_history_messages[-6:]:
                    messages.append({"role": msg["role"] if msg["role"] in ["user", "assistant"] else "user", "content": msg["content"]})
                # Add current message
                messages.append({"role": "user", "content": message})

                async with httpx.AsyncClient(timeout=20.0) as client:
                    response = await client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": "llama-3.3-70b-versatile",
                            "messages": messages,
                            "temperature": 0.8,
                            "max_tokens": 600,
                        },
                    )
                    if response.status_code == 200:
                        data = response.json()
                        return data["choices"][0]["message"]["content"].strip()
                    else:
                        self.logger.error("Groq failed", status=response.status_code, body=response.text[:200])
            except Exception as e:
                self.logger.error("Groq error", error=str(e))

        return None

    def _generate_contextual_response(self, message: str, ctx: Dict) -> str:
        """Fallback: generate response using user data without API."""
        message_lower = message.lower()
        profile = ctx.get("profile", {})
        financial = ctx.get("financial", {})
        wellness = ctx.get("wellness")
        name = (profile.get("name") or "").split()[0] or "there"

        # Budget/financial questions
        if any(w in message_lower for w in ["budget", "spent", "money", "expense", "income", "save", "afford", "left", "remaining"]):
            spent = financial.get("total_spent_this_month", 0)
            income = financial.get("total_income_this_month", 0)
            remaining = financial.get("remaining_budget")
            daily_avg = financial.get("daily_avg_spend", 0)
            top_cats = financial.get("top_categories", [])

            parts = [f"Hey {name}! Here's your financial picture:\n"]
            parts.append(f"💰 Income this month: ₹{income:,.0f}")
            parts.append(f"💸 Spent so far: ₹{spent:,.0f}")
            if remaining is not None:
                parts.append(f"💵 Remaining: ₹{remaining:,.0f}")
                days_left = max(1, 30 - date.today().day)
                parts.append(f"📊 Safe daily spend: ₹{remaining/days_left:,.0f}")
            if top_cats:
                parts.append(f"\nTop categories: {', '.join([f'{c[0]} ₹{c[1]:.0f}' for c in top_cats[:3]])}")
            if remaining and remaining < 0:
                parts.append(f"\n⚠️ You're over budget! Cut back on {top_cats[0][0] if top_cats else 'non-essentials'}.")
            elif daily_avg > 0:
                parts.append(f"\n✅ You're averaging ₹{daily_avg:,.0f}/day.")
            return "\n".join(parts)

        # Wellness
        if any(w in message_lower for w in ["wellness", "score", "health", "how am i doing"]):
            if wellness:
                parts = [f"Your wellness snapshot (last {wellness['days_tracked']} days):\n"]
                parts.append(f"😊 Mood: {wellness['avg_mood']}/10")
                parts.append(f"😰 Stress: {wellness['avg_stress']}/10")
                parts.append(f"😴 Sleep: {wellness['avg_sleep']}h/night")
                parts.append(f"🏃 Exercise: {wellness['avg_exercise']}min/day")
                if wellness['avg_stress'] > 7:
                    parts.append(f"\n⚠️ Your stress is high. Try: box breathing, a short walk, or talking to someone.")
                if wellness['avg_sleep'] < 6:
                    parts.append(f"\n💤 You need more sleep! Aim for {profile.get('sleep_goal', 7)}h tonight.")
                return "\n".join(parts)
            return "I don't have wellness data yet! Do a quick check-in on the Wellness page — it takes 30 seconds. 🧘"

        # Routine generation
        if any(w in message_lower for w in ["routine", "schedule", "generate"]):
            is_exam = "exam" in message_lower
            parts = []
            if is_exam:
                parts.append(f"📚 Here's an exam routine for you, {name}:\n")
                parts.append("06:30 — Wake up + hydrate")
                parts.append("07:00 — Breakfast")
                parts.append("07:30 — Study Block 1 (hardest subject)")
                parts.append("09:30 — 15min break + stretch")
                parts.append("09:45 — Study Block 2")
                parts.append("12:00 — Lunch + rest")
                parts.append("13:00 — Study Block 3 (revision)")
                parts.append("15:00 — Snack + short walk")
                parts.append("15:30 — Study Block 4 (practice problems)")
                parts.append("17:30 — Exercise (20min)")
                parts.append("18:00 — Dinner")
                parts.append("19:00 — Light review / flashcards")
                parts.append("20:30 — Relax (no screens)")
                parts.append("21:30 — Sleep")
                parts.append(f"\n💡 Tips: Stay hydrated, eat brain food (nuts, fruits), and don't skip sleep!")
            else:
                start = profile.get("college_start", "09:00")
                end = profile.get("college_end", "17:00")
                parts.append(f"📅 Here's a daily routine for you:\n")
                parts.append("07:00 — Wake up + morning routine")
                parts.append("07:30 — Breakfast")
                parts.append(f"08:30 — Travel to college" if profile.get("living") != "hosteller" else "08:30 — Get ready")
                parts.append(f"{start} — Classes begin")
                parts.append("13:00 — Lunch")
                parts.append(f"{end} — Classes end")
                parts.append(f"{'17:30' if end <= '17:00' else '18:00'} — Exercise / walk (30min)")
                parts.append("18:30 — Dinner")
                parts.append("19:30 — Study / assignments")
                parts.append("21:00 — Free time / socialize")
                parts.append("22:00 — Wind down (no screens)")
                parts.append(f"22:30 — Sleep (goal: {profile.get('sleep_goal', 7)}h)")
                if profile.get("monthly_budget"):
                    parts.append(f"\n💰 Daily food budget: ~₹{(profile['monthly_budget']*0.4)/30:,.0f}")
            return "\n".join(parts)

        # Emotional
        if any(w in message_lower for w in ["stress", "anxious", "overwhelm", "sad", "lonely", "tired", "exhaust"]):
            parts = [f"I hear you, {name}. 💙\n"]
            if wellness and wellness['avg_stress'] > 6:
                parts.append(f"Your stress has been {wellness['avg_stress']}/10 this week — that's a lot to carry.\n")
            parts.append("Here's what can help right now:")
            parts.append("🫁 Box breathing: 4s inhale → 4s hold → 4s exhale → 4s hold")
            parts.append("🚶 5-minute walk outside")
            parts.append("📝 Write down what's bothering you — getting it out helps")
            parts.append("🎵 Put on your favorite song")
            parts.append(f"\nYou're doing better than you think. One step at a time. ❤️")
            return "\n".join(parts)

        # Greeting / general
        parts = [f"Hey {name}! 👋\n"]
        if financial.get("total_spent_this_month"):
            parts.append(f"💰 Budget status: ₹{financial.get('remaining_budget', 0):,.0f} remaining this month")
        if wellness:
            parts.append(f"🧘 Wellness: Mood {wellness['avg_mood']}/10, Sleep {wellness['avg_sleep']}h")
        parts.append(f"\nWhat can I help with? Ask me anything about your finances, wellness, routines, or just chat!")
        return "\n".join(parts)

    def _determine_agent(self, message: str) -> str:
        """Determine which agent badge to display."""
        msg = message.lower()
        if any(w in msg for w in ["spent", "budget", "money", "expense", "income", "save", "₹"]):
            return "financial_wellness"
        if any(w in msg for w in ["routine", "schedule", "plan", "timetable"]):
            return "routine_planning"
        if any(w in msg for w in ["stress", "anxious", "sad", "overwhelm", "feeling", "lonely"]):
            return "emotional_support"
        if any(w in msg for w in ["sleep", "exercise", "meal", "wellness", "health"]):
            return "wellness"
        if any(w in msg for w in ["burnout", "exhausted", "breaking"]):
            return "burnout_detection"
        return "life_coach"

    def _get_suggestions(self, message: str) -> list:
        """Get contextual follow-up suggestions."""
        msg = message.lower()
        if any(w in msg for w in ["budget", "money", "spent"]):
            return ["How can I save more?", "Show spending breakdown", "Set a budget"]
        if any(w in msg for w in ["routine", "schedule"]):
            return ["Generate exam routine", "Budget-friendly tips", "Sleep schedule"]
        if any(w in msg for w in ["stress", "anxious", "sad"]):
            return ["Breathing exercise", "Generate self-care routine", "Track my mood"]
        if any(w in msg for w in ["sleep", "tired"]):
            return ["Sleep hygiene tips", "Set sleep goal", "Why am I tired?"]
        return ["How's my budget?", "Wellness check", "Generate a routine"]

    async def _save_routine_from_ai(self, ai_response: str, user_id: str, message: str, db: AsyncSession):
        """Parse AI-generated routine text and save to routines table."""
        import re
        from app.models.ai_insights import Routine

        # Parse time-activity pairs from the response
        lines = ai_response.split('\n')
        schedule = []

        for line in lines:
            line = line.strip().lstrip('•*- ')
            # Simple pattern: digits:digits optionally AM/PM then separator then activity
            match = re.match(r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)\s*[\-–—:]+\s*(.+)', line)
            if match:
                time_str = match.group(1).strip()
                activity = match.group(2).strip()

                # Convert to 24hr format
                time_24 = self._to_24hr(time_str)

                # Determine category
                act_lower = activity.lower()
                category = "wellness"
                if any(w in act_lower for w in ["study", "class", "assignment", "work", "focus"]):
                    category = "academic"
                elif any(w in act_lower for w in ["breakfast", "lunch", "dinner", "eat", "cook", "meal", "food"]):
                    category = "nutrition"
                elif any(w in act_lower for w in ["exercise", "walk", "gym", "stretch", "workout", "jog"]):
                    category = "fitness"
                elif any(w in act_lower for w in ["travel", "commute", "bus", "metro"]):
                    category = "commute"
                elif any(w in act_lower for w in ["social", "friends", "relax", "free time", "fun"]):
                    category = "social"

                schedule.append({"time": time_24, "activity": activity, "category": category})

        if len(schedule) >= 4:  # Only save if we got a meaningful routine
            # Determine routine type from message AND AI response
            msg_lower = message.lower()
            response_lower = ai_response.lower()
            combined = msg_lower + " " + response_lower

            # Check specific types FIRST (order matters - most specific first)
            routine_type = "daily"  # default
            if any(w in msg_lower for w in ["exam", "test prep", "revision"]) or any(w in response_lower for w in ["exam survival", "exam routine", "study plan"]):
                routine_type = "exam"
            elif any(w in msg_lower for w in ["budget", "buget", "cheap", "affordable", "frugal", "save money", "cost"]) or any(w in response_lower for w in ["budget-friendly", "cost-saving", "budget friendly"]):
                routine_type = "budget_friendly"
            elif any(w in msg_lower for w in ["weekly", "week plan", "whole week"]) or any(w in response_lower for w in ["weekly plan", "week routine", "monday to"]):
                routine_type = "weekly"
            # else stays "daily"

            self.logger.info("Saving routine", type=routine_type, items=len(schedule), user=user_id[:8])

            # Deactivate old routines of same type
            from sqlalchemy import update as sql_update
            await db.execute(
                sql_update(Routine)
                .where(Routine.user_id == user_id, Routine.routine_type == routine_type)
                .values(is_active="no")
            )

            # Save new routine
            routine = Routine(
                user_id=user_id,
                routine_type=routine_type,
                name=f"AI-Generated {routine_type.replace('_', ' ').title()} Routine",
                schedule=schedule,
                is_active="yes",
            )
            db.add(routine)

    def _to_24hr(self, time_str: str) -> str:
        """Convert time string to 24hr format."""
        import re
        time_str = time_str.strip()

        # Already 24hr (e.g., "07:00", "14:30")
        match = re.match(r'^(\d{1,2}):(\d{2})$', time_str)
        if match:
            h = int(match.group(1))
            m = match.group(2)
            return f"{h:02d}:{m}"

        # 12hr format (e.g., "6:00 AM", "1:00 PM")
        match = re.match(r'^(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)', time_str)
        if match:
            h = int(match.group(1))
            m = match.group(2)
            period = match.group(3).upper()
            if period == "PM" and h != 12:
                h += 12
            elif period == "AM" and h == 12:
                h = 0
            return f"{h:02d}:{m}"

        return time_str

    async def _get_full_user_context(self, user_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Get comprehensive user context."""
        context = {}

        # Profile
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            context["profile"] = {
                "name": user.full_name,
                "age": user.age,
                "college": user.college_name,
                "living": user.living_situation.value if user.living_situation else None,
                "monthly_budget": user.monthly_budget,
                "food_prefs": user.food_preferences,
                "fitness_goals": user.fitness_goals,
                "sleep_goal": user.sleep_goal_hours,
                "has_kitchen": user.has_kitchen_access,
                "college_start": user.college_start_time,
                "college_end": user.college_end_time,
            }

        # Financial
        today = date.today()
        month_start = today.replace(day=1)

        expenses_result = await db.execute(
            select(Expense).where(Expense.user_id == user_id, Expense.date >= month_start)
        )
        expenses = expenses_result.scalars().all()

        income_result = await db.execute(
            select(Income).where(Income.user_id == user_id, Income.date >= month_start)
        )
        incomes = income_result.scalars().all()

        total_spent = sum(e.amount for e in expenses)
        total_income = sum(i.amount for i in incomes)

        category_spending = {}
        for e in expenses:
            cat = e.category.value if hasattr(e.category, 'value') else str(e.category)
            category_spending[cat] = category_spending.get(cat, 0) + e.amount

        context["financial"] = {
            "total_spent_this_month": total_spent,
            "total_income_this_month": total_income,
            "remaining_budget": (user.monthly_budget - total_spent) if user and user.monthly_budget else None,
            "savings": total_income - total_spent,
            "top_categories": sorted(category_spending.items(), key=lambda x: x[1], reverse=True)[:5],
            "num_transactions": len(expenses),
            "daily_avg_spend": total_spent / max(1, (today - month_start).days + 1),
        }

        # Wellness
        week_ago = today - timedelta(days=7)
        checkins_result = await db.execute(
            select(DailyCheckin)
            .where(DailyCheckin.user_id == user_id, DailyCheckin.date >= week_ago)
            .order_by(DailyCheckin.date.desc())
        )
        checkins = checkins_result.scalars().all()

        if checkins:
            context["wellness"] = {
                "avg_mood": round(sum(c.mood_score for c in checkins) / len(checkins), 1),
                "avg_stress": round(sum(c.stress_score for c in checkins) / len(checkins), 1),
                "avg_sleep": round(sum(c.sleep_hours for c in checkins) / len(checkins), 1),
                "avg_meals_skipped": round(sum(c.meals_skipped for c in checkins) / len(checkins), 1),
                "avg_exercise": round(sum(c.exercise_minutes for c in checkins) / len(checkins), 0),
                "days_tracked": len(checkins),
            }
        else:
            context["wellness"] = None

        # Scores
        score_result = await db.execute(
            select(WellnessScore)
            .where(WellnessScore.user_id == user_id)
            .order_by(WellnessScore.date.desc())
            .limit(1)
        )
        score = score_result.scalar_one_or_none()
        if score:
            context["scores"] = {
                "overall_wellness": score.overall_wellness,
                "burnout_risk": score.burnout_risk,
            }

        # Routine completion logs (what user actually does vs planned)
        from app.models.routine_log import RoutineLog
        logs_result = await db.execute(
            select(RoutineLog)
            .where(RoutineLog.user_id == user_id)
            .order_by(RoutineLog.id.desc())
            .limit(1)
        )
        logs = logs_result.scalars().all()
        self.logger.info("ROUTINE_LOGS_DEBUG", count=len(logs), user=user_id[:8])
        if logs:
            self.logger.info("ROUTINE_LOG_DATA", completed=logs[0].completed_activities[:3] if logs[0].completed_activities else [], skipped=logs[0].skipped_activities[:3] if logs[0].skipped_activities else [])
            context["routine_logs"] = {
                "recent_completion_rates": [l.completion_rate for l in logs],
                "commonly_completed": logs[0].completed_activities if logs[0].completed_activities else [],
                "commonly_skipped": logs[0].skipped_activities if logs[0].skipped_activities else [],
            }

        return context
