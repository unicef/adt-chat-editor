import os
import aiofiles
import asyncio
from pathlib import Path
from typing import List

from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig

from src.llm.llm_client import llm_client
from src.settings import custom_logger, OUTPUT_DIR
from src.prompts import (
    LAYOUT_MIRRORING_SYSTEM_PROMPT,
    LAYOUT_MIRRORING_USER_PROMPT,
)
from src.structs.status import StepStatus
from src.workflows.state import ADTState
from src.workflows.utils import (
    get_relative_path,
    get_html_files,
    read_html_file,
    write_html_file,
)

logger = custom_logger("Layout Mirroring Agent")


async def mirror_layout(state: ADTState, config: RunnableConfig) -> ADTState:
    """Mirror layout propertoies to target TML files based on a template HTML."""

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
    filteres_files = current_step.html_files

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
        html_file for html_file in html_files if (
            html_file in filteres_files and html_file not in html_templates
        )
    ]

    # Process each relevant HTML file
    for html_file in html_files:
        # Get relative path for logging
        rel_path = await get_relative_path(html_file, "data")

        # Read the file content using the new async function
        html_content = await read_html_file(html_file)

        # Format messages
        formatted_messages = await messages.ainvoke(
            {
                "layout_template": html_templates,
                "text": html_content,
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

        state.add_message(HumanMessage(content=f"Processed and updated layout for {rel_path}"))

    # Update step status
    if 0 <= state.current_step_index < len(state.steps):
        state.steps[state.current_step_index].step_status = StepStatus.SUCCESS

    return state
