from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import json
import uuid as uuid_lib

from app.database import get_db
from app.models import ChatSession
from app.agents.teacher import teacher_graph
from app.middleware.tenant import get_current_tenant

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


class CreateSessionRequest(BaseModel):
    paper_id: str


@router.get("/sessions/{paper_id}")
async def get_sessions_for_paper(
    paper_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Get all chat sessions for a paper."""
    tenant_id = get_current_tenant(request)

    query = select(ChatSession).where(ChatSession.paper_id == paper_id).order_by(desc(ChatSession.updated_at))
    if tenant_id:
        query = query.where(ChatSession.tenant_id == tenant_id)

    result = await db.execute(query)
    sessions = result.scalars().all()
    return {
        "sessions": [
            {
                "id": str(session.id),
                "title": session.title or "New Chat",
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "updated_at": session.updated_at.isoformat() if session.updated_at else None,
                "message_count": len(session.messages) if session.messages else 0
            }
            for session in sessions
        ]
    }


@router.get("/session/{session_id}")
async def get_session(
    session_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific chat session by ID."""
    tenant_id = get_current_tenant(request)

    try:
        session_uuid = uuid_lib.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    query = select(ChatSession).where(ChatSession.id == session_uuid)
    if tenant_id:
        query = query.where(ChatSession.tenant_id == tenant_id)

    result = await db.execute(query)
    session = result.scalars().first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "id": str(session.id),
        "paper_id": session.paper_id,
        "title": session.title or "New Chat",
        "messages": session.messages or []
    }


@router.post("/session")
async def create_session(
    req: CreateSessionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Create a new chat session for a paper."""
    tenant_id = get_current_tenant(request)

    new_session = ChatSession(
        paper_id=req.paper_id,
        title=None,
        messages=[],
        tenant_id=tenant_id
    )
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)

    return {
        "id": str(new_session.id),
        "paper_id": new_session.paper_id,
        "title": "New Chat",
        "messages": []
    }


@router.delete("/session/{session_id}")
async def delete_session(
    session_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Delete a chat session by ID."""
    tenant_id = get_current_tenant(request)

    try:
        session_uuid = uuid_lib.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    query = select(ChatSession).where(ChatSession.id == session_uuid)
    if tenant_id:
        query = query.where(ChatSession.tenant_id == tenant_id)

    result = await db.execute(query)
    session = result.scalars().first()

    if session:
        await db.delete(session)
        await db.commit()

    return {"status": "deleted"}


@router.post("")
async def chat_endpoint(request: Request, db: AsyncSession = Depends(get_db)):
    """Streaming chat endpoint compatible with Vercel AI SDK."""
    tenant_id = get_current_tenant(request)
    body = await request.json()
    session_id = body.get("sessionId")
    paper_id = body.get("paperId")
    new_message = body.get("message")  # Only send the new message from client

    if not new_message or not new_message.get("content"):
        raise HTTPException(status_code=400, detail="Message content is required")

    # Fetch existing chat history from database if session exists
    existing_messages = []
    if session_id:
        try:
            session_uuid = uuid_lib.UUID(session_id)
            query = select(ChatSession).where(ChatSession.id == session_uuid)
            if tenant_id:
                query = query.where(ChatSession.tenant_id == tenant_id)

            result = await db.execute(query)
            session = result.scalars().first()

            if session and session.messages:
                existing_messages = session.messages
        except (ValueError, Exception) as e:
            print(f"Error loading session history: {e}")

    # Append new user message to history
    user_content = new_message.get("content", "")
    new_user_msg = {
        "role": "user",
        "content": user_content,
        "id": new_message.get("id", str(uuid_lib.uuid4()))
    }

    # Combine history + new message for LLM context
    sanitized_messages = existing_messages + [new_user_msg]
    first_user_message = user_content[:50] + ("..." if len(user_content) > 50 else "")

    async def event_generator():
        inputs = {"messages": sanitized_messages, "paper_id": paper_id}
        final_response_content = ""
        message_id = str(uuid_lib.uuid4())

        async for event in teacher_graph.astream_events(inputs, version="v2"):
            kind = event["event"]

            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    final_response_content += content
                    # Vercel AI SDK data stream format: 0:"text" for text deltas
                    yield f'0:{json.dumps(content)}\n'
            elif kind == "on_llm_new_token":
                token = event["data"]["token"]
                if token:
                    final_response_content += token
                    yield f'0:{json.dumps(token)}\n'

        # Send finish message in Vercel AI SDK format
        yield f'd:{json.dumps({"finishReason": "stop"})}\n'

        # Save to DB after streaming is complete
        ai_message = {"role": "assistant", "content": final_response_content, "id": message_id}
        # Append new user message + AI response to existing history
        updated_messages = existing_messages + [new_user_msg, ai_message]

        if session_id:
            try:
                session_uuid = uuid_lib.UUID(session_id)
                query = select(ChatSession).where(ChatSession.id == session_uuid)
                if tenant_id:
                    query = query.where(ChatSession.tenant_id == tenant_id)

                result = await db.execute(query)
                existing_session = result.scalars().first()

                if existing_session:
                    existing_session.messages = updated_messages
                    if not existing_session.title and first_user_message:
                        existing_session.title = first_user_message
            except ValueError:
                pass
        else:
            # No session_id provided, find or create session for this paper
            query = select(ChatSession).where(ChatSession.paper_id == paper_id)
            if tenant_id:
                query = query.where(ChatSession.tenant_id == tenant_id)

            result = await db.execute(query)
            existing_session = result.scalars().first()

            if existing_session:
                existing_session.messages = updated_messages
                if not existing_session.title and first_user_message:
                    existing_session.title = first_user_message
            else:
                new_session = ChatSession(
                    paper_id=paper_id,
                    messages=updated_messages,
                    title=first_user_message,
                    tenant_id=tenant_id
                )
                db.add(new_session)

        await db.commit()

    return StreamingResponse(event_generator(), media_type="text/plain; charset=utf-8", headers={
        "X-Accel-Buffering": "no",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "x-vercel-ai-data-stream": "v1"
    })
