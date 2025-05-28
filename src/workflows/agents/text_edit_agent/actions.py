from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig

from src.llm.llm_client import llm_client
from src.prompts import (
    TEXT_EDIT_SYSTEM_PROMPT,
    TEXT_EDIT_USER_PROMPT,
)
from src.settings import custom_logger, OUTPUT_DIR
from src.structs.status import StepStatus
from src.workflows.state import ADTState
from src.workflows.utils import (
    get_relative_path,
    get_html_files,
    read_html_file,
    write_html_file,
)


# Initialize logger
logger = custom_logger("Text Edit Agent")


# Actions
async def edit_text(state: ADTState, config: RunnableConfig) -> ADTState:
    """
    Edit text based on the instruction while preserving HTML structure.

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
    modified_files = []
    for html_file in html_files:

        # Read the file content
        rel_path = await get_relative_path(html_file, "data")
        html_content = await read_html_file(html_file)

        # Format messages
        formatted_messages = await messages.ainvoke(
            {
                "text": html_content,
                "instruction": current_step.step,
            },
            config,
        )

        # Call model
        response = await llm_client.ainvoke(formatted_messages, config)
        edited_text = str(response.content)

        # Save edited text back to the same file
        await write_html_file(html_file, edited_text)

        # Save file path to modified files
        modified_files.append(rel_path)

    # Add message about the file being processed
    message = f"The following files have been processed and updated based on the instruction: '{current_step.step}'\n"
    for file in modified_files:
        message += f"\n- {file}"
    state.add_message(AIMessage(content=message))

    logger.info(f"Total files modified: {len(modified_files)}")

    # Update step status
    if state.current_step_index >= 0 and state.current_step_index < len(state.steps):
        state.steps[state.current_step_index].status = StepStatus.SUCCESS

    return state
