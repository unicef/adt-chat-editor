from enum import Enum


class UserLanguage(Enum):
    es = "es"
    en = "en"


class TranslatedHTMLStatus(str, Enum):
    NOT_INSTALLED = "not_installed"
    INSTALLING = "installing"
    INSTALLED = "installed"
    FAILED = "failed"
