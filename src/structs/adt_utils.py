from pydantic import BaseModel
from typing import Optional


class RunAllRequest(BaseModel):
    target_dir: str
    start: int
    end: int

class RunAllResponse(BaseModel):
    status: str
    message: str
    output: Optional[str] = None
    error: Optional[str] = None
