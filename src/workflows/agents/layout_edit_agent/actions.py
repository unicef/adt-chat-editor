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
)
from src.structs.status import StepStatus
from src.workflows.state import ADTState

logger = custom_logger("Layout Edit Agent")


async def get_html_files(output_dir: str) -> List[str]:
    """Get all HTML files from the output directory asynchronously."""
    output_path = Path(output_dir)
    files = await asyncio.to_thread(lambda: list(output_path.glob("*.html")))
    return [str(f) for f in files]


async def get_relative_path(path: str, start: str) -> str:
    """Get relative path asynchronously."""
    return await asyncio.to_thread(os.path.relpath, path, start)


async def edit_layout(state: ADTState, config: RunnableConfig) -> ADTState:
    """Edit layout based on the instruction while preserving HTML semantics and structure."""

    # Create prompt
    messages = ChatPromptTemplate.from_messages(
        [
            ("system", LAYOUT_EDIT_SYSTEM_PROMPT),
            ("user", LAYOUT_EDIT_USER_PROMPT),
        ]
    )

    # Get all HTML files from output directory
    output_dir = "data/output"
    html_files = await get_html_files(output_dir)

    # Process each file
    for html_file in html_files:
        rel_path = await get_relative_path(html_file, "data")

        async with aiofiles.open(html_file, "r", encoding="utf-8") as f:
            html_content = await f.read()

        formatted_messages = await messages.ainvoke(
            {
                "text": html_content,
                "instruction": state.messages[-1].content,
            },
            config,
        )

        response = await llm_client.ainvoke(formatted_messages, config)
        edited_html = str(response.content)

        async with aiofiles.open(html_file, "w", encoding="utf-8") as f:
            await f.write(edited_html)

        state.add_message(HumanMessage(content=f"Processed and updated layout for {rel_path}"))

    # Update step status
    if 0 <= state.current_step_index < len(state.steps):
        state.steps[state.current_step_index].step_status = StepStatus.SUCCESS

    return state
