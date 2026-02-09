from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ExecuteCommandRequest(BaseModel):
    command: str
    working_directory: Optional[str] = None
    is_prompt: bool = Field(
        default=False,
        alias="isPrompt",
        description="True if user is in Prompt Mode (send to Codex), False if Command Mode (execute as shell command)"
    )

    class Config:
        populate_by_name = True  # Accept both 'is_prompt' and 'isPrompt'


class CommandResponse(BaseModel):
    output: str
    exit_code: int
    timestamp: str


class CommandHistory(BaseModel):
    command: str
    output: str
    timestamp: str
    exit_code: int
