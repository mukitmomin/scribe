from typing import TypedDict, List, Any
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage
from app.services.arxiv_service import ArxivService
from app.config import settings


class AgentState(TypedDict):
    messages: List[Any]
    paper_id: str
    paper_content: str


arxiv_service = ArxivService()

# Initialize LLM based on config
if settings.use_mock_llm:
    print("MOCK MODE: Using MockChatModel", flush=True)
    from app.agents.mock_llm import MockChatModel
    llm = MockChatModel()
else:
    print("REAL MODE: Using ChatGoogleGenerativeAI", flush=True)
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.5)


async def load_paper_node(state: AgentState):
    """Loads the paper content if not already loaded."""
    if not state.get("paper_content"):
        paper_id = state["paper_id"]
        from app.database import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            paper = await arxiv_service.get_paper_details(session, paper_id)

        if paper:
            content = f"Title: {paper['title']}\n\nAbstract: {paper['summary']}"
            return {"paper_content": content}
        else:
            return {"paper_content": "Paper not found."}
    return {}


async def teacher_node(state: AgentState):
    """The core teacher agent logic."""
    messages = state["messages"]
    paper_content = state.get("paper_content", "")

    system_prompt = SystemMessage(content=f"""
    You are 'The Teacher', an AI research assistant designed to help users understand complex academic papers.

    Your goal is to explain concepts deeply, using analogies (e.g., distributed systems, Python code) where appropriate.
    You have read the following paper:

    {paper_content}

    When the user asks a question, answer it based on the paper.
    If the user asks for math explanations, provide step-by-step derivations.
    If the user asks for code, provide Python pseudocode.

    Be concise but thorough. Do not hallucinate facts not in the paper.
    """)

    response = await llm.ainvoke([system_prompt] + messages)

    return {"messages": [response]}


# Build the graph
workflow = StateGraph(AgentState)

workflow.add_node("load_paper", load_paper_node)
workflow.add_node("teacher", teacher_node)

workflow.set_entry_point("load_paper")
workflow.add_edge("load_paper", "teacher")
workflow.add_edge("teacher", END)

teacher_graph = workflow.compile()
