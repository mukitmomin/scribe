import arxiv
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import Paper


class ArxivService:
    def search_papers(
        self,
        query: str = "cat:cs.AI OR cat:cs.LG OR cat:cs.CL",
        max_results: int = 10,
        sort_by: str = "date"
    ) -> List[Dict[str, Any]]:
        """
        Search for papers on arXiv.
        Supports advanced queries, ID lookup, and sorting.
        """
        import re
        client = arxiv.Client()

        # Check if query is an URL or ID
        # Matches: 2310.12345, 2310.12345v1, http://arxiv.org/abs/2310.12345, etc.
        id_pattern = r'(\d{4}\.\d{4,5}(v\d+)?)'
        match = re.search(id_pattern, query)

        search = None

        if match and (len(query.strip()) < 30 or "arxiv.org" in query):
            # Treat as ID lookup
            paper_id = match.group(1)
            search = arxiv.Search(id_list=[paper_id])
        else:
            # Standard search
            sort_criterion = arxiv.SortCriterion.SubmittedDate
            if sort_by == 'relevance':
                sort_criterion = arxiv.SortCriterion.Relevance
            elif sort_by == 'lastUpdated':
                sort_criterion = arxiv.SortCriterion.LastUpdatedDate

            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=sort_criterion
            )

        results = []
        try:
            for result in client.results(search):
                # Extract ID from entry_id (http://arxiv.org/abs/2310.12345v1 -> 2310.12345)
                paper_id = result.get_short_id().split('v')[0]

                results.append({
                    "id": paper_id,
                    "title": result.title,
                    "authors": [author.name for author in result.authors],
                    "summary": result.summary,
                    "published_date": result.published.replace(tzinfo=None),
                    "pdf_url": result.pdf_url,
                    "status": "new"
                })
        except Exception as e:
            print(f"Error searching arxiv: {e}")

        return results

    async def save_papers(
        self,
        db: AsyncSession,
        papers_data: List[Dict[str, Any]],
        tenant_id: Optional[str] = None
    ):
        """Save fetched papers to the database, ignoring duplicates."""
        for data in papers_data:
            # Check if exists
            result = await db.execute(select(Paper).where(Paper.id == data["id"]))
            existing_paper = result.scalars().first()

            if not existing_paper:
                paper = Paper(
                    id=data["id"],
                    title=data["title"],
                    authors=data["authors"],
                    summary=data["summary"],
                    published_date=data["published_date"],
                    pdf_url=data["pdf_url"],
                    status=data["status"],
                    tenant_id=tenant_id
                )
                db.add(paper)
        await db.commit()

    async def get_paper_details(
        self,
        db: AsyncSession,
        paper_id: str,
        tenant_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Fetch details for a single paper, checking DB first."""
        # 1. Check DB
        query = select(Paper).where(Paper.id == paper_id)
        if tenant_id:
            query = query.where(Paper.tenant_id == tenant_id)

        result = await db.execute(query)
        paper = result.scalars().first()

        if paper:
            return {
                "id": paper.id,
                "title": paper.title,
                "authors": paper.authors,
                "summary": paper.summary,
                "published_date": paper.published_date.isoformat() if paper.published_date else None,
                "pdf_url": paper.pdf_url
            }

        # 2. Fallback to ArXiv
        client = arxiv.Client()
        search = arxiv.Search(id_list=[paper_id])

        try:
            result = next(client.results(search))
            paper_data = {
                "id": paper_id,
                "title": result.title,
                "authors": [author.name for author in result.authors],
                "summary": result.summary,
                "published_date": result.published.replace(tzinfo=None),
                "pdf_url": result.pdf_url,
                "status": "new"
            }
            # Save to DB
            await self.save_papers(db, [paper_data], tenant_id)

            # Return dict with isoformat date for JSON response
            paper_data["published_date"] = paper_data["published_date"].isoformat()
            return paper_data
        except StopIteration:
            return None
