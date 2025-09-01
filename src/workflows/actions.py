import textwrap
from typing import Any

from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig

from src.llm.llm_call import async_model_call
from src.llm.llm_client import llm_client
from src.prompts import (
    ORCHESTRATOR_PLANNING_PROMPT,
    ORCHESTRATOR_SYSTEM_PROMPT,
)
from src.settings import (
    OUTPUT_DIR,
    custom_logger,
)
from src.structs import (
    OrchestratorPlanningOutput,
    PlanningStep,
    StepStatus,
    TailwindStatus,
    TranslatedHTMLStatus,
    WorkflowStatus,
)
from src.utils import (
    get_language_name,
    get_message,
    load_translated_html_contents,
    parse_html_pages,
)
from src.workflows.agents import AVAILABLE_AGENTS
from src.workflows.state import ADTState
from src.core.git_manager_provider import get_git_manager  # reuse lazy git manager

# Initialize logger
logger = custom_logger("Main Workflow Actions")


# Response parsers
orchestrator_planning_parser = PydanticOutputParser(
    pydantic_object=OrchestratorPlanningOutput
)


# Note: Git operations are handled elsewhere (publish routes). Avoid creating
# a Git manager here to prevent event-loop issues during import in tests.


# Actions
async def plan_steps(state: ADTState, config: RunnableConfig) -> ADTState:
    """Plan the steps for the report.

    Args:
        state: The state of the agent.
        config: The configuration of the agent.

    Returns:
        The state of the agent.
    """
    logger.info("Planning steps")

    # Initialize languages
    if not state.available_languages:
        await state.initialize_languages()

    # Initialize tailwind
    if state.tailwind_status != TailwindStatus.INSTALLED:
        await state.initialize_tailwind()

    # Initialize translated HTML contents
    if state.translated_html_status != TranslatedHTMLStatus.INSTALLED:
        await state.initialize_translated_html_content(state.available_languages)

    # Initialize the flags
    state.is_irrelevant_query = False
    state.is_forbidden_query = False

    # Set user query
    state.user_query = str(state.messages[-1].content)

    # Get previous conversation
    previous_conversation = "\n".join(
        f"- {message.type}: {message.content}" for message in state.messages
    )

    # Manage completed steps on previous iteration
    state.completed_steps.extend(state.steps)
    state.steps = []
    state.current_step_index = -1

    completed_steps = "\n".join(
        f"- {step.step}"
        for step in state.completed_steps
        if step.status == StepStatus.SUCCESS
    )

    # Load translated HTML contents
    available_html_files = await load_translated_html_contents(language=state.language)
    if state.current_pages:
        logger.info("Filtering selected page")
        current_pages = [
            f"{OUTPUT_DIR}/{current_page}" for current_page in state.current_pages
        ]
        available_html_files = {
            path: " ".join(val for item in content_list for val in item.values())
            for entry in available_html_files
            for path, content_list in entry.items()
            if path in current_pages
        }
        is_current_page = True
        logger.info(f"The selected page is: {available_html_files.keys()}")
    else:
        available_html_files = {
            path: " ".join(val for item in content_list for val in item.values())
            for entry in available_html_files
            for path, content_list in entry.items()
        }
        is_current_page = False

    # Get all relevant HTML files map to pages
    html_files = list(available_html_files.keys())
    html_page_map = await parse_html_pages(html_files)

    # Format messages
    messages = ChatPromptTemplate(
        messages=[
            ("system", ORCHESTRATOR_SYSTEM_PROMPT),
            ("user", ORCHESTRATOR_PLANNING_PROMPT),
        ]
    )

    formatted_messages = await messages.ainvoke(
        {
            "user_query": state.user_query,
            "available_agents": [
                f"{agent['name']}: {agent['description']}" for agent in AVAILABLE_AGENTS
            ],
            "available_html_files": available_html_files,
            "html_page_map": html_page_map,
            "is_current_page": is_current_page,
            "previous_conversation": previous_conversation,
            "user_feedback": "",  # Empty string for initial planning
            "user_language": get_language_name(state.user_language.value),
            "completed_steps": completed_steps,
        },
        config,
    )

    # Model call
    retries = 0
    while retries < 3:
        response = await async_model_call(
            llm_client=llm_client,
            config=config,
            formatted_prompt=formatted_messages,
        )
        retries += 1

        # Parse the response
        content = (
            response.content
            if isinstance(response.content, str)
            else str(response.content)
        )
        parsed_response = orchestrator_planning_parser.parse(content)

        if (
            parsed_response.is_irrelevant
            or parsed_response.is_forbidden
            or parsed_response.steps
        ):
            break

        logger.info(f"No steps found in the response. Retrying... ({retries}/3)")

    logger.info(f"Orchestrator planning output: {parsed_response}")

    # Check for invalid queries
    if parsed_response.is_irrelevant:
        state.is_irrelevant_query = True
        logger.info("Query marked as irrelevant")

    if parsed_response.is_forbidden:
        state.is_forbidden_query = True
        logger.info("Query marked as forbidden")

    # Create steps
    for step in parsed_response.steps:
        state.steps.append(
            PlanningStep(
                step=step.step,
                non_technical_description=step.non_technical_description,
                agent=step.agent,
                html_files=step.html_files,
                layout_template_files=step.layout_template_files,
            )
        )

    # Add the rephrase query message if no steps were found
    if not state.steps:
        rephrase_query_display = textwrap.dedent(
            get_message(state.user_language.value, "rephrase_query")
        )
        if not parsed_response.is_irrelevant and not parsed_response.is_forbidden:
            state.add_message(SystemMessage(content=rephrase_query_display))

    return state


async def rephrase_query(state: ADTState, config: RunnableConfig) -> dict[str, Any]:
    """Ask the user to rephrase the query to make it more specific and clear.

    Args:
        state: The state of the agent.
        config: The configuration of the agent.
    """
    logger.info("Asking the user to rephrase the query")

    # Format the plan for display
    rephrase_query_display = textwrap.dedent(
        get_message(state.user_language.value, "rephrase_query")
    )

    # Update the state
    state.add_message(AIMessage(content=rephrase_query_display))

    return {"messages": [AIMessage(content=rephrase_query_display)]}


def create_plan_display(state: ADTState) -> str:
    """Create the plan display.

    Args:
        state: The state of the agent.
    """
    # Escape underscores in step descriptions to prevent markdown formatting issues
    steps_description = []
    for i, step in enumerate(state.steps, 1):
        # Escape underscores in the non_technical_description to prevent markdown italics
        escaped_description = step.non_technical_description.replace("_", "\\_")
        steps_description.append(f"{i}. {escaped_description}")

    steps_description_str = "\n".join(steps_description)

    plan_display = get_message(state.user_language.value, "plan_display")
    plan_display = plan_display.format(steps=steps_description_str)

    return plan_display


async def show_plan_to_user(state: ADTState, config: RunnableConfig) -> dict[str, Any]:
    """Show the planned steps to the user and allow for adjustments.

    Args:
        state: The state of the agent.
        config: The configuration of the agent.

    Returns:
        The state of the agent.
    """
    logger.info("Showing plan to user")

    # Format the plan for display
    plan_display = create_plan_display(state).replace(f"{OUTPUT_DIR}/", "")
    logger.info(f"Plan display: {plan_display}")

    return {"messages": [AIMessage(content=plan_display)], "plan_shown_to_user": True}


async def handle_plan_response(state: ADTState, config: RunnableConfig) -> ADTState:
    """Handle the user's response to the plan and make adjustments if needed.

    Args:
        state: The state of the agent.
        config: The configuration of the agent.

    Returns:
        The state of the agent.
    """
    logger.info("Handling user's plan response")

    # Get the last message from the user
    last_message = str(state.messages[-1].content)

    # Get previous conversation
    previous_conversation = "\n".join(
        f"- {message.type}: {message.content}" for message in state.messages
    )

    completed_steps = "\n".join(
        f"- {step.step}"
        for step in state.completed_steps
        if step.status == StepStatus.SUCCESS
    )

    # Load translated HTML contents
    available_html_files = await load_translated_html_contents(language=state.language)
    if state.current_pages:
        logger.info("Filtering selected page")
        current_pages = [
            f"{OUTPUT_DIR}/{current_page}" for current_page in state.current_pages
        ]
        available_html_files = {
            path: " ".join(val for item in content_list for val in item.values())
            for entry in available_html_files
            for path, content_list in entry.items()
            if path in current_pages
        }
        is_current_page = True
        logger.info(f"The selected page is: {available_html_files.keys()}")
    else:
        available_html_files = {
            path: " ".join(val for item in content_list for val in item.values())
            for entry in available_html_files
            for path, content_list in entry.items()
        }
        is_current_page = False

    # Get all relevant HTML files map to pages
    html_files = list(available_html_files.keys())
    html_page_map = await parse_html_pages(html_files)

    # Format messages
    messages = ChatPromptTemplate(
        messages=[
            ("system", ORCHESTRATOR_SYSTEM_PROMPT),
            ("user", ORCHESTRATOR_PLANNING_PROMPT),
        ]
    )

    formatted_messages = await messages.ainvoke(
        {
            "user_query": last_message,
            "available_agents": [
                f"{agent['name']}: {agent['description']}" for agent in AVAILABLE_AGENTS
            ],
            "available_html_files": available_html_files,
            "html_page_map": html_page_map,
            "is_current_page": is_current_page,
            "previous_conversation": previous_conversation,
            "user_feedback": last_message,
            "user_language": get_language_name(state.user_language.value),
            "completed_steps": completed_steps,
        },
        config,
    )

    # Model call
    response = await async_model_call(
        llm_client=llm_client,
        config=config,
        formatted_prompt=formatted_messages,
    )

    # Parse the response
    content = (
        response.content if isinstance(response.content, str) else str(response.content)
    )
    parsed_response = orchestrator_planning_parser.parse(content)
    logger.info(f"Re-planning response: {parsed_response}")

    # Check if the plan was accepted
    state.plan_accepted = not parsed_response.modified

    # Change the new steps if needed
    if parsed_response.modified:
        state.steps = parsed_response.steps

    return state


async def execute_next_step(state: ADTState, config: RunnableConfig) -> ADTState:
    """Execute the next step in the plan.

    Args:
        state: The state of the agent.
        config: The configuration of the agent.

    Returns:
        The state of the agent.
    """
    logger.info("Executing current step")
    logger.debug(f"State at execute_next_step: {state}")

    # Increment the step index
    state.current_step_index += 1

    # If we've processed all steps, we're done
    if state.current_step_index >= len(state.steps):
        logger.info("All steps completed")
        return state

    # Get the current step
    current_step = state.steps[state.current_step_index]
    logger.info(
        f"Processing step {state.current_step_index}: The '{current_step.agent}' will '{current_step.step}'"
    )

    return state


async def add_non_valid_message(
    state: ADTState, config: RunnableConfig
) -> dict[str, list[AIMessage]]:
    """Add a non-valid message to the state.

    Args:
        state: The state of the agent.
        config: The configuration of the agent.

    Returns:
        A dictionary with the key "messages" and the value being a list of AIMessage objects.
    """
    if state.is_forbidden_query:
        non_valid_message = textwrap.dedent(
            get_message(state.user_language.value, "forbidden_query")
        )
    elif state.is_irrelevant_query:
        non_valid_message = textwrap.dedent(
            get_message(state.user_language.value, "irrelevant_query")
        )
    else:
        raise ValueError(
            f"The query was not found as forbidden or irrelevant. Query: {state.user_query}"
        )

    state.add_message(AIMessage(content=non_valid_message))

    return {"messages": [AIMessage(content=non_valid_message)]}


async def finalize_task_execution(state: ADTState, config: RunnableConfig) -> ADTState:
    """Finalize the task execution.

    Args:
        state: The state of the agent.
        config: The configuration of the agent.
    """
    logger.info("Finalizing task execution")

    # Save the state
    state.plan_shown_to_user = False
    state.status = WorkflowStatus.SUCCESS

    git_manager = get_git_manager()
    if git_manager is None:
        logger.debug("Git manager unavailable; skipping commit and checkout steps")
        return state

    try:
        message = "New Change Saved"
        committed = await git_manager.commit_changes(message=message)
        if committed:
            logger.debug(f"Committed changes with message: {message}")
        else:
            logger.debug("No changes to commit")
    except Exception as e:
        logger.error(f"Error committing changes: {e}")

    commits = []
    try:
        current_branch = await git_manager.current_branch()
        commits = await git_manager.list_commits(branch_name=current_branch)
        logger.debug(f"Commits retrieved successfully: {commits}")
    except Exception as e:
        logger.debug(f"Error fetching commits: {e}")

    try:
        if commits:
            commit_hash = commits[-1].get("hash")
            await git_manager.checkout_commit(commit_hash)
            logger.debug(f"Checkout commit successfully: {commit_hash}")
    except Exception as e:
        logger.debug(f"Error checking out commit: {e}")

    return state
