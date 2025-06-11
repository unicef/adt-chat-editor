from dataclasses import field
from typing import Annotated, Optional, Sequence

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from pydantic import BaseModel, Field

from src.settings import OUTPUT_DIR, TRANSLATIONS_DIR
from src.structs import (
    TailwindStatus,
    TranslatedHTMLStatus,
    WorkflowStatus,
)
from src.structs.planning import PlanningStep
from src.utils import (
    extract_and_save_html_contents,
    get_language_from_translation_files,
    install_tailwind,
)


class BaseState(BaseModel):
    """Defines the input state for the agent, representing a narrower interface to the outside world.
    This class is used to define the initial state and structure of incoming data.
    """

    messages: Annotated[Sequence[AnyMessage], add_messages] = Field(
        default_factory=list
    )

    def add_message(self, message: AnyMessage) -> None:
        self.messages = list(self.messages) + [message]


class ADTState(BaseState):
    """Represents the complete state of the agent, extending State with additional attributes.
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
    plan_shown_to_user: bool = Field(default=False)
    plan_display: str = Field(default="")

    # Flags
    is_irrelevant_query: bool = Field(default=False)
    is_forbidden_query: bool = Field(default=False)

    # Information
    available_languages: list[str] = field(default_factory=list)
    tailwind_status: TailwindStatus = field(default=TailwindStatus.NOT_INSTALLED)
    translated_html_status: TranslatedHTMLStatus = field(default=TranslatedHTMLStatus.NOT_INSTALLED)

    # Configs
    language: Optional[str] = None

    async def initialize_languages(self) -> None:
        """Initialize the available languages asynchronously."""
        self.available_languages = await get_language_from_translation_files()

    async def initialize_tailwind(self) -> None:
        """Initialize Tailwind resources asynchronously."""
        self.tailwind_status = TailwindStatus.INSTALLING
        try:
            success = await install_tailwind()
            if success:
                self.tailwind_status = TailwindStatus.INSTALLED
            else:
                self.tailwind_status = TailwindStatus.FAILED
        except Exception:
            self.tailwind_status = TailwindStatus.FAILED

    async def initialize_translated_html_content(self, language: str) -> None:
        """Initialize translated HTML contents asynchronously."""
        self.translated_html_status = TranslatedHTMLStatus.INSTALLING
        try:
            success = await extract_and_save_html_contents(
                language=language,
                output_dir=OUTPUT_DIR,
                translations_dir=TRANSLATIONS_DIR
            )
            if success:
                self.translated_html_status = TranslatedHTMLStatus.INSTALLED
            else:
                self.translated_html_status = TranslatedHTMLStatus.FAILED
        except Exception:
            self.translated_html_status = TranslatedHTMLStatus.FAILED