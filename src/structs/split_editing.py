from typing import List
from pydantic import BaseModel


class SplitEdit(BaseModel):
    split_html_file: str


class SplitEditResponse(BaseModel):
    split_edits: List[SplitEdit]
