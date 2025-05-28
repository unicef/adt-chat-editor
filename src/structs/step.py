from pydantic import BaseModel, Field

from src.structs.status import StepStatus


class BaseStep(BaseModel):
    step: str
    non_technical_description: str
    status: StepStatus = Field(default=StepStatus.PENDING)
