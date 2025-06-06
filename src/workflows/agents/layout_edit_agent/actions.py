from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig

from src.llm.llm_client import llm_client
from src.prompts import (
    LAYOUT_EDIT_SYSTEM_PROMPT,
    LAYOUT_EDIT_USER_PROMPT,
)
from src.settings import (
    OUTPUT_DIR,
    TAILWIND_CSS_IN_DIR,
    TAILWIND_CSS_OUT_DIR,
    custom_logger,
)
from src.structs.status import StepStatus
from src.utils import (
    get_html_files,
    get_relative_path,
    read_html_file,
    write_html_file,
    update_tailwind,
)
from src.workflows.state import ADTState

# Initialize logger
logger = custom_logger("Layout Edit Agent")


# Actions
async def edit_layout(state: ADTState, config: RunnableConfig) -> ADTState:
    """Edit layout based on the instruction while preserving HTML semantics and structure.

    Args:
        state: The current state of the workflow
        config: The configuration for the workflow

    Returns:
        The updated state of the workflow
    """
    # Create prompt
    messages = ChatPromptTemplate.from_messages(
        [
            ("system", LAYOUT_EDIT_SYSTEM_PROMPT),
            ("user", LAYOUT_EDIT_USER_PROMPT),
        ]
    )

    # Define current state step
    current_step = state.steps[state.current_step_index]

    # Get the relevant and layout-base-template html files
    filtered_files = current_step.html_files

    # Get all relevant HTML files from output directory
    html_files = await get_html_files(OUTPUT_DIR)
    html_files = [html_file for html_file in html_files if html_file in filtered_files]
    
    # Process each relevant HTML file
    modified_files = []
    for html_file in html_files:

        # Read the file content
        rel_path = await get_relative_path(html_file, "data")
        html_content = await read_html_file(html_file)

        # Format messages
        formatted_messages = await messages.ainvoke(
            {
                "target_html_file": html_content,
                "instruction": current_step.step,
            },
            config,
        )

        # Call model
        response = await llm_client.ainvoke(formatted_messages, config)

        # Get edited layout from response
        edited_html = str(response.content)

        # Save edited text back to the same file
        await write_html_file(html_file, edited_html)

        # Save file path to modified files
        modified_files.append(rel_path)

    # Command to update the tailwind.css
    await update_tailwind(
        OUTPUT_DIR, 
        TAILWIND_CSS_IN_DIR, 
        TAILWIND_CSS_OUT_DIR
    )
    
    # Add message about the file being processed
    message = f"The following files have been processed and updated based on the instruction: '{current_step.step}'\n"
    for file in modified_files:
        message += f"- {file}\n"
    state.add_message(AIMessage(content=message))
    logger.info(f"Total files modified: {len(modified_files)}")

    # Update step status
    if 0 <= state.current_step_index < len(state.steps):
        state.steps[state.current_step_index].status = StepStatus.SUCCESS

    return state
