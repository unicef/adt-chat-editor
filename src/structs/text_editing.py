from enum import Enum
from typing import List
from pydantic import BaseModel


class TextEditElement(Enum):
    TEXT = "texts"
    VERB = "verbs"
    ARIA = "aria"
    PLACEHOLDER = "placeholder"
    IMG_CAPTION = "img"
    SECTION_ELI5 = "sectioneli5"
    EASYREAD_TEXT = "easyread-text"


class TextEditTranslation(BaseModel):
    language: str
    text: str


class TextEdit(BaseModel):
    element: TextEditElement
    element_id: str
    translations: List[TextEditTranslation]


class TextEditResponse(BaseModel):
    text_edits: List[TextEdit]
