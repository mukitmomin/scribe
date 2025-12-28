from typing import TypedDict, List, Any, Dict
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import json
from app.services.arxiv_service import ArxivService
from app.config import settings

arxiv_service = ArxivService()

# Initialize LLM based on config
if settings.use_mock_llm:
    from app.agents.mock_llm import MockChatModel
    llm = MockChatModel()
else:
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.5)


class ResearchState(TypedDict):
    user_context: str
    user_query: str
    generated_queries: List[str]
    found_papers: List[Dict[str, Any]]


async def generate_queries_node(state: ResearchState):
    """Generates search queries based on user context."""
    context = state["user_context"]
    user_query = state.get("user_query", "")

    prompt = f"""
    You are an expert Research Assistant.

    USER CONTEXT (Interests):
    {context}

    USER QUERY (Specific Focus):
    {user_query if user_query else "None provided (Discovery Mode)"}

    global_trends = "Generative AI, Large Language Models, Autonomous Agents, diffusion models, multimodal learning"

    TASK:
    Generate 3 specific, novel ArXiv search queries.
    - IF User Query is provided: Focus HEAVILY on it, but expand it with "Agentic" reasoning (e.g., look for recent breakthroughs, critiques, or sub-niches related to the query). Combine it with trends if relevant.
    - IF "Discovery Mode": Combine User Interests with broader AI trends to find emerging papers.

    OUTPUT FORMAT:
    Return ONLY a JSON array of strings. Example: ["cat:cs.AI AND 'autonomous agents'", "cat:cs.CL AND 'reasoning'"]
    Do not include markdown formatting.
    """

    messages = [
        SystemMessage(content="You generate specific ArXiv search queries in JSON format."),
        HumanMessage(content=prompt)
    ]

    response = await llm.ainvoke(messages)
    content = response.content.strip()

    # Clean up potential markdown code blocks
    if content.startswith("```json"):
        content = content.replace("```json", "").replace("```", "")

    try:
        queries = json.loads(content)
        if not isinstance(queries, list):
            queries = [content]
    except:
        queries = ["cat:cs.AI"]

    return {"generated_queries": queries}


async def search_arxiv_node(state: ResearchState):
    """Executes the generated queries."""
    queries = state["generated_queries"]
    all_results = []

    for q in queries:
        try:
            results = arxiv_service.search_papers(query=q, max_results=3, sort_by="date")
            all_results.extend(results)
        except Exception as e:
            print(f"Error searching {q}: {e}")

    # Deduplicate by ID
    seen_ids = set()
    unique_results = []
    for p in all_results:
        if p["id"] not in seen_ids:
            unique_results.append(p)
            seen_ids.add(p["id"])

    return {"found_papers": unique_results}


# Build Graph
workflow = StateGraph(ResearchState)
workflow.add_node("generate_queries", generate_queries_node)
workflow.add_node("search_arxiv", search_arxiv_node)

workflow.set_entry_point("generate_queries")
workflow.add_edge("generate_queries", "search_arxiv")
workflow.add_edge("search_arxiv", END)

researcher_graph = workflow.compile()
