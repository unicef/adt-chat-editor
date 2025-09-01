from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from src.core.state_loader import StateCheckpointManager


def test_serialize_deserialize_messages_roundtrip():
    mgr = StateCheckpointManager()
    messages = [
        HumanMessage(content="hello"),
        AIMessage(content="bot"),
        SystemMessage(content="sys"),
    ]

    data = mgr._serialize_messages(messages)
    restored = mgr._deserialize_messages(data)

    assert len(restored) == 3
    assert isinstance(restored[0], HumanMessage)
    assert isinstance(restored[1], AIMessage)
    assert isinstance(restored[2], SystemMessage)
    assert restored[0].content == "hello"
    assert restored[1].content == "bot"
    assert restored[2].content == "sys"

