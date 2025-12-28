from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime

from app.database import get_db
from app.models import Paper, ChatSession, Post
from app.agents.scribe import scribe_graph
from app.middleware.tenant import get_current_tenant

router = APIRouter(prefix="/api/v1/scribe", tags=["scribe"])


@router.post("/draft")
async def generate_draft(
    request: Request,
    body: dict = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """Generate a blog post draft from a paper and chat session."""
    tenant_id = get_current_tenant(request)
    paper_id = body.get("paper_id")
    session_id = body.get("session_id")

    if not paper_id:
        raise HTTPException(status_code=400, detail="paper_id is required")

    # Fetch paper summary
    query = select(Paper).where(Paper.id == paper_id)
    if tenant_id:
        query = query.where(Paper.tenant_id == tenant_id)

    paper_res = await db.execute(query)
    paper = paper_res.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Fetch chat history if session_id provided
    chat_history = []
    if session_id:
        query = select(ChatSession).where(ChatSession.id == session_id)
        if tenant_id:
            query = query.where(ChatSession.tenant_id == tenant_id)

        session_res = await db.execute(query)
        chat_session = session_res.scalar_one_or_none()
        if chat_session and chat_session.messages:
            chat_history = chat_session.messages

    # Run Scribe Agent
    inputs = {
        "paper_id": paper_id,
        "paper_summary": paper.summary or "",
        "chat_history": chat_history,
        "draft_content": ""
    }

    result = await scribe_graph.ainvoke(inputs)
    draft_content = result.get("draft_content", "")

    # Create new post
    new_post = Post(
        paper_id=paper_id,
        title=f"Deep Dive: {paper.title}",
        content_markdown=draft_content,
        status='draft',
        tenant_id=tenant_id
    )
    db.add(new_post)
    await db.flush()
    post_id = new_post.id

    await db.commit()

    return {"post_id": str(post_id), "content": draft_content}


@router.get("/posts/{paper_id}")
async def get_posts_for_paper(
    paper_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Get all posts for a specific paper."""
    tenant_id = get_current_tenant(request)

    query = select(Post).where(Post.paper_id == paper_id).order_by(desc(Post.created_at))
    if tenant_id:
        query = query.where(Post.tenant_id == tenant_id)

    result = await db.execute(query)
    posts = result.scalars().all()
    return {
        "posts": [
            {
                "id": str(p.id),
                "title": p.title,
                "status": p.status,
                "slug": p.slug,
                "created_at": p.created_at.isoformat() if p.created_at else None
            }
            for p in posts
        ]
    }


@router.get("/admin/posts")
async def get_all_admin_posts(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Get all posts for admin dashboard."""
    tenant_id = get_current_tenant(request)

    query = select(Post).order_by(desc(Post.created_at))
    if tenant_id:
        query = query.where(Post.tenant_id == tenant_id)

    result = await db.execute(query)
    posts = result.scalars().all()
    return {
        "posts": [
            {
                "id": str(p.id),
                "title": p.title,
                "status": p.status,
                "paper_id": p.paper_id,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "published_at": p.published_at.isoformat() if p.published_at else None,
                "slug": p.slug,
                "has_embed": bool(p.substack_embed_code)
            }
            for p in posts
        ]
    }


@router.get("/post/{post_id}")
async def get_post(
    post_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific post by ID."""
    tenant_id = get_current_tenant(request)

    query = select(Post).where(Post.id == post_id)
    if tenant_id:
        query = query.where(Post.tenant_id == tenant_id)

    result = await db.execute(query)
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    return {
        "id": str(post.id),
        "title": post.title,
        "content_markdown": post.content_markdown,
        "status": post.status,
        "paper_id": post.paper_id,
        "slug": post.slug,
        "substack_embed_code": post.substack_embed_code
    }


@router.put("/post/{post_id}")
async def update_post(
    post_id: str,
    request: Request,
    body: dict = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """Update a post."""
    tenant_id = get_current_tenant(request)

    query = select(Post).where(Post.id == post_id)
    if tenant_id:
        query = query.where(Post.tenant_id == tenant_id)

    result = await db.execute(query)
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if "content_markdown" in body:
        post.content_markdown = body["content_markdown"]
    if "title" in body:
        post.title = body["title"]
    if "slug" in body:
        post.slug = body["slug"]
    if "substack_embed_code" in body:
        post.substack_embed_code = body["substack_embed_code"]
    if "status" in body:
        post.status = body["status"]
        if post.status == "published" and not post.published_at:
            post.published_at = datetime.utcnow()

    await db.commit()
    return {"status": "success"}


@router.delete("/post/{post_id}")
async def delete_post(
    post_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Delete a post."""
    tenant_id = get_current_tenant(request)

    query = select(Post).where(Post.id == post_id)
    if tenant_id:
        query = query.where(Post.tenant_id == tenant_id)

    result = await db.execute(query)
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    await db.delete(post)
    await db.commit()
    return {"status": "success"}
