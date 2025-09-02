"""LLM client invocation utilities."""

from typing import Any, cast

from langchain.chat_models.base import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig


async def async_model_call(
    llm_client: BaseChatModel,
    config: RunnableConfig,
    formatted_prompt: Any,
) -> AIMessage:
    """Call the LLM client and return an AIMessage response.

    Args:
        llm_client: The LLM client to use.
        config: The configuration of the agent.
        formatted_prompt: The formatted prompt to use.

    Returns:
        The LLM response as an AIMessage.
    """
    response = cast(AIMessage, await llm_client.ainvoke(formatted_prompt, config))
    return response
