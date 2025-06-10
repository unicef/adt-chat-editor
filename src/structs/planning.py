from typing import List, Union

from pydantic import BaseModel

from src.structs.step import BaseStep
from src.structs.text_editing import TextEdit


class PlanningStep(BaseStep):
    agent: str
    html_files: List[str]
    layout_template_files: List[str]
    text_edits: Union[List[TextEdit], None] = None


class OrchestratorPlanningOutput(BaseModel):
    is_irrelevant: bool
    is_forbidden: bool
    steps: list[PlanningStep]
    modified: bool
    comments: str
