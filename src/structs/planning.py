from pydantic import BaseModel

from src.structs.step import BaseStep


class PlanningStep(BaseStep):
    agent: str


class OrchestratorPlanningOutput(BaseModel):
    is_irrelevant: bool
    is_forbidden: bool
    steps: list[PlanningStep]
    modified: bool
    comments: str
