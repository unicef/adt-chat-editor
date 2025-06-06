import json
import os
import textwrap
from dataclasses import asdict

from langchain_core.messages import AIMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langgraph.types import interrupt

from src.llm.llm_call import async_model_call
from src.llm.llm_client import llm_client
from src.prompts import (
    ORCHESTRATOR_PLANNING_PROMPT,
    ORCHESTRATOR_SYSTEM_PROMPT,
)
from src.settings import custom_logger, STATE_CHECKPOINTS_DIR, OUTPUT_DIR
from src.structs import OrchestratorPlanningOutput, PlanningStep, StepStatus
from src.workflows.agents import AVAILABLE_AGENTS
from src.workflows.state import ADTState
from src.utils import (
    get_html_files,
    read_html_file,
    extract_html_content_async,
)


# Initialize logger
logger = custom_logger("Main Workflow Actions")


# Response parsers
orchestrator_planning_parser = PydanticOutputParser(
    pydantic_object=OrchestratorPlanningOutput
)


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

    # Initialize the flags
    state.is_irrelevant_query = False
    state.is_forbidden_query = False

    # Initialize languages
    await state.initialize_languages()

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

    # Define available HTML files
    html_files = await get_html_files(OUTPUT_DIR)
    available_html_files = [
        {
            "html_name": html_file,
            "html_content": await extract_html_content_async(
                await read_html_file(html_file)
            ),
        }
        for html_file in html_files
    ]

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
            "previous_conversation": previous_conversation,
            "user_feedback": "",  # Empty string for initial planning
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

    # Add the plan display to the messages
    state.add_message(AIMessage(content=create_plan_display(state)))

    # Add the rephrase query message if no steps were found
    if not state.steps:
        rephrase_query_display = textwrap.dedent(
            """
            The system did not detect any actionable steps to solve the task.
            Please, rephrase the query to make it more specific and clear.
            """
        )
        state.add_message(AIMessage(content=rephrase_query_display))

    return state


async def rephrase_query(state: ADTState, config: RunnableConfig) -> ADTState:
    """
    Ask the user to rephrase the query to make it more specific and clear.

    Args:
        state: The state of the agent.
        config: The configuration of the agent.
    """
    logger.info("Asking the user to rephrase the query")

    # Format the plan for display
    rephrase_query_display = textwrap.dedent(
        """
        The system did not detect any actionable steps to solve the task.
        Please, rephrase the query to make it more specific and clear.
        """
    )

    # Use interrupt to get user input
    user_response = interrupt(
        {
            "type": "rephrase_query",
            "content": rephrase_query_display,
        }
    )

    return state


def create_plan_display(state: ADTState) -> str:
    """Create the plan display.

    Args:
        state: The state of the agent.
    """
    plan_display = "Here are the planned steps:\n\n"
    for i, step in enumerate(state.steps, 1):
        plan_display += f"{i}. {step.non_technical_description}\n"

    plan_display += "\nWould you like to proceed with this plan?"
    return plan_display


async def show_plan_to_user(state: ADTState, config: RunnableConfig) -> ADTState:
    """Show the planned steps to the user and allow for adjustments.

    Args:
        state: The state of the agent.
        config: The configuration of the agent.

    Returns:
        The state of the agent.
    """
    logger.info("Showing plan to user")

    # Format the plan for display
    plan_display = create_plan_display(state)
    logger.info(f"Plan display: {plan_display}")

    # Use interrupt to get user input
    user_response = interrupt(
        {
            "type": "plan_review",
            "content": plan_display,
        }
    )

    return state


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

    # Define available HTML files
    html_files = await get_html_files(OUTPUT_DIR)
    available_html_files = [
        {
            "html_name": html_file,
            "html_content": await extract_html_content_async(html_file),
        }
        for html_file in html_files
    ]

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
            "previous_conversation": previous_conversation,
            "user_feedback": last_message,
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
        state.add_message(AIMessage(content=create_plan_display(state)))

    return state


async def execute_step(state: ADTState, config: RunnableConfig) -> ADTState:
    """Execute the current step in the plan.

    Args:
        state: The state of the agent.
        config: The configuration of the agent.

    Returns:
        The state of the agent.
    """
    logger.info("Executing current step")

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
    """
    Add a non-valid message to the state.

    Args:
        state: The state of the agent.
        config: The configuration of the agent.

    Returns:
        A dictionary with the key "messages" and the value being a list of AIMessage objects.
    """

    if state.is_forbidden_query:
        non_valid_message = textwrap.dedent(
            """
            The message sent was found as not allowed to be processed.
            Please, rephrase the query to make it more specific and clear and alligned with the user guidelines.
            """
        )
    elif state.is_irrelevant_query:
        non_valid_message = textwrap.dedent(
            """
            The message sent was not found relevant to the user guidelines.
            This system is intended to be used to help the reviewers to modify Accessible Digital Textbooks.

            Please, rephrase the query to make it more specific and clear and alligned with the user guidelines.
            """
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

    state_checkpoint = json.dumps(asdict(state))
    state_checkpoint_path = os.path.join(
        STATE_CHECKPOINTS_DIR, f"checkpoint-{state.session_id}.json"
    )
    with open(state_checkpoint_path, "w") as f:
        f.write(state_checkpoint)

    return state
