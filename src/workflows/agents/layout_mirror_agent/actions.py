from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig

from src.llm.llm_client import llm_client
from src.prompts import (
    LAYOUT_MIRRORING_SYSTEM_PROMPT,
    LAYOUT_MIRRORING_USER_PROMPT,
)
from src.settings import custom_logger, OUTPUT_DIR
from src.structs.status import StepStatus
from src.workflows.state import ADTState
from src.utils import (
    get_relative_path,
    get_html_files,
    read_html_file,
    write_html_file,
    load_translated_html_contents,
    extract_layout_properties_async, 
)


# Initialize logger
logger = custom_logger("Layout Mirroring Agent")


# Actions
async def mirror_layout(state: ADTState, config: RunnableConfig) -> ADTState:
    """
    Mirror layout properties to target HTML files based on a template HTML.

    Args:
        state: The current state of the workflow
        config: The configuration for the workflow

    Returns:
        The updated state of the workflow
    """

    # Create prompt
    messages = ChatPromptTemplate.from_messages(
        [
            ("system", LAYOUT_MIRRORING_SYSTEM_PROMPT),
            ("user", LAYOUT_MIRRORING_USER_PROMPT),
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
                "layout_template": html_templates,
                "target_html_file": html_content,
                "instruction": state.messages[-1].content,
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

    # Add message about the file being processed
    message = f"The following files have been processed and updated based on the instruction: '{current_step.step}'\n"
    for file in modified_files:
        message += f"- {file}\n"
    state.add_message(SystemMessage(content=message))
    state.add_message(
        AIMessage(
            content="The files had been mirrored and updated based on your request. Please check the files and make sure they are correct."
        )
    )
    logger.info(f"Total files modified: {len(modified_files)}")

    # Update step status
    if 0 <= state.current_step_index < len(state.steps):
        state.steps[state.current_step_index].status = StepStatus.SUCCESS

    return state
