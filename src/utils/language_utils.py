import json
import logging

from pathlib import Path

MESSAGES_PATH = Path(__file__).parent / "messages.json"


try:
    with open(MESSAGES_PATH, encoding="utf-8") as f:
        LANG_CONFIG = json.load(f)
except Exception as e:
    logging.error(f"[Localization] Could not load messages.json: {e}")
    LANG_CONFIG = {}


def normalize_lang(accept_language: str) -> str:
    """
    Normalize 'en-US', 'es-AR', etc. to 'en', 'es'.
    Falls back to 'en' if unknown.
    """
    if not accept_language:
        return "en"
    code = accept_language.split(",")[0].split("-")[0].lower()
    return code if code in LANG_CONFIG else "en"


def get_message(lang_code: str, key: str) -> str:
    """
    Retrieve a message for a given language and key.
    Falls back to English if not available.
    """
    # Try requested language
    normalize_lang_code = normalize_lang(lang_code)
    lang_data = LANG_CONFIG.get(normalize_lang_code)
    if lang_data:
        msg = lang_data.get("messages", {}).get(key)
        if msg:
            return msg

    # Fallback to English
    fallback_msg = LANG_CONFIG.get("en", {}).get("messages", {}).get(key)
    if fallback_msg:
        logging.warning(
            f"[Localization] Missing '{key}' in '{normalize_lang_code}', using English fallback."
        )
        return fallback_msg

    # Ultimate fallback
    logging.error(f"[Localization] Missing message key: '{key}'")
    return f"[Missing message: '{key}']"


def get_language_name(lang_code: str) -> str:
    """
    Get the user-friendly language name for the LLM system.
    Defaults to 'English'.
    """
    normalize_lang_code = normalize_lang(lang_code)
    return LANG_CONFIG.get(normalize_lang_code, LANG_CONFIG.get("en", {})).get(
        "llm_name", "English"
    )
