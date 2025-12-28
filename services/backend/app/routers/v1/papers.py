from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Union, Optional
from app.services.arxiv_service import ArxivService
from app.middleware.tenant import get_current_tenant
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models import Paper as DBPaper
from datetime import datetime

router = APIRouter(prefix="/api/v1/papers", tags=["papers"])
arxiv_service = ArxivService()


class Paper(BaseModel):
    id: str
    title: str
    authors: List[str]
    summary: str
    published_date: Union[datetime, str]
    pdf_url: str
    status: str
    is_bookmarked: bool = False


@router.put("/{paper_id}/bookmark")
async def toggle_bookmark(
    paper_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Toggle bookmark status for a paper."""
    tenant_id = get_current_tenant(request)

    query = select(DBPaper).where(DBPaper.id == paper_id)
    if tenant_id:
        query = query.where(DBPaper.tenant_id == tenant_id)

    result = await db.execute(query)
    paper = result.scalars().first()

    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    paper.is_bookmarked = not paper.is_bookmarked
    await db.commit()
    return {"status": "success", "is_bookmarked": paper.is_bookmarked}


@router.get("/bookmarks", response_model=List[Paper])
async def get_bookmarks(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Fetch all bookmarked papers."""
    tenant_id = get_current_tenant(request)

    query = select(DBPaper).where(DBPaper.is_bookmarked == True).order_by(DBPaper.created_at.desc())
    if tenant_id:
        query = query.where(DBPaper.tenant_id == tenant_id)

    result = await db.execute(query)
    papers = result.scalars().all()
    return papers


@router.get("/trending", response_model=List[Paper])
async def get_trending_papers(
    request: Request,
    q: Union[str, None] = None,
    sort: Union[str, None] = "date",
    topic: Union[str, None] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Fetch papers from arXiv with optional search, topic, and sort parameters.
    """
    tenant_id = get_current_tenant(request)

    try:
        # Construct query
        search_query = "cat:cs.AI AND (llm OR 'language model' OR agent OR 'state space model' OR mamba)"

        if q:
            search_query = q
        elif topic:
            topic_queries = {
                "LLMs": "large language models OR GPT OR transformer",
                "Agents": "autonomous agents OR reasoning OR planning",
                "Vision": "computer vision OR diffusion models",
                "Robotics": "robotics OR reinforcement learning"
            }
            if topic in topic_queries:
                search_query = topic_queries[topic]

        # 1. Fetch from ArXiv
        papers_data = arxiv_service.search_papers(query=search_query, sort_by=sort)

        if not papers_data:
            return []

        # 2. Save/Update DB
        await arxiv_service.save_papers(db, papers_data, tenant_id)

        # 3. Fetch fresh from DB to get correct is_bookmarked status
        paper_ids = [p["id"] for p in papers_data]

        query = select(DBPaper).where(DBPaper.id.in_(paper_ids))
        if tenant_id:
            query = query.where(DBPaper.tenant_id == tenant_id)

        result = await db.execute(query)
        db_papers = result.scalars().all()

        db_paper_map = {p.id: p for p in db_papers}
        final_papers = []
        for p_data in papers_data:
            if p_data["id"] in db_paper_map:
                final_papers.append(db_paper_map[p_data["id"]])
            else:
                final_papers.append(p_data)

        return final_papers
    except Exception as e:
        print(f"Error in trending papers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/discover", response_model=List[Paper])
async def discover_papers(
    request: Request,
    q: Union[str, None] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Uses the Intelligent Research Agent to find papers.
    - If `q` is provided: Targeted Agentic Search.
    - If `q` is None: Discovery Mode (Bookmarks + Trends).
    """
    tenant_id = get_current_tenant(request)

    try:
        # 1. Gather Context (Bookmarks)
        query = select(DBPaper).where(DBPaper.is_bookmarked == True)
        if tenant_id:
            query = query.where(DBPaper.tenant_id == tenant_id)

        result = await db.execute(query)
        bookmarks = result.scalars().all()

        if not bookmarks:
            context = "General interest in AI, LLMs, and future tech."
        else:
            titles = [p.title for p in bookmarks]
            context = f"User has bookmarked these papers: {'; '.join(titles)}"

        # 2. Invoke Agent
        from app.agents.researcher import researcher_graph

        inputs = {
            "user_context": context,
            "user_query": q if q else ""
        }

        state = await researcher_graph.ainvoke(inputs)

        papers_data = state.get("found_papers", [])

        if not papers_data:
            return []

        # 3. Save to DB (so we can bookmark them)
        await arxiv_service.save_papers(db, papers_data, tenant_id)

        # 4. Return with bookmark status checked
        paper_ids = [p["id"] for p in papers_data]

        query = select(DBPaper).where(DBPaper.id.in_(paper_ids))
        if tenant_id:
            query = query.where(DBPaper.tenant_id == tenant_id)

        result = await db.execute(query)
        db_papers = result.scalars().all()

        return db_papers

    except Exception as e:
        print(f"Error in discovery: {e}")
        raise HTTPException(status_code=500, detail=str(e))
