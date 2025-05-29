from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig

from src.settings import custom_logger, OUTPUT_DIR
from src.structs.status import StepStatus
from src.workflows.state import ADTState
from src.utils import (
    get_html_files,
    read_html_file,
    write_html_file,
    delete_html_files_async,
)

logger = custom_logger("Web Delete Agent")


async def web_delete(state: ADTState, config: RunnableConfig) -> ADTState:
    """Delete HTML files based on the instruction."""

    # Define current state step
    current_step = state.steps[state.current_step_index]

    # Get the relevant and layout-base-template html files 
    filtered_files = current_step.html_files

    # Get all relevant HTML files from output directory
    html_files = await get_html_files(OUTPUT_DIR)
    html_files = [html_file for html_file in html_files if html_file in filtered_files]
    
    # Delete files
    deleted_files = html_files
    await delete_html_files_async(deleted_files)
    
    # Add message about the file being processed
    message = f"The following files have been processed and updated based on the instruction: '{current_step.step}'\n"
    for file in deleted_files:
        message += f"- {file}\n"
    state.add_message(AIMessage(content=message))
    logger.info(f"Total files modified: {len(deleted_files)}")

    # Update step status
    if 0 <= state.current_step_index < len(state.steps):
        state.steps[state.current_step_index].status = StepStatus.SUCCESS

    return state
