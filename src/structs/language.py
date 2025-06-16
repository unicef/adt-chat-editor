from enum import Enum


class Language(Enum):
    EN = "English"
    ES = "Spanish"


class TranslatedHTMLStatus(str, Enum):
    NOT_INSTALLED = "not_installed"
    INSTALLING = "installing"
    INSTALLED = "installed"
    FAILED = "failed"
