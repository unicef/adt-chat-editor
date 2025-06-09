from dataclasses import dataclass, field
from typing import Annotated, Optional, Sequence

from pydantic import BaseModel, Field
from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages

from src.structs import Language, WorkflowStatus
from src.structs.planning import PlanningStep
from src.utils import get_language_from_translation_files


class BaseState(BaseModel):
    """
    Defines the input state for the agent, representing a narrower interface to the outside world.
    This class is used to define the initial state and structure of incoming data.
    """

    messages: Annotated[Sequence[AnyMessage], add_messages] = Field(
        default_factory=list
    )

    def add_message(self, message: AnyMessage) -> None:
        self.messages = list(self.messages) + [message]


class ADTState(BaseState):
    """
    Represents the complete state of the agent, extending State with additional attributes.
    This class can be used to store any information needed throughout the agent's lifecycle.
    """

    # Main task
    user_query: Annotated[str, add_messages] = Field(default="")
    status: WorkflowStatus = Field(default=WorkflowStatus.IN_PROGRESS)
    session_id: str = Field(default="")

    # Steps
    steps: list[PlanningStep] = Field(default_factory=list)
    current_step_index: int = Field(default=-1)
    completed_steps: list[PlanningStep] = Field(default_factory=list)
    plan_accepted: bool = Field(default=False)
    plan_display: str = Field(default="")

    # Flags
    is_irrelevant_query: bool = Field(default=False)
    is_forbidden_query: bool = Field(default=False)

    # Information
    available_languages: list[str] = Field(default_factory=list)

    # Configs
    language: Optional[str] = None

    async def initialize_languages(self) -> None:
        """Initialize the available languages asynchronously."""
        self.available_languages = await get_language_from_translation_files()
