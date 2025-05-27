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
    WEB_MERGE_SYSTEM_PROMPT,
    WEB_MERGE_USER_PROMPT,
)
from src.structs.status import StepStatus
from src.workflows.state import ADTState
from src.workflows.utils import (
    get_relative_path,
    get_html_files,
    read_html_file,
    write_html_file,
)

logger = custom_logger("Web Merge Agent")


async def web_merge(state: ADTState, config: RunnableConfig) -> ADTState:
    """Merge two or more webs based on the instruction while preserving HTML semantics and structure."""

    # Create prompt
    messages = ChatPromptTemplate.from_messages(
        [
            ("system", WEB_MERGE_SYSTEM_PROMPT),
            ("user", WEB_MERGE_USER_PROMPT),
        ]
    )

    # Define current state step
    current_step = state.steps[state.current_step_index]

    # Get the relevant and layout-base-template html files 
    filtered_files = current_step.html_files

    # Get all HTML files from output directory
    html_files = await get_html_files(OUTPUT_DIR)

    # Filter relevant HTML to be changed
    html_files = [
        html_file for html_file in html_files if html_file in filtered_files
    ]

    # Process each relevant HTML file to get its content
    html_contents = []
    for html_file in html_files:
        # Get relative path for logging
        rel_path = await get_relative_path(html_file, "data")

        # Read the file content using the new async function
        html_content = await read_html_file(html_file)

        html_contents.append(html_content)

    # Format messages
    formatted_messages = await messages.ainvoke(
        {
            "html_inputs": html_contents,
            "instruction": state.messages[-1].content,
        },
        config,
    )

    # Call model
    response = await llm_client.ainvoke(formatted_messages, config)

    # Get edited layout from response
    edited_html = str(response.content)

    # Extract just the base names without path or extension
    file_names = [f.split("/")[-1].replace(".html", "") for f in html_files]
    joined_name = "_".join(file_names)
    merged_file_name = OUTPUT_DIR + "/" + joined_name + ".html"
    
    # Save edited text back to the same file
    await write_html_file(merged_file_name, edited_html)

    state.add_message(HumanMessage(content=f"Processed and updated layout for {rel_path}"))

    # Update step status
    if 0 <= state.current_step_index < len(state.steps):
        state.steps[state.current_step_index].step_status = StepStatus.SUCCESS

    return state
