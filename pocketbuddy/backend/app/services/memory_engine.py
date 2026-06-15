"""Memory Engine - extracts, stores, and retrieves long-term user memories."""

import re
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.memory import UserMemory, ConversationSummary
from app.models.chat import ChatMessage


async def extract_and_store_memories(user_id: str, message: str, ai_response: str, db: AsyncSession):
    """Analyze a conversation turn and extract memorable information."""
    msg_lower = message.lower()

    # Financial goals
    goal_patterns = [
        (r'(?:want to|goal is to|trying to|plan to|aim to)\s+save\s+(?:₹|rs\.?|rupees?)?\s*([\d,]+)', 'financial_goal', 'Save ₹{}'),
        (r'(?:budget|limit)\s+(?:is|of)\s+(?:₹|rs\.?)?\s*([\d,]+)', 'financial_goal', 'Monthly budget: ₹{}'),
        (r'(?:earn|income|allowance|salary)\s+(?:is|of)\s+(?:₹|rs\.?)?\s*([\d,]+)', 'financial_goal', 'Monthly income: ₹{}'),
    ]

    for pattern, mem_type, template in goal_patterns:
        match = re.search(pattern, msg_lower)
        if match:
            content = template.format(match.group(1))
            await _store_memory(user_id, mem_type, content, 8.0, db)

    # Wellness goals
    if any(w in msg_lower for w in ['want to sleep', 'sleep goal', 'aim for', 'target']):
        sleep_match = re.search(r'(\d+)\s*(?:hours?|hrs?)\s*(?:of\s*)?sleep', msg_lower)
        if sleep_match:
            await _store_memory(user_id, 'wellness_goal', f"Sleep goal: {sleep_match.group(1)} hours", 7.0, db)

    if any(w in msg_lower for w in ['lose weight', 'gain weight', 'exercise', 'workout', 'gym']):
        await _store_memory(user_id, 'wellness_goal', f"Fitness intent: {message[:80]}", 6.0, db)

    # Preferences
    if any(w in msg_lower for w in ['vegetarian', 'vegan', 'non-veg', 'jain', 'no spicy', 'allergic']):
        await _store_memory(user_id, 'preference', f"Food preference: {message[:80]}", 7.0, db)

    if any(w in msg_lower for w in ['prefer', 'i like', 'i dont like', "i don't like", 'i hate']):
        await _store_memory(user_id, 'preference', f"Preference: {message[:80]}", 5.0, db)

    # Academic/Career context
    if any(w in msg_lower for w in ['preparing for', 'studying for', 'exam', 'certification', 'course', 'semester']):
        await _store_memory(user_id, 'user_context', f"Academic: {message[:100]}", 8.0, db)

    # Stress patterns
    if any(w in msg_lower for w in ['stressed about', 'anxious about', 'worried about', 'overwhelmed by']):
        await _store_memory(user_id, 'stress_pattern', f"Stress trigger: {message[:80]}", 7.0, db)

    # Spending habits mentioned
    if any(w in msg_lower for w in ['i usually spend', 'i always buy', 'food delivery', 'ordering food', 'eating out']):
        await _store_memory(user_id, 'spending_habit', f"Habit: {message[:80]}", 6.0, db)

    # Routines and schedule
    if any(w in msg_lower for w in ['i wake up at', 'my classes start', 'i sleep at', 'my schedule']):
        await _store_memory(user_id, 'routine', f"Schedule: {message[:80]}", 6.0, db)

    # Achievements from AI response
    if any(w in ai_response.lower() for w in ['congratulations', 'well done', 'improved', 'achieved', 'streak']):
        await _store_memory(user_id, 'achievement', f"Achievement: {ai_response[:80]}", 5.0, db)


async def _store_memory(user_id: str, memory_type: str, content: str, importance: float, db: AsyncSession):
    """Store a memory, avoiding duplicates."""
    # Check for similar existing memory
    result = await db.execute(
        select(UserMemory).where(
            UserMemory.user_id == user_id,
            UserMemory.memory_type == memory_type,
            UserMemory.is_active == True,
        )
    )
    existing = result.scalars().all()

    # Simple dedup: if content is very similar to existing, update instead of create
    for mem in existing:
        if _similarity(mem.memory_content, content) > 0.7:
            mem.memory_content = content
            mem.importance_score = importance
            mem.updated_at = datetime.utcnow()
            return

    # Store new memory
    memory = UserMemory(
        user_id=user_id,
        memory_type=memory_type,
        memory_content=content,
        importance_score=importance,
    )
    db.add(memory)


def _similarity(a: str, b: str) -> float:
    """Simple word overlap similarity."""
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    if not words_a or not words_b:
        return 0
    overlap = len(words_a & words_b)
    return overlap / max(len(words_a), len(words_b))


async def get_relevant_memories(user_id: str, message: str, db: AsyncSession) -> list:
    """Retrieve memories relevant to the current message, sorted by importance."""
    result = await db.execute(
        select(UserMemory)
        .where(UserMemory.user_id == user_id, UserMemory.is_active == True)
        .order_by(UserMemory.importance_score.desc())
        .limit(15)
    )
    all_memories = result.scalars().all()

    # Score relevance to current message
    msg_words = set(message.lower().split())
    scored = []
    for mem in all_memories:
        mem_words = set(mem.memory_content.lower().split())
        relevance = len(msg_words & mem_words) / max(1, len(msg_words))
        score = mem.importance_score * 0.6 + relevance * 10 * 0.4
        scored.append((mem, score))

    # Return top memories (always include high-importance ones)
    scored.sort(key=lambda x: x[1], reverse=True)
    top = [m.memory_content for m, s in scored[:8]]

    # Always include goals (high importance)
    for mem in all_memories:
        if mem.memory_type in ('financial_goal', 'wellness_goal') and mem.memory_content not in top:
            top.append(mem.memory_content)

    return top[:10]


async def get_conversation_context(user_id: str, db: AsyncSession, limit: int = 8) -> list:
    """Get recent conversation messages for context."""
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.user_id == user_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
    )
    messages = list(reversed(result.scalars().all()))
    return [{"role": m.role, "content": m.content[:200]} for m in messages]


async def generate_session_summary(user_id: str, db: AsyncSession):
    """Generate a summary of recent conversation if it's getting long."""
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.user_id == user_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(20)
    )
    messages = result.scalars().all()

    if len(messages) < 15:
        return  # Not long enough to summarize

    # Check if we already summarized recently
    summary_result = await db.execute(
        select(ConversationSummary)
        .where(ConversationSummary.user_id == user_id)
        .order_by(ConversationSummary.created_at.desc())
        .limit(1)
    )
    last_summary = summary_result.scalar_one_or_none()
    if last_summary and (datetime.utcnow() - last_summary.created_at).seconds < 3600:
        return  # Summarized less than an hour ago

    # Create summary from messages
    user_msgs = [m.content[:100] for m in messages if m.role == 'user']
    topics = ", ".join(user_msgs[:5])
    summary_text = f"Recent topics discussed: {topics}"

    summary = ConversationSummary(
        user_id=user_id,
        summary=summary_text,
    )
    db.add(summary)
