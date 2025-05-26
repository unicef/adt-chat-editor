import os
import aiofiles
import asyncio
from pathlib import Path
from typing import List

from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig

from src.llm.llm_client import llm_client
from src.settings import custom_logger
from src.prompts import (
    LAYOUT_EDIT_SYSTEM_PROMPT,
    LAYOUT_EDIT_USER_PROMPT,
    LAYOUT_COMPARISON_SYSTEM_PROMPT,
    LAYOUT_COMPARISON_USER_PROMPT,
)
from src.structs.status import StepStatus
from src.workflows.state import ADTState
from src.workflows.utils import (
    get_relative_path,
    get_html_files,
    read_html_file,
    write_html_file,
    extract_layout_properties_async,
)

logger = custom_logger("Layout Edit Agent")


async def edit_layout(state: ADTState, config: RunnableConfig) -> ADTState:
    """Edit layout based on the instruction while preserving HTML semantics and structure."""

    # Define current state step
    current_step = state.steps[state.current_step_index]
    
    # Get all HTML files from output directory
    output_dir = "data/output"
    html_files = await get_html_files(output_dir)

    # Get the relevant and layout-base-template html files 
    filteres_files = current_step.html_files
    layout_template_files = current_step.layout_template_files

    # Filter relevant HTML to be changed
    html_files = [
        html_file for html_file in html_files if (
            html_file in filteres_files and html_file not in layout_template_files
        )
    ]

    # Set comparison variables as empty strings
    layout_comparison_system_prompt = ""
    layout_comparison_user_prompt = ""
    
    # Only if a comparision or changes based on a layout template is required
    if layout_template_files: 

        # Append all base html layout properties (templates) inside the same list
        layout_templates = []
        for layout_template_file in layout_template_files:
            # Get relative path for logging
            rel_path = await get_relative_path(layout_template_file, "data")
            html_content = await read_html_file(layout_template_file)
            html_layout_content = html_content #await extract_layout_properties_async(html_content)
            layout_templates.append(html_layout_content)

        # Define the comparison prompts
        layout_comparison_system_prompt = LAYOUT_COMPARISON_SYSTEM_PROMPT
        layout_comparison_user_prompt = LAYOUT_COMPARISON_USER_PROMPT.format(
            layout_templates=layout_templates
        )

    # Create prompt
    messages = ChatPromptTemplate.from_messages(
        [
            ("system", LAYOUT_EDIT_SYSTEM_PROMPT),
            ("user", LAYOUT_EDIT_USER_PROMPT),
        ]
    )

    # Process each relevant HTML file
    for html_file in html_files:
        # Get relative path for logging
        rel_path = await get_relative_path(html_file, "data")

        # Read the file content using the new async function
        html_content = await read_html_file(html_file)

        # Format messages
        formatted_messages = await messages.ainvoke(
            {
                "text": {
                    "file name" :html_file,
                    "file content": html_content,
                },
                "instruction": state.messages[-1].content,
                "layout_comparison_system_prompt": layout_comparison_system_prompt,
                "layout_comparison_user_prompt": layout_comparison_user_prompt,
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
