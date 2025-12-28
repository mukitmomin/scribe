from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.models import Post

router = APIRouter(prefix="/api/public/blog", tags=["public-blog"])


@router.get("/posts")
async def get_public_posts(db: AsyncSession = Depends(get_db)):
    """Get all published blog posts. Public endpoint for portfolio consumption."""
    result = await db.execute(
        select(Post)
        .where(Post.status == "published")
        .order_by(desc(Post.published_at))
    )
    posts = result.scalars().all()
    return {
        "posts": [
            {
                "id": str(p.id),
                "title": p.title,
                "slug": p.slug,
                "published_at": p.published_at.isoformat() if p.published_at else None,
                "summary": p.content_markdown[:200] + "..." if p.content_markdown else ""
            }
            for p in posts
        ]
    }


@router.get("/post/{slug}")
async def get_public_post_by_slug(slug: str, db: AsyncSession = Depends(get_db)):
    """Get a published post by its slug. Public endpoint."""
    result = await db.execute(select(Post).where(Post.slug == slug))
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    return {
        "id": str(post.id),
        "title": post.title,
        "content_markdown": post.content_markdown,
        "published_at": post.published_at.isoformat() if post.published_at else None,
        "slug": post.slug,
        "substack_embed_code": post.substack_embed_code,
        "paper_id": post.paper_id
    }
