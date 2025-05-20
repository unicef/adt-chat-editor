from enum import Enum

from src.structs.country import Country


class Language(Enum):
    EN = "English"
    ES = "Spanish"


LANGUAGE_MAP = {
    Country.UY: Language.ES,
    Country.USA: Language.EN,
}
