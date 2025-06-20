from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from src.settings import (
    NAV_HTML_DIR,
    OUTPUT_DIR,
    custom_logger,
)
from src.structs import (
    StepStatus, 
    TranslatedHTMLStatus
)
from src.utils import (
    delete_html_files_async,
    read_html_file,
    remove_nav_line_by_href,
    write_html_file,
    get_message,
)
from src.workflows.state import ADTState

logger = custom_logger("Web Delete Agent")


async def web_delete(state: ADTState, config: RunnableConfig) -> ADTState:
    """Delete HTML files based on the instruction."""
    # Define current state step
    current_step = state.steps[state.current_step_index]

    # Get the relevant html files
    deleted_files = current_step.html_files

    # Delete files
    await delete_html_files_async(deleted_files, OUTPUT_DIR)

    # Update nav
    nav_html = await read_html_file(OUTPUT_DIR + NAV_HTML_DIR)
    for file_name in deleted_files:
        file_name = file_name.split("/")[-1]
        try:
            nav_html = await remove_nav_line_by_href(nav_html, file_name)
        except Exception as e:
            logger.info(f"File couldn't be deleted in nav: {e}")
            continue
    await write_html_file(OUTPUT_DIR + NAV_HTML_DIR, nav_html)

    # Add message about the file being processed
    message = f"The following files have been deleted based on based on the instruction: '{current_step.step}'\n"
    for file in deleted_files:
        message += f"- {file}\n"
    state.add_message(SystemMessage(content=message))
    state.add_message(
        AIMessage(
            content=get_message(state.user_language.value, "final_response")
        )
    )
    logger.info(f"Total files deleted: {len(deleted_files)}")

    # Set translated_html_status to not installed
    state.translated_html_status = TranslatedHTMLStatus.NOT_INSTALLED

    # Update step status
    if 0 <= state.current_step_index < len(state.steps):
        state.steps[state.current_step_index].status = StepStatus.SUCCESS

    return state
