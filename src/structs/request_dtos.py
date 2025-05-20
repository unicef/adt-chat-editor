from pydantic import BaseModel, Field

from src.structs.country import Country
from src.structs.language import Language, LANGUAGE_MAP


class ChatRequest(BaseModel):
    user_query: str
    country: Country
    language: Language = Field(default_factory=lambda: LANGUAGE_MAP[Country.UY])
