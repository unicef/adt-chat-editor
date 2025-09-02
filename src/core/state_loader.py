"""State checkpoint load/save utilities.

This module handles persistence of the agentic workflow state across requests.
"""

import json
import os
from ast import literal_eval

from langchain_core.messages import (
    AIMessage,
    AnyMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)

from src.settings import STATE_CHECKPOINTS_DIR, custom_logger
from src.structs import (
    ChatEditRequest,
    TailwindStatus,
    TranslatedHTMLStatus,
    UserLanguage,
    WorkflowStatus,
)
from src.workflows.state import ADTState


class StateCheckpointManager:
    """Load and save state checkpoints for a given session ID."""

    def __init__(self):
        """Initialize the checkpoint manager and ensure storage directory exists."""
        self.logger = custom_logger(self.__class__.__name__)
        os.makedirs(STATE_CHECKPOINTS_DIR, exist_ok=True)

    def create_new_state_checkpoint(
        self, request: ChatEditRequest, path: str
    ) -> ADTState:
        """Create a new state checkpoint for a given session ID.

        Args:
            request: The request object containing the session ID and user message.

        Returns:
            The new state checkpoint.
        """
        # Create directory if it doesn't exist
        os.makedirs(path, exist_ok=True)

        # Create new state checkpoint
        state_checkpoint = ADTState(
            messages=[HumanMessage(content=request.user_message)],
            user_query=request.user_message,
            session_id=request.session_id,
            tailwind_status=TailwindStatus.INSTALLED,
            translated_html_status=TranslatedHTMLStatus.INSTALLED,
        )
        if request.language:
            state_checkpoint.language = request.language
        if request.user_language:
            try:
                state_checkpoint.user_language = UserLanguage(request.user_language.lower())
            except ValueError:
                state_checkpoint.user_language = UserLanguage.en
        state_checkpoint.current_pages = request.pages

        return state_checkpoint

    def load_state_checkpoint(self, request: ChatEditRequest, path: str) -> ADTState:
        """Load the state checkpoint for a given session ID.

        Args:
            request: The request object containing the session ID and user message.
            path: The path to the checkpoint file.

        Returns:
            The state checkpoint for the given session ID.
        """
        try:
            with open(path, encoding="utf-8") as f:
                try:
                    raw = json.load(f)
                    # Backward compatibility: older versions stored a JSON string in JSON.
                    if isinstance(raw, str):
                        try:
                            state_dict = json.loads(raw)
                        except json.JSONDecodeError:
                            # Last resort: evaluate Python-literal-like strings
                            state_dict = literal_eval(raw)
                    else:
                        state_dict = raw

                    self.logger.debug(f"Loaded state dict: {state_dict}")

                    # Update messages and required fields
                    state_dict["messages"] = self._deserialize_messages(
                        state_dict.get("messages", [])
                    ) + [HumanMessage(content=request.user_message)]

                    state_dict["user_query"] = request.user_message
                    state_dict["session_id"] = request.session_id
                    state_dict["current_step_index"] = -1
                    state_dict["plan_accepted"] = False
                    state_dict["status"] = WorkflowStatus.IN_PROGRESS
                    state_dict["current_pages"] = request.pages
                    if request.language:
                        state_dict["language"] = request.language
                    if request.user_language:
                        try:
                            state_dict["user_language"] = UserLanguage(request.user_language.lower())
                        except ValueError:
                            state_dict["user_language"] = UserLanguage.en

                    state_checkpoint = ADTState(**state_dict)
                    self.logger.debug(f"Loading state checkpoint: {state_checkpoint}")
                    return state_checkpoint
                except json.JSONDecodeError as e:
                    self.logger.error(f"Error decoding JSON from {path}: {e}")
                    raise
        except FileNotFoundError:
            self.logger.info(f"No checkpoint found for session {request.session_id}")
            raise FileNotFoundError(
                f"No checkpoint found for session {request.session_id}"
            )
        except Exception as e:
            self.logger.error(f"Unexpected error loading checkpoint: {e}")
            raise Exception(f"Unexpected error loading checkpoint: {e}")

    def save_state_checkpoint(self, request: ChatEditRequest, output: dict):
        """Save the state checkpoint for a given session ID.

        Args:
            request: The request object containing the session ID and user message.
            output: The output of the workflow.
        """
        # Convert output to dict
        output["user_query"] = output["user_query"][0].content
        output: ADTState = ADTState(**output)
        self.logger.debug(f"Output: {output}")

        # Convert to dictionary (not nested JSON string)
        state_dict = output.model_dump(mode="json", serialize_as_any=True)
        # Ensure messages are stored in a simple JSON-serializable format
        state_dict["messages"] = self._serialize_messages(list(output.messages))
        self.logger.debug(f"State dict keys: {list(state_dict.keys())}")

        # Save state checkpoint
        checkpoint_path = os.path.join(
            os.getcwd(),
            STATE_CHECKPOINTS_DIR,
            request.session_id,
            "checkpoint.json",
        )
        self.logger.debug(f"Saving checkpoint to: {checkpoint_path}")
        try:
            with open(checkpoint_path, "w", encoding="utf-8") as f:
                json.dump(state_dict, f, ensure_ascii=False)
            self.logger.debug(f"Saved checkpoint to: {checkpoint_path}")
        except Exception as e:
            self.logger.error(f"Error saving checkpoint to {checkpoint_path}: {e}")
            raise

    @staticmethod
    def _serialize_messages(messages: list[BaseMessage]) -> list[dict]:
        """Convert LangChain messages to a simple JSON format.

        Args:
            messages: The messages to serialize.

        Returns:
            The serialized messages.
        """
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

    @staticmethod
    def _deserialize_messages(messages_data: list[dict]) -> list[AnyMessage]:
        """Convert JSON format back to LangChain messages.

        Args:
            messages_data: The messages data to deserialize.

        Returns:
            The deserialized messages.
        """
        message_types = {
            "human": HumanMessage,
            "ai": AIMessage,
            "system": SystemMessage,
        }
        return [
            message_types[msg["type"]](content=msg["content"]) for msg in messages_data
        ]
