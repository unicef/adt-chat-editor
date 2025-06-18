from ast import literal_eval
import json
import os

from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
    BaseMessage,
    AnyMessage,
)

from src.settings import custom_logger, STATE_CHECKPOINTS_DIR
from src.structs import (
    ChatEditRequest,
    TranslatedHTMLStatus,
    TailwindStatus,
    WorkflowStatus,
)
from src.workflows.state import ADTState


class StateCheckpointManager:
    """
    Class to load and save the state checkpoint for a given session ID.
    """

    def __init__(self):
        self.logger = custom_logger(self.__class__.__name__)
        # Ensure state checkpoints directory exists
        os.makedirs(STATE_CHECKPOINTS_DIR, exist_ok=True)

    def create_new_state_checkpoint(
        self, request: ChatEditRequest, path: str
    ) -> ADTState:
        """
        Function to create a new state checkpoint for a given session ID.

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
            language=request.language,
            current_pages=request.pages,
            tailwind_status=TailwindStatus.INSTALLED,
            translated_html_status=TranslatedHTMLStatus.INSTALLED,
        )
        if request.language:
            state_checkpoint.language = request.language
        if request.pages:
            state_checkpoint.current_pages = request.pages

        return state_checkpoint

    def load_state_checkpoint(self, request: ChatEditRequest, path: str) -> ADTState:
        """
        Function to load the state checkpoint for a given session ID.

        Args:
            request: The request object containing the session ID and user message.
            path: The path to the checkpoint file.

        Returns:
            The state checkpoint for the given session ID.
        """
        try:
            with open(path, "r") as f:
                try:
                    json_string = f.read()
                    json_string = json_string.replace("null", "None")
                    json_string = json_string.replace("false", "False")
                    json_string = json_string.replace("true", "True")
                    state_dict = json.loads(json_string)
                    state_dict = literal_eval(state_dict)
                    self.logger.debug(f"Loaded state dict: {state_dict}")

                    # Update messages and required fields
                    state_dict["messages"] = self._deserialize_messages(
                        state_dict["messages"]
                    ) + [HumanMessage(content=request.user_message)]
                    state_dict["user_query"] = request.user_message
                    state_dict["session_id"] = request.session_id
                    state_dict["current_step_index"] = -1
                    state_dict["plan_accepted"] = False
                    state_dict["status"] = WorkflowStatus.IN_PROGRESS

                    state_checkpoint = ADTState(**state_dict)
                    self.logger.debug(f"Loading state checkpoint: {state_checkpoint}")
                    return state_checkpoint
                except json.JSONDecodeError as e:
                    self.logger.error(f"Error decoding JSON from {path}: {e}")
                    # If file is corrupted, create a new checkpoint
                    raise json.JSONDecodeError(
                        f"Error decoding JSON from {path}: {e}", json_string, 0
                    )
        except FileNotFoundError:
            self.logger.info(f"No checkpoint found for session {request.session_id}")
            raise FileNotFoundError(
                f"No checkpoint found for session {request.session_id}"
            )
        except Exception as e:
            self.logger.error(f"Unexpected error loading checkpoint: {e}")
            raise Exception(f"Unexpected error loading checkpoint: {e}")

    def save_state_checkpoint(self, request: ChatEditRequest, output: dict):
        """
        Function to save the state checkpoint for a given session ID.

        Args:
            request: The request object containing the session ID and user message.
            output: The output of the workflow.
        """
        # Convert output to dict
        output["user_query"] = output["user_query"][0].content
        output: ADTState = ADTState(**output)
        self.logger.debug(f"Output: {output}")

        # Convert to dictionary instead of JSON string
        state_dict = output.model_dump_json(serialize_as_any=True)
        self.logger.debug(f"State dict: {state_dict}")

        # Save state checkpoint
        checkpoint_path = os.path.join(
            os.getcwd(),
            STATE_CHECKPOINTS_DIR,
            request.session_id,
            f"checkpoint.json",
        )
        self.logger.debug(f"Saving checkpoint to: {checkpoint_path}")
        try:
            with open(checkpoint_path, "w") as f:
                json.dump(state_dict, f)
            self.logger.debug(f"Saved checkpoint to: {checkpoint_path}")
        except Exception as e:
            self.logger.error(f"Error saving checkpoint to {checkpoint_path}: {e}")
            raise

    @staticmethod
    def _serialize_messages(messages: list[BaseMessage]) -> list[dict]:
        """
        Convert LangChain messages to a simple JSON format.

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
        """
        Convert JSON format back to LangChain messages.

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
