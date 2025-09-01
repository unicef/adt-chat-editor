import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from src.utils.messages import message_is_agent, message_is_human


def test_message_is_agent():
    assert message_is_agent(AIMessage(content="hi")) is True
    assert message_is_agent(SystemMessage(content="sys")) is True
    assert message_is_agent(HumanMessage(content="user")) is False


def test_message_is_human():
    assert message_is_human(HumanMessage(content="hello")) is True
    assert message_is_human(AIMessage(content="bot")) is True
    assert message_is_human(SystemMessage(content="sys")) is False

