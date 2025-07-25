from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig

from src.llm.llm_client import llm_client
from src.prompts import (
    ASSET_TRANSFER_SYSTEM_PROMPT,
    ASSET_TRANSFER_USER_PROMPT,
)
from src.settings import OUTPUT_DIR, custom_logger
from src.structs.status import StepStatus
from src.utils import (
    extract_layout_properties_async,
    get_html_files,
    get_message,
    get_relative_path,
    read_html_file,
    write_html_file,
)
from src.workflows.state import ADTState

# Initialize logger
logger = custom_logger("Asset Transfer Agent")


# Actions
async def asset_transfer(state: ADTState, config: RunnableConfig) -> ADTState:
    """Asset transfer properties to target HTML files based on a template HTML.

    Args:
        state: The current state of the workflow
        config: The configuration for the workflow

    Returns:
        The updated state of the workflow
    """
    # Create prompt
    messages = ChatPromptTemplate.from_messages(
        [
            ("system", ASSET_TRANSFER_SYSTEM_PROMPT),
            ("user", ASSET_TRANSFER_USER_PROMPT),
        ]
    )

    # Define current state step
    current_step = state.steps[state.current_step_index]

    # Get the relevant html files
    filtered_files = current_step.html_files

    # Get all HTML files from output directory
    html_files = await get_html_files(OUTPUT_DIR)

    # Get the base HTML (template) files
    html_templates = []
    for html_template in current_step.layout_template_files:
        rel_path = await get_relative_path(html_template, "data")
        html_template = await read_html_file(html_template)
        html_templates.append(html_template)

    # Filter relevant HTML to be changed
    html_files = [
        html_file
        for html_file in html_files
        if (html_file in filtered_files and html_file not in html_templates)
    ]

    # Process each relevant HTML file
    modified_files = []
    for html_file in html_files:

        # Read the file content
        rel_path = await get_relative_path(html_file, "data")
        html_content = await read_html_file(html_file)
        html_content, _ = await extract_layout_properties_async(html_content)

        # Format messages
        formatted_messages = await messages.ainvoke(
            {
                "source_html_file": html_templates,
                "target_html_file": html_content,
                "asset_instructions": state.messages[-1].content,
            },
            config,
        )

        # Call model
        response = await llm_client.ainvoke(formatted_messages, config)

        # Get edited asset from response
        edited_html = str(response.content)

        # Save edited text back to the same file
        await write_html_file(html_file, edited_html)

        # Save file path to modified files
        modified_files.append(rel_path)

    # Add message about the file being processed
    message = f"The following files have been processed and updated based on the instruction: '{current_step.step}'\n"
    for file in modified_files:
        message += f"- {file}\n"
    state.add_message(SystemMessage(content=message))
    state.add_message(
        AIMessage(
            content=get_message(state.user_language.value, "final_response")
        )
    )
    logger.info(f"Total files modified: {len(modified_files)}")

    # Update step status
    if 0 <= state.current_step_index < len(state.steps):
        state.steps[state.current_step_index].status = StepStatus.SUCCESS

    return state
