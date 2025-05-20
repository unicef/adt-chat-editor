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
    TEXT_EDIT_SYSTEM_PROMPT,
    TEXT_EDIT_USER_PROMPT,
)
from src.structs.status import StepStatus
from src.workflows.state import ADTState


logger = custom_logger("Text Edit Agent")


async def get_html_files(output_dir: str) -> List[str]:
    """Get all HTML files from the output directory asynchronously."""
    output_path = Path(output_dir)
    # Use asyncio.to_thread to run the blocking glob operation in a thread pool
    files = await asyncio.to_thread(lambda: list(output_path.glob("*.html")))
    return [str(f) for f in files]


async def get_relative_path(path: str, start: str) -> str:
    """Get relative path asynchronously."""
    return await asyncio.to_thread(os.path.relpath, path, start)


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

    # Process each file
    for html_file in html_files:
        # Get relative path for logging
        rel_path = await get_relative_path(html_file, "data")

        # Read the file content
        async with aiofiles.open(html_file, "r", encoding="utf-8") as f:
            html_content = await f.read()

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
        async with aiofiles.open(html_file, "w", encoding="utf-8") as f:
            await f.write(edited_text)

        # Add message about the file being processed
        state.add_message(HumanMessage(content=f"Processed and updated {rel_path}"))

    # Update step status
    if state.current_step_index >= 0 and state.current_step_index < len(state.steps):
        state.steps[state.current_step_index].step_status = StepStatus.SUCCESS

    return state
