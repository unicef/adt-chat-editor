from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig

from src.llm.llm_client import llm_client
from src.settings import custom_logger
from src.prompts import (
    TEXT_EDIT_SYSTEM_PROMPT,
    TEXT_EDIT_USER_PROMPT,
)
from src.structs.status import StepStatus
from src.workflows.state import ADTState
from src.workflows.utils import (
    get_relative_path,
    get_html_files,
    read_html_file,
    write_html_file,
)

logger = custom_logger("Text Edit Agent")


async def edit_text(state: ADTState, config: RunnableConfig) -> ADTState:
    """Edit text based on the instruction while preserving HTML structure."""

    # Create prompt
    messages = ChatPromptTemplate.from_messages(
        [
            ("system", TEXT_EDIT_SYSTEM_PROMPT),
            ("user", TEXT_EDIT_USER_PROMPT),
        ]
    )

    # Get all HTML files from output directory
    output_dir = "data/output"
    html_files = await get_html_files(output_dir)
    filteres_files = [step.html_files for step in state.steps]
    html_files = [
        html_file for html_file in html_files if html_file in filteres_files
    ]

    # Process each file
    for html_file in html_files:
        # Get relative path for logging
        rel_path = await get_relative_path(html_file, "data")

        # Read the file content using the new async function
        html_content = await read_html_file(html_file)

        # Format messages
        formatted_messages = await messages.ainvoke(
            {
                "text": html_content,
                "instruction": state.messages[-1].content,
            },
            config,
        )

        # Call model
        response = await llm_client.ainvoke(formatted_messages, config)

        # Get edited text from response
        edited_text = str(response.content)

        # Save edited text back to the same file
        await write_html_file(html_file, edited_text)

        # Add message about the file being processed
        state.add_message(HumanMessage(content=f"Processed and updated {rel_path}"))

    # Update step status
    if state.current_step_index >= 0 and state.current_step_index < len(state.steps):
        state.steps[state.current_step_index].step_status = StepStatus.SUCCESS

    return state
