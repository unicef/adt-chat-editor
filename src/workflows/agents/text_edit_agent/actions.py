import os
import json
from typing import List

from langchain_core.messages import AIMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig

from src.llm.llm_client import llm_client
from src.prompts import (
    TEXT_EDIT_SYSTEM_PROMPT,
    TEXT_EDIT_USER_PROMPT,
)
from src.settings import custom_logger, OUTPUT_DIR
from src.structs import StepStatus, TextEdit, TextEditResponse
from src.workflows.state import ADTState
from src.workflows.utils import (
    get_html_files,
    read_html_file,
    write_html_file,
)


# Initialize logger
logger = custom_logger("Text Edit Agent")

# Output parser
text_edits_parser = PydanticOutputParser(pydantic_object=TextEditResponse)


# Actions
async def detect_text_edits(state: ADTState, config: RunnableConfig) -> ADTState:
    """
    Detect text edits based on the instruction while preserving HTML structure.

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

    # Process each file
    text_edits: List[TextEdit] = []
    for html_file in html_files:

        # Read the file content
        html_content = await read_html_file(html_file)

        # Format messages
        formatted_messages = await messages.ainvoke(
            {
                "text": html_content,
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
    """
    Edit text in files based on the instruction while preserving HTML structure.

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
                OUTPUT_DIR, f"translations_{text_edit_translation.language}.json"
            )

            # Read and update the translation file
            with open(file_path, "r") as file:
                data = json.load(file)

            # Update the text
            data["texts"][text_edit.element_id] = text_edit_translation.text

            # Write the updated data back to file
            with open(file_path, "w") as file:
                json.dump(data, file, indent=2)

    # Add message about the file being processed
    message = f"The following files have been processed and updated based on the instruction: '{state.steps[state.current_step_index].step}' for the languages: '{', '.join(state.available_languages)}'\n"
    for file in state.steps[state.current_step_index].html_files:  # type: ignore
        message += f"\n- {file}"
    state.add_message(AIMessage(content=message))

    logger.info(
        f"Total files modified: {len(state.steps[state.current_step_index].html_files)}"
    )

    # Update step status
    if state.current_step_index >= 0 and state.current_step_index < len(state.steps):
        state.steps[state.current_step_index].status = StepStatus.SUCCESS

    return state
