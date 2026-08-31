"""Chat / AI Mentor API."""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.models import Learner, ChatMessage, MessageRole
from app.schemas.schemas import ChatRequest, ChatResponse
from app.ai.mentor import get_mentor_response

router = APIRouter(prefix="/api/assistant", tags=["assistant"])
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponse)
async def chat_with_mentor(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Send a message to the AI mentor and get a context-aware response."""
    result = await db.execute(select(Learner).where(Learner.id == request.learner_id))
    learner = result.scalar_one_or_none()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")

    # Save user message
    user_msg = ChatMessage(
        learner_id=learner.id,
        role=MessageRole.USER,
        content=request.message,
    )
    db.add(user_msg)
    await db.flush()

    # Get AI response
    response_text = await get_mentor_response(learner, request.message, db)

    # Save assistant response
    assistant_msg = ChatMessage(
        learner_id=learner.id,
        role=MessageRole.ASSISTANT,
        content=response_text,
    )
    db.add(assistant_msg)
    await db.commit()
    await db.refresh(assistant_msg)

    return ChatResponse(
        id=assistant_msg.id,
        role=assistant_msg.role,
        content=assistant_msg.content,
        timestamp=assistant_msg.timestamp,
    )


@router.get("/chat/{learner_id}")
async def get_chat_history(learner_id: int, limit: int = 20, db: AsyncSession = Depends(get_db)):
    """Get chat history for a learner."""
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.learner_id == learner_id)
        .order_by(ChatMessage.timestamp.desc())
        .limit(limit)
    )
    messages = list(reversed(result.scalars().all()))
    return [
        {"id": m.id, "role": m.role, "content": m.content, "timestamp": m.timestamp}
        for m in messages
    ]


@router.delete("/chat/{learner_id}")
async def clear_chat_history(learner_id: int, db: AsyncSession = Depends(get_db)):
    """Clear chat history for a learner (keep last 2 messages)."""
    from sqlalchemy import delete as sql_delete
    await db.execute(
        sql_delete(ChatMessage).where(ChatMessage.learner_id == learner_id)
    )
    await db.commit()
    return {"message": "Chat history cleared"}
