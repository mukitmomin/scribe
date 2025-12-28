from typing import TypedDict, List, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings


class ScribeState(TypedDict):
    paper_id: str
    paper_summary: str
    chat_history: List[Any]
    draft_content: str


# Initialize LLM based on config
if settings.use_mock_llm:
    from app.agents.mock_llm import MockChatModel
    llm = MockChatModel()
else:
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)


async def drafting_node(state: ScribeState):
    """Generates a blog post draft based on the paper and chat history."""
    paper_summary = state["paper_summary"]
    chat_history = state.get("chat_history", [])

    context_str = ""
    for msg in chat_history:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        context_str += f"{role.upper()}: {content}\n\n"

    prompt = f"""
    You are 'The Scribe', an expert technical writer.
    Your goal is to write a high-quality technical blog post about a research paper.

    PAPER SUMMARY:
    {paper_summary}

    CHAT HISTORY (What the user discussed/learned):
    {context_str}

    INSTRUCTIONS:
    1. Write a blog post titled "Deep Dive: [Paper Title]".
    2. Focus HEAVILY on the concepts discussed in the CHAT HISTORY. If the user asked about specific math or code, explain that in detail.
    3. If the chat history is empty, write a general overview based on the summary.
    4. Use Markdown formatting (headers, code blocks, bold text).
    5. The tone should be educational, technical, but accessible (like a senior engineer teaching a junior).
    6. Include a section called "Key Takeaways".
    """

    messages = [
        SystemMessage(content="You are a helpful technical writer."),
        HumanMessage(content=prompt)
    ]

    response = await llm.ainvoke(messages)

    return {"draft_content": response.content}


# Build the graph
workflow = StateGraph(ScribeState)
workflow.add_node("drafting", drafting_node)
workflow.set_entry_point("drafting")
workflow.add_edge("drafting", END)

scribe_graph = workflow.compile()
