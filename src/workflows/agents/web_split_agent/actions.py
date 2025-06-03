import ast
import json

from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig

from src.llm.llm_client import llm_client
from src.prompts import (
    NAV_UPDATE_SYSTEM_PROMPT,
    NAV_UPDATE_USER_PROMPT,
    WEB_SPLIT_SYSTEM_PROMPT,
    WEB_SPLIT_USER_PROMPT,
)
from src.settings import (
    INTERFACE_HTML_DIR,
    NAV_HTML_DIR,
    OUTPUT_DIR,
    custom_logger,
)
from src.structs.status import StepStatus
from src.utils import (
    get_html_files,
    read_html_file,
    write_html_file,
)
from src.workflows.state import ADTState

logger = custom_logger("Web Split Agent")


async def web_split(state: ADTState, config: RunnableConfig) -> ADTState:
    """Split one HTML file into several and update nav/interface accordingly."""
    current_step = state.steps[state.current_step_index]
    html_files = await get_html_files(OUTPUT_DIR)
    html_files = [f for f in html_files if f in current_step.html_files]
    html_file = html_files[-1]

    html_content = await read_html_file(html_file)
    file_base = html_file.split("/")[-1].replace(".html", "")

    # Step 1: Split HTML
    split_prompt = ChatPromptTemplate.from_messages([
        ("system", WEB_SPLIT_SYSTEM_PROMPT),
        ("user", WEB_SPLIT_USER_PROMPT),
    ])
    split_input = {
        "html_input": html_content,
        "instruction": state.messages[-1].content,
    }
    formatted_split_prompt = await split_prompt.ainvoke(split_input, config)
    split_response = await llm_client.ainvoke(formatted_split_prompt, config)

    split_htmls = ast.literal_eval(split_response.content) 
    splitted_file_paths = []

    # Step 2: Initialize nav/interface
    nav_html = await read_html_file(OUTPUT_DIR + NAV_HTML_DIR)
    interface_html = await read_html_file(OUTPUT_DIR + INTERFACE_HTML_DIR)

    # Step 3: Write each split file and update nav/interface
    for idx, html in enumerate(split_htmls):
        file_name = f"{file_base}_split_{idx + 1}.html"
        full_path = f"{OUTPUT_DIR}/{file_name}"
        await write_html_file(full_path, html)
        splitted_file_paths.append(file_name)

        # Call nav/interface update for this file
        nav_prompt = ChatPromptTemplate.from_messages([
            ("system", NAV_UPDATE_SYSTEM_PROMPT),
            ("user", NAV_UPDATE_USER_PROMPT),
        ])
        nav_input = {
            "split_html_name": file_name,
            "split_html_content": html,
            "nav_html": nav_html,
            "interface_html": interface_html,
        }
        formatted_nav_prompt = await nav_prompt.ainvoke(nav_input, config)
        nav_response = await llm_client.ainvoke(formatted_nav_prompt, config)

        try:
            nav_update = json.loads(nav_response.content)
            nav_html = nav_update["updated_nav"]
            interface_html = nav_update["updated_interface"]
        except json.JSONDecodeError as e:
            print("⚠️ JSON decode error:", e)
            print("Response was:", nav_response)

    # Step 4: Save final nav/interface versions
    await write_html_file(OUTPUT_DIR + NAV_HTML_DIR, nav_html)
    await write_html_file(OUTPUT_DIR + INTERFACE_HTML_DIR, interface_html)

    # Log and state update
    summary_message = (
        f"Split '{html_file}' into {len(split_htmls)} files:\n"
        + "\n".join(f"- {name}" for name in splitted_file_paths)
        + "\nUpdated nav.html and interface.html for each new file."
    )
    state.add_message(AIMessage(content=summary_message))
    logger.info(summary_message)

    if 0 <= state.current_step_index < len(state.steps):
        state.steps[state.current_step_index].status = StepStatus.SUCCESS

    return state
