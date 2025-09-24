"""Actions for the Text Edit Agent, including detection, application, and TTS regeneration."""

import asyncio
import json
import os
import subprocess
from typing import List

from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig

from src.llm.llm_client import llm_client
from src.prompts import (
    TEXT_EDIT_SYSTEM_PROMPT,
    TEXT_EDIT_USER_PROMPT,
)
from src.settings import (
    ADT_UTILS_DIR,
    OUTPUT_DIR,
    TRANSLATIONS_DIR,
    custom_logger,
)
from src.structs import StepStatus, TextEdit, TextEditResponse
from src.utils import (
    extract_layout_properties_async,
    get_html_files,
    get_message,
    load_translated_html_contents,
    read_html_file,
)
from src.workflows.state import ADTState

# Initialize logger
logger = custom_logger("Text Edit Agent")

# Output parser
text_edits_parser = PydanticOutputParser(pydantic_object=TextEditResponse)


# Actions
async def detect_text_edits(state: ADTState, config: RunnableConfig) -> ADTState:
    """Detect text edits based on the instruction while preserving HTML structure.

    Args:
        state: The current state of the workflow
        config: The configuration for the workflow

    Returns:
        The updated state of the workflow
    """
    # Create prompt
    messages = ChatPromptTemplate.from_messages(
        [
            ("system", TEXT_EDIT_SYSTEM_PROMPT),
            ("user", TEXT_EDIT_USER_PROMPT),
        ]
    )

    # Define current state step
    current_step = state.steps[state.current_step_index]

    # Get the relevant and layout-base-template html files
    filtered_files = current_step.html_files

    # Get all relevant HTML files from output directory
    html_files = await get_html_files(OUTPUT_DIR)
    html_files = [html_file for html_file in html_files if html_file in filtered_files]

    # Load translated HTML contents
    translated_html_contents = await load_translated_html_contents(
        language=state.language
    )

    # Process each file
    text_edits: List[TextEdit] = []
    for html_file in html_files:

        # Read the file content
        html_content = await read_html_file(html_file)
        html_content, _ = await extract_layout_properties_async(html_content)

        translated_contents = next(
            (
                item[html_file] for item in translated_html_contents 
                if item.get(html_file)
            ),
            None
        )

        # Format messages
        formatted_messages = await messages.ainvoke(
            {
                "text": html_content,
                "translated_texts": translated_contents,
                "instruction": current_step.step,
                "languages": state.available_languages,
            },
            config,
        )

        # Call model
        response = await llm_client.ainvoke(formatted_messages, config)

        # Parse the response
        new_text_edits = text_edits_parser.parse(str(response.content))
        text_edits.extend(new_text_edits.text_edits)

    # Add the text edits to the state
    # TODO: Reorder edits by file (language)
    state.steps[state.current_step_index].text_edits = text_edits
    return state


def edit_texts(state: ADTState, config: RunnableConfig) -> ADTState:
    """Edit text in files based on the instruction while preserving HTML structure.

    Args:
        state: The current state of the workflow
        config: The configuration for the workflow

    Returns:
        The updated state of the workflow
    """
    if not state.steps[state.current_step_index].text_edits:
        logger.warning("No text edits to process")
        return state

    # Process each text edit
    for text_edit in state.steps[state.current_step_index].text_edits:  # type: ignore
        for text_edit_translation in text_edit.translations:
            file_path = os.path.join(
                OUTPUT_DIR,
                TRANSLATIONS_DIR,
                text_edit_translation.language,
                "texts.json",
            )

            # Read and update the translation file
            with open(file_path) as file:
                data = json.load(file)

            # Update the text
            data[text_edit.element_id] = text_edit_translation.text

            # Write the updated data back to file
            with open(file_path, "w") as file:
                json.dump(data, file, indent=2)

    # Add message about the file being processed
    message = f"The following files have been processed and updated based on the instruction: '{state.steps[state.current_step_index].step}' for the languages: '{', '.join(state.available_languages)}'\n"
    for file in state.steps[state.current_step_index].html_files:  # type: ignore
        message += f"\n- {file}"
    state.add_message(SystemMessage(content=message))
    state.add_message(
        AIMessage(
            content=get_message(state.user_language.value, "final_response")
        )
    )

    logger.info(
        f"Total files modified: {len(state.steps[state.current_step_index].html_files)}"
    )

    # Update step status
    if state.current_step_index >= 0 and state.current_step_index < len(state.steps):
        state.steps[state.current_step_index].status = StepStatus.SUCCESS

    return state


async def regenerate_tts_for_edits(state: ADTState, config: RunnableConfig) -> ADTState:
    """Regenerate TTS audio only for edited data-ids across all available languages.

    This node triggers the existing adt-utils regeneration script with the
    --data-ids flag so it only processes the affected keys.
    """
    # Collect data-ids from the current step's text edits
    edits = state.steps[state.current_step_index].text_edits or []
    data_ids = sorted({edit.element_id for edit in edits})

    if not data_ids:
        logger.info("No data-ids to regenerate TTS for. Skipping TTS regeneration.")
        return state

    if not state.available_languages:
        logger.warning("No available languages found. Skipping TTS regeneration.")
        return state

    # Ensure API key is available
    if not os.getenv("OPENAI_API_KEY"):
        msg = (
            "Skipping TTS regeneration: OPENAI_API_KEY is not set. "
            "Set it in the environment or .env to enable TTS generation."
        )
        logger.warning(msg)
        state.add_message(SystemMessage(content=msg))
        return state

    # Build command to call the adt-utils regenerate_tts script
    # Use path relative to ADT_UTILS_DIR (cwd) to avoid duplicating directory segments
    script_rel_path = os.path.join("src", "regeneration", "scripts", "regenerate_tts.py")
    script_fs_path = os.path.join(ADT_UTILS_DIR, script_rel_path)

    if not os.path.exists(script_fs_path):
        logger.error(
            f"regenerate_tts script not found at {script_fs_path}. Skipping."
        )
        return state

    abs_output_dir = os.path.abspath(OUTPUT_DIR)
    languages_csv = ",".join(state.available_languages)
    ids_csv = ",".join(data_ids)

    command = [
        "python",
        script_rel_path,
        abs_output_dir,
        "--language",
        languages_csv,
        "--data-ids",
        ids_csv,
    ]

    logger.info(
        "Executing TTS regeneration for edited data-ids: "
        + f"{len(data_ids)} ids across languages [{languages_csv}]"
    )

    # Run the script asynchronously without blocking the event loop
    def _run():
        return subprocess.run(
            command,
            cwd=ADT_UTILS_DIR,
            capture_output=True,
            text=True,
            timeout=300,
        )

    try:
        result = await asyncio.to_thread(_run)
    except subprocess.TimeoutExpired:
        logger.error("TTS regeneration timed out after 300s")
        return state
    except Exception as e:
        logger.error(f"Error executing TTS regeneration: {e}")
        return state

    # Summarize outcome in workflow messages
    if result.returncode == 0:
        summary = (
            "TTS regeneration completed for edited items.\n\n"
            "Summary:\n" + (result.stdout or "(no output)")
        )
        state.add_message(SystemMessage(content=summary))
        logger.info("TTS regeneration completed successfully")
    else:
        error_details = []
        if result.stderr:
            error_details.append(f"STDERR:\n{result.stderr}")
        if result.stdout:
            error_details.append(f"STDOUT:\n{result.stdout}")
        message = (
            "TTS regeneration encountered an error.\n\n" + "\n\n".join(error_details)
        )
        state.add_message(SystemMessage(content=message))
        logger.error(f"TTS regeneration failed with return code {result.returncode}.")
        if result.stderr:
            logger.error(f"STDERR: {result.stderr}")
        if result.stdout:
            logger.error(f"STDOUT: {result.stdout}")

    return state
