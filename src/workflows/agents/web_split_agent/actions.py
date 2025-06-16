import ast
import json

from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig

from src.llm.llm_client import llm_client
from src.prompts import (
    WEB_SPLIT_SYSTEM_PROMPT,
    WEB_SPLIT_USER_PROMPT,
)
from src.settings import (
    NAV_HTML_DIR,
    OUTPUT_DIR,
    custom_logger,
)
from src.structs import StepStatus, SplitEditResponse
from src.utils import (
    get_html_files,
    read_html_file,
    write_html_file,
    find_and_duplicate_nav_line,
    write_nav_line,
    load_translated_html_contents,
    extract_layout_properties_async,
)
from src.workflows.state import ADTState

logger = custom_logger("Web Split Agent")

# Output parser
split_edits_parser = PydanticOutputParser(pydantic_object=SplitEditResponse)


async def web_split(state: ADTState, config: RunnableConfig) -> ADTState:
    """Split one HTML file into several and update nav accordingly."""
    current_step = state.steps[state.current_step_index]
    html_files = await get_html_files(OUTPUT_DIR)
    html_files = [f for f in html_files if f in current_step.html_files]
    html_file = html_files[-1]

    html_content = await read_html_file(html_file)
    html_content, _ = await extract_layout_properties_async(html_content)
    file_base = html_file.split("/")[-1].replace(".html", "")

    # Load translated HTML contents
    translated_html_contents = await load_translated_html_contents(
        language=state.language
    )

    translated_contents = next(
        (
            item[html_file] for item in translated_html_contents 
            if item.get(html_file)
        ),
        None
    )

    # Step 1: Split HTML
    split_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", WEB_SPLIT_SYSTEM_PROMPT),
            ("user", WEB_SPLIT_USER_PROMPT),
        ]
    )
    split_input = {
        "html_input": html_content,
        "translated_texts": translated_contents,
        "instruction": state.messages[-1].content,
    }
    formatted_split_prompt = await split_prompt.ainvoke(split_input, config)
    split_response = await llm_client.ainvoke(formatted_split_prompt, config)

    # Parse the response
    split_response = split_edits_parser.parse(str(split_response.content))
    split_response = split_response.split_edits

    # Step 2: Initialize nav
    nav_html = await read_html_file(OUTPUT_DIR + NAV_HTML_DIR)

    # Step 3: Write each split file and update nav
    splitted_file_paths = []
    for idx, response in enumerate(split_response):
        html = response.split_html_file
        file_name = f"{file_base}_split_{idx + 1}.html"
        splitted_file_paths.append(file_name)
        full_path = f"{OUTPUT_DIR}/{file_name}"
        await write_html_file(full_path, html)

        # Update nav
        nav_line = await find_and_duplicate_nav_line(
            nav_html, f"{file_base}.html", file_name
        )
        nav_html = await write_nav_line(nav_html, nav_line)

    await write_html_file(OUTPUT_DIR + NAV_HTML_DIR, nav_html)

    # Log and state update
    summary_message = (
        f"Split '{html_file}' into {len(split_response)} files:\n"
        + "\n".join(f"- {name}" for name in splitted_file_paths)
        + "\nUpdated nav.html for each new file."
    )
    state.add_message(SystemMessage(content=summary_message))
    state.add_message(
        AIMessage(
            content="The files had been split and updated based on your request. Please check the files and make sure they are correct."
        )
    )
    logger.info(summary_message)

    if 0 <= state.current_step_index < len(state.steps):
        state.steps[state.current_step_index].status = StepStatus.SUCCESS

    return state
