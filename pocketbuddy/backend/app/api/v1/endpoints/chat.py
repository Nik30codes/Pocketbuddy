"""Chat endpoint - ChatGPT-style conversation system."""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
import base64
import httpx
from fastapi import UploadFile, File, Form

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.schemas.ai_schemas import ChatMessage as ChatMessageSchema, ChatResponse
from app.models.chat import ChatMessage, Conversation

router = APIRouter()


def _generate_title(message: str) -> str:
    """Generate a short title from the first message."""
    msg = message.strip()
    # Remove common starters
    for prefix in ["can you", "please", "hey", "hi", "hello", "i want to", "help me"]:
        if msg.lower().startswith(prefix):
            msg = msg[len(prefix):].strip()

    # Capitalize and truncate
    title = msg[:40].strip()
    if len(message) > 40:
        title += "..."
    return title.capitalize() if title else "New Chat"


@router.post("/message", response_model=ChatResponse)
async def send_message(
    data: ChatMessageSchema,
    conversation_id: Optional[int] = None,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a message. Creates a new conversation if conversation_id is not provided."""
    from app.agents.orchestrator import AgentOrchestrator

    # Get or create conversation
    if conversation_id:
        result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user_id)
        )
        convo = result.scalar_one_or_none()
        if not convo:
            convo = Conversation(user_id=user_id, title=_generate_title(data.message))
            db.add(convo)
            await db.flush()
    else:
        convo = Conversation(user_id=user_id, title=_generate_title(data.message))
        db.add(convo)
        await db.flush()

    # Save user message
    user_msg = ChatMessage(conversation_id=convo.id, user_id=user_id, role="user", content=data.message)
    db.add(user_msg)

    # Process through AI
    orchestrator = AgentOrchestrator()
    response = await orchestrator.process_message(user_id=user_id, message=data.message, context=data.context, db=db)

    # Save assistant response
    assistant_msg = ChatMessage(
        conversation_id=convo.id, user_id=user_id, role="assistant", content=response.response,
        agent=response.agent, suggestions=response.suggestions, actions_taken=response.actions_taken,
    )
    db.add(assistant_msg)

    # Extract memories
    from app.services.memory_engine import extract_and_store_memories
    await extract_and_store_memories(user_id, data.message, response.response, db)

    return ChatResponse(
        response=response.response,
        agent=response.agent,
        actions_taken=response.actions_taken,
        suggestions=response.suggestions,
        conversation_id=convo.id,
    )


@router.post("/message-with-image")
async def send_message_with_image(
    message: str = Form(default="Analyze this bill and extract expenses"),
    conversation_id: int = Form(default=None),
    image: UploadFile = File(...),
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a message with image."""
    import json
    from datetime import date as date_module

    image_bytes = await image.read()
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    content_type = image.content_type or "image/jpeg"

    # Get or create conversation
    if conversation_id:
        result = await db.execute(select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user_id))
        convo = result.scalar_one_or_none()
    else:
        convo = None

    if not convo:
        convo = Conversation(user_id=user_id, title="Bill Analysis")
        db.add(convo)
        await db.flush()

    user_msg = ChatMessage(conversation_id=convo.id, user_id=user_id, role="user", content=f"[Image: {image.filename}] {message}")
    db.add(user_msg)

    from app.api.v1.endpoints.chat_helpers import analyze_image_with_ai, auto_save_expenses
    ai_response = await analyze_image_with_ai(image_base64, content_type, message)
    actions_taken = []
    saved = await auto_save_expenses(ai_response, user_id, db)
    if saved > 0:
        actions_taken.append(f"Saved {saved} expense(s)")

    assistant_msg = ChatMessage(
        conversation_id=convo.id, user_id=user_id, role="assistant", content=ai_response,
        agent="financial_wellness", actions_taken=actions_taken,
    )
    db.add(assistant_msg)

    return {
        "response": ai_response + (f"\n\n✅ Auto-saved {saved} expense(s)!" if saved > 0 else ""),
        "agent": "financial_wellness",
        "suggestions": ["Show my spending", "Upload another bill"],
        "actions_taken": actions_taken,
        "conversation_id": convo.id,
    }


# --- Conversation Management ---

@router.get("/conversations")
async def get_conversations(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all conversations for sidebar."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
        .limit(50)
    )
    convos = result.scalars().all()
    return [
        {"id": c.id, "title": c.title, "created_at": str(c.created_at), "updated_at": str(c.updated_at)}
        for c in convos
    ]


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: int,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all messages in a conversation."""
    # Verify ownership
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user_id)
    )
    if not result.scalar_one_or_none():
        return []

    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = result.scalars().all()
    return [
        {"id": m.id, "role": m.role, "content": m.content, "agent": m.agent, "suggestions": m.suggestions, "created_at": str(m.created_at)}
        for m in messages
    ]


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a conversation and all its messages."""
    await db.execute(delete(ChatMessage).where(ChatMessage.conversation_id == conversation_id))
    await db.execute(delete(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user_id))
    return {"status": "deleted"}


@router.put("/conversations/{conversation_id}/rename")
async def rename_conversation(
    conversation_id: int,
    title: str = Query(...),
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Rename a conversation."""
    await db.execute(
        update(Conversation)
        .where(Conversation.id == conversation_id, Conversation.user_id == user_id)
        .values(title=title)
    )
    return {"status": "renamed"}


# Keep legacy endpoint for compatibility
@router.get("/history")
async def get_chat_history(
    limit: int = 50,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Legacy: get recent messages across all conversations."""
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.user_id == user_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
    )
    messages = result.scalars().all()
    return [
        {"id": m.id, "role": m.role, "content": m.content, "agent": m.agent, "suggestions": m.suggestions, "created_at": str(m.created_at)}
        for m in reversed(messages)
    ]
