from typing import List

from pydantic import BaseModel

from src.structs.step import BaseStep


class PlanningStep(BaseStep):
    agent: str
    html_files: List
    layout_template_files: List


class OrchestratorPlanningOutput(BaseModel):
    is_irrelevant: bool
    is_forbidden: bool
    steps: list[PlanningStep]
    modified: bool
    comments: str
