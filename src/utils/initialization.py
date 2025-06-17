import os

from src.settings import HTML_CONTENTS_DIR, OUTPUT_DIR, TRANSLATIONS_DIR, custom_logger
from src.structs import TailwindStatus, TranslatedHTMLStatus
from src.utils.file_utils import (
    extract_and_save_html_contents,
    get_language_from_translation_files,
    install_tailwind,
)


# Create logger
logger = custom_logger("Initialization")


# Define the initialization functions
async def initialize_languages() -> list[str]:
    """
    Initialize the available languages asynchronously.
    """
    logger.info("Initializing languages")
    available_languages = await get_language_from_translation_files()
    logger.info(f"Available languages: {available_languages}")
    return available_languages


async def initialize_tailwind() -> TailwindStatus:
    """
    Initialize Tailwind resources asynchronously.

    Returns:
        TailwindStatus: The status of the Tailwind resources.
    """
    logger.info("Initializing Tailwind")
    tailwind_status = TailwindStatus.INSTALLING
    try:
        success = await install_tailwind()
        if success:
            tailwind_status = TailwindStatus.INSTALLED
        else:
            tailwind_status = TailwindStatus.FAILED
    except Exception:
        tailwind_status = TailwindStatus.FAILED
    logger.info(f"Tailwind status: {tailwind_status.value}")
    return tailwind_status


async def initialize_translated_html_content(language: str) -> TranslatedHTMLStatus:
    """
    Initialize translated HTML contents asynchronously.

    Args:
        language: The language to initialize the translated HTML content for.

    Returns:
        TranslatedHTMLStatus: The status of the translated HTML content.
    """
    logger.info(f"Initializing translated HTML content for language: {language}")
    translated_html_status = TranslatedHTMLStatus.INSTALLING
    try:
        # Create HTML contents directory if it doesn't exist
        os.makedirs(HTML_CONTENTS_DIR, exist_ok=True)

        success = await extract_and_save_html_contents(language=language)
        if success:
            translated_html_status = TranslatedHTMLStatus.INSTALLED
        else:
            translated_html_status = TranslatedHTMLStatus.FAILED
    except Exception as e:
        translated_html_status = TranslatedHTMLStatus.FAILED
        logger.error(f"Error initializing translated HTML content: {e}")
    logger.info(f"Translated HTML status: {translated_html_status.value}")
    return translated_html_status
