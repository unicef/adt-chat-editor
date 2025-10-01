from pydantic_settings import BaseSettings, SettingsConfigDict

# Define default values
INPUT_DIR = "data/input"
OUTPUT_DIR = "data/output"
ADT_UTILS_DIR = "data/adt-utils"

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
    ADT_UTILS_DIR: str = ADT_UTILS_DIR
    STATE_CHECKPOINTS_DIR: str = STATE_CHECKPOINTS_DIR
    HTML_CONTENTS_DIR: str = HTML_CONTENTS_DIR
    NAV_HTML_DIR: str = NAV_HTML_DIR
    TRANSLATIONS_DIR: str = TRANSLATIONS_DIR
    TAILWIND_CSS_IN_DIR: str = TAILWIND_CSS_IN_DIR
    TAILWIND_CSS_OUT_DIR: str = TAILWIND_CSS_OUT_DIR
    BASE_BRANCH_NAME: str = BASE_BRANCH_NAME

    # From .env
    LANGSMITH_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4.1"  # default if not in .env
    OPENAI_CODEX_MODEL: str = "o3"  # default if not in .env
    GITHUB_TOKEN: str | None = None
    ADTS: str | None = None
    ACTIVE_ADT: str | None = None
    JWT_SECRET_KEY: str | None = None
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 1
    ADMIN_USERNAME: str | None = None
    ADMIN_PASSWORD: str | None = None
    FRONTEND_URL: str = "https://unicef.demos.marvik.cloud"

    # Pydantic v2 settings configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",  # Ignore extra env vars present in .env or environment
    )


settings = Settings()
