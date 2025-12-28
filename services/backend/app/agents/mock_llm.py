from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from typing import List, Any, Optional


class MockChatModel(BaseChatModel):
    """
    A mock LLM for development and testing.
    Returns predefined responses without making API calls.
    """

    @property
    def _llm_type(self) -> str:
        return "mock"

    def _generate(
        self,
        messages: List[Any],
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> ChatResult:
        # Get the last user message
        last_message = messages[-1].content if messages else ""

        # Generate a mock response
        response = f"[Mock Response] I received your message about: {last_message[:100]}..."

        return ChatResult(
            generations=[
                ChatGeneration(
                    message=AIMessage(content=response)
                )
            ]
        )

    async def _agenerate(
        self,
        messages: List[Any],
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> ChatResult:
        return self._generate(messages, stop, **kwargs)
