from typing import Any, cast

from langchain.chat_models.base import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig

from src.workflows.state import ADTState


async def async_model_call(
    llm_client: BaseChatModel,
    state: ADTState,
    config: RunnableConfig,
    formatted_prompt: Any,
) -> ADTState:
    """
    Make a client call to the LLM.

    Args:
        llm_client: The LLM client to use.
        state: The state of the agent.
        config: The configuration of the agent.
        formatted_prompt: The formatted prompt to use.

    Returns:
        The state of the agent.
    """
    response = cast(AIMessage, await llm_client.ainvoke(formatted_prompt, config))

    # Update state with response
    state.add_message(response)
    return state
