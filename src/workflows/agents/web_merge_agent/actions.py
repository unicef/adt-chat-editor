from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig

from src.llm.llm_client import llm_client
from src.prompts import (
    WEB_MERGE_SYSTEM_PROMPT,
    WEB_MERGE_USER_PROMPT,
)
from src.settings import (
    NAV_HTML_DIR,
    OUTPUT_DIR,
    custom_logger,
)
from src.structs.status import StepStatus
from src.workflows.state import ADTState
from src.utils import (
    get_relative_path,
    get_html_files,
    read_html_file,
    write_html_file,
    find_and_duplicate_nav_line,
    write_nav_line,
    load_translated_html_contents,
    extract_layout_properties_async,
    get_message,
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

    # Get all relevant HTML files from output directory
    html_files = await get_html_files(OUTPUT_DIR)
    html_files = [html_file for html_file in html_files if html_file in filtered_files]

    # Process each relevant HTML file to get its content
    html_contents = []
    for html_file in html_files:
        # Get relative path for logging
        rel_path = await get_relative_path(html_file, "data")

        # Read the file content using the new async function
        html_content = await read_html_file(html_file)
        html_content, _ = await extract_layout_properties_async(html_content)

        html_contents.append(html_content)

    # Load translated HTML contents
    translated_html_contents = await load_translated_html_contents(
        language=state.language
    )

    translated_contents = [
        next(
                (
                    item[html_file] for item in translated_html_contents 
                    if item.get(html_file)
                ),
                None
            )
        for html_file in html_files
    ]

    # Format messages
    formatted_messages = await messages.ainvoke(
        {
            "html_inputs": html_contents,
            "translated_texts": translated_contents,
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
    modified_files = [merged_file_name]

    # Save edited text back to the same file
    await write_html_file(merged_file_name, edited_html)

    # Update nav
    nav_html = await read_html_file(OUTPUT_DIR + NAV_HTML_DIR)
    nav_line = await find_and_duplicate_nav_line(
        nav_html, file_names[0] + ".html", joined_name + ".html"
    )
    nav_html = await write_nav_line(nav_html, nav_line)
    await write_html_file(OUTPUT_DIR + NAV_HTML_DIR, nav_html)

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
