from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ExecuteCommandRequest(BaseModel):
    command: str
    working_directory: Optional[str] = None


class CommandResponse(BaseModel):
    output: str
    exit_code: int
    timestamp: str


class CommandHistory(BaseModel):
    command: str
    output: str
    timestamp: str
    exit_code: int
