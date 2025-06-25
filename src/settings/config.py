from pydantic_settings import BaseSettings

INPUT_DIR = "data/input"
OUTPUT_DIR = "data/output"

STATE_CHECKPOINTS_DIR = "tmp/state_checkpoints"
HTML_CONTENTS_DIR = "tmp/html_contents"

NAV_HTML_DIR = "content/navigation/nav.html"
TRANSLATIONS_DIR = "content/i18n"
TAILWIND_CSS_IN_DIR = "assets/tailwind_css.css"
TAILWIND_CSS_OUT_DIR = "content/tailwind_output.css"

BASE_BRANCH_NAME = "adt_chat_editor/"

class Settings(BaseSettings):
    INPUT_DIR: str = INPUT_DIR
    OUTPUT_DIR: str = OUTPUT_DIR
    STATE_CHECKPOINTS_DIR: str = STATE_CHECKPOINTS_DIR
    HTML_CONTENTS_DIR: str = HTML_CONTENTS_DIR
    NAV_HTML_DIR: str = NAV_HTML_DIR
    TRANSLATIONS_DIR: str = TRANSLATIONS_DIR
    TAILWIND_CSS_IN_DIR: str = TAILWIND_CSS_IN_DIR
    TAILWIND_CSS_OUT_DIR: str = TAILWIND_CSS_OUT_DIR
    BASE_BRANCH_NAME: str = BASE_BRANCH_NAME
