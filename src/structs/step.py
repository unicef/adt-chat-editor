from pydantic import BaseModel, Field

from src.structs.status import StepStatus


class BaseStep(BaseModel):
    step: str
    step_status: StepStatus = Field(default=StepStatus.PENDING)
