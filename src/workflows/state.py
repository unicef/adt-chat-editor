from dataclasses import dataclass, field
from typing import Annotated, Optional, Sequence

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages

from src.structs import WorkflowStatus
from src.structs.planning import PlanningStep


@dataclass
class BaseState:
    """
    Defines the input state for the agent, representing a narrower interface to the outside world.
    This class is used to define the initial state and structure of incoming data.
    """

    messages: Annotated[Sequence[AnyMessage], add_messages] = field(
        default_factory=list
    )

    def add_message(self, message: AnyMessage) -> None:
        self.messages = list(self.messages) + [message]


@dataclass
class ADTState(BaseState):
    """
    Represents the complete state of the agent, extending State with additional attributes.
    This class can be used to store any information needed throughout the agent's lifecycle.
    """

    # Main task
    user_query: Annotated[str, add_messages] = field(default="")
    status: WorkflowStatus = field(default=WorkflowStatus.IN_PROGRESS)

    # Steps
    steps: list[PlanningStep] = field(default_factory=list)
    current_step_index: int = field(default=-1)
    completed_steps: list[PlanningStep] = field(default_factory=list)
    plan_accepted: bool = field(default=False)
    plan_display: str = field(default="")
    # Flags
    is_irrelevant_query: bool = field(default=False)
    is_forbidden_query: bool = field(default=False)

    # Configs
    language: Optional[str] = None
