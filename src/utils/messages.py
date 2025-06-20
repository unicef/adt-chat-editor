from typing import Union

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage


def message_is_agent(
    message_type: Union[AIMessage, HumanMessage, SystemMessage],
) -> bool:
    """
    Check if the message is an agent message.

    Args:
        message_type: The type of message to check.

    Returns:
        True if the message is an agent message, False otherwise.
    """

    return isinstance(message_type, AIMessage) or isinstance(
        message_type, SystemMessage
    )


def message_is_human(
    message_type: Union[AIMessage, HumanMessage, SystemMessage],
) -> bool:
    """
    Check if the message is a human message.

    Args:
        message_type: The type of message to check.

    Returns:
        True if the message is a human message, False otherwise.
    """

    return isinstance(message_type, HumanMessage) or isinstance(message_type, AIMessage)
