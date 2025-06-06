import os
import json
from dataclasses import asdict

from fastapi import APIRouter
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.pregel.io import AddableValuesDict

from src.structs import ChatEditRequest, ChatEditResponse, ChatMessageResponse
from src.settings import custom_logger
from src.utils.messages import message_is_agent, message_is_human
from src.workflows.graph import graph
from src.settings import STATE_CHECKPOINTS_DIR
from src.workflows.state import ADTState


# Create logger
logger = custom_logger("Chat API Router")


# Create router
router = APIRouter(prefix="/chat", tags=["Chat"])


def serialize_messages(messages):
    """Convert LangChain messages to a simple JSON format."""
    return [
        {
            "type": (
                "human"
                if isinstance(msg, HumanMessage)
                else "ai" if isinstance(msg, AIMessage) else "system"
            ),
            "content": msg.content,
        }
        for msg in messages
    ]


def deserialize_messages(messages_data):
    """Convert JSON format back to LangChain messages."""
    message_types = {
        "human": HumanMessage,
        "ai": AIMessage,
        "system": SystemMessage,
    }
    return [message_types[msg["type"]](content=msg["content"]) for msg in messages_data]


# Define the endpoints
@router.post("/edit", response_model=ChatEditResponse)
async def chat_edit(request: ChatEditRequest) -> ChatEditResponse:
    """Make changes on the current version of the ADT using natural language."""
    logger.debug(
        f"Chat edit request: session_id={request.session_id}, language={request.language}"
    )

    # Load state checkpoint
    if os.path.exists(
        os.path.join(STATE_CHECKPOINTS_DIR, f"checkpoint-{request.session_id}.json")
    ):
        with open(
            os.path.join(
                STATE_CHECKPOINTS_DIR, f"checkpoint-{request.session_id}.json"
            ),
            "r",
        ) as f:
            state_data = json.load(f)
            state_checkpoint = ADTState(
                messages=deserialize_messages(state_data["messages"])
                + [HumanMessage(content=request.user_message)],
                user_query=request.user_message,
                session_id=request.session_id,
            )
            if "language" in state_data:
                state_checkpoint.language = state_data["language"]
    else:
        state_checkpoint = ADTState(
            messages=[HumanMessage(content=request.user_message)],
            user_query=request.user_message,
            session_id=request.session_id,
        )
        if request.language:
            state_checkpoint.language = request.language

    output = await graph.ainvoke(state_checkpoint)

    # Format messages
    for message in output["messages"]:
        print(f"Message: {message.content} -> Type: {type(message)}")

    messages = [
        ChatMessageResponse(
            message_number=k,
            content=message.content,
            is_agent=message_is_agent(message),
            show=message_is_human(message),
        )
        for k, message in enumerate(output["messages"])
    ]

    # Create response
    response = ChatEditResponse(
        session_id=request.session_id,
        messages=messages,
        book_information=request.book_information,
    )

    # Save state checkpoint
    serialized_output = {
        **dict(output),
    }
    serialized_output["messages"] = serialize_messages(output["messages"])
    serialized_output["user_query"] = ""
    serialized_output["status"] = serialized_output["status"].value

    logger.info(f"Serialized output: {serialized_output}")
    with open(
        os.path.join(STATE_CHECKPOINTS_DIR, f"checkpoint-{request.session_id}.json"),
        "w",
    ) as f:
        json.dump(serialized_output, f)

    return response
