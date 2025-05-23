from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langgraph.types import interrupt

from src.llm.llm_client import llm_client
from src.llm.llm_call import async_model_call
from src.prompts import (
    ORCHESTRATOR_PLANNING_PROMPT,
    ORCHESTRATOR_SYSTEM_PROMPT,
)
from src.settings import custom_logger
from src.structs import OrchestratorPlanningOutput, PlanningStep
from src.structs.status import WorkflowStatus
from src.workflows.state import ADTState

logger = custom_logger("Main Workflow Actions")


# Initialize LLM client
logger.info(f"LLM client initialized: {llm_client}")

# Response parser
orchestrator_planning_parser = PydanticOutputParser(
    pydantic_object=OrchestratorPlanningOutput
)

# Define available agents
available_agents = [
    {
        "name": "Text Edit Agent",
        "description": "Edit the text of the pages",
        "graph": None,
    },
    {
        "name": "Image Edit Agent",
        "description": "Edit the images of the pages",
        "graph": None,
    },
]


async def plan_steps(state: ADTState, config: RunnableConfig) -> ADTState:
    """
    Plan the steps for the report.

    Args:
        state: The state of the agent.
        config: The configuration of the agent.

    Returns:
        The state of the agent.
    """

    logger.info("Planning steps")
    logger.info(f"Initial state: {state}")

    # Initialize the flags
    state.is_irrelevant_query = False
    state.is_forbidden_query = False

    # Set user query
    state.user_query = str(state.messages[-1].content)

    # Get previous conversation
    previous_conversation = "\n".join(
        f"- {message.type}: {message.content}" for message in state.messages
    )

    # Format messages
    messages = ChatPromptTemplate(
        messages=[
            ("system", ORCHESTRATOR_SYSTEM_PROMPT),
            ("user", ORCHESTRATOR_PLANNING_PROMPT),
        ]
    )

    # Format messages
    formatted_messages = await messages.ainvoke(
        {
            "user_query": state.user_query,
            "available_agents": [
                f"- {agent['name']}: {agent['description']}"
                for agent in available_agents
            ],
            "previous_conversation": previous_conversation,
            "user_feedback": "",  # Empty string for initial planning
        },
        config,
    )

    # Model call
    response = await async_model_call(
        llm_client=llm_client,
        state=state,
        config=config,
        formatted_prompt=formatted_messages,
    )

    # Parse the response
    last_message = list(response.messages)[-1]
    parsed_response = orchestrator_planning_parser.parse(str(last_message.content))

    logger.info(f"Orchestrator planning output: {parsed_response}")

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
                agent=step.agent,
            )
        )

    # Update the state
    state.is_irrelevant_query = parsed_response.is_irrelevant
    state.is_forbidden_query = parsed_response.is_forbidden

    # The index increments +1 at the first step (planning insights)
    state.current_step_index = -1

    logger.info(f"Final state after planning: {state}")
    logger.info(f"Steps created: {state.steps}")
    logger.info(f"Is irrelevant: {state.is_irrelevant_query}")

    return state


async def show_plan_to_user(state: ADTState, config: RunnableConfig) -> ADTState:
    """
    Show the planned steps to the user and allow for adjustments.

    Args:
        state: The state of the agent.
        config: The configuration of the agent.

    Returns:
        The state of the agent.
    """
    logger.info("Showing plan to user")

    # Format the plan for display
    plan_display = "Here's the planned steps:\n\n"
    for i, step in enumerate(state.steps, 1):
        plan_display += f"{i}. {step.step}\n"

    # Use interrupt to get user input
    user_response = interrupt(
        {
            "type": "plan_review",
            "content": f"{plan_display}\nWould you like to make any adjustments to this plan? Please respond with 'yes' if you want to modify the plan and provide specific feedback, or 'no' to proceed with the previous plan.",
        }
    )

    # Add the response to the messages
    state.add_message(HumanMessage(content=user_response["content"]))

    return state


async def handle_plan_response(state: ADTState, config: RunnableConfig) -> ADTState:
    """
    Handle the user's response to the plan and make adjustments if needed.

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

    # Format messages
    messages = ChatPromptTemplate(
        messages=[
            ("system", ORCHESTRATOR_SYSTEM_PROMPT),
            ("user", ORCHESTRATOR_PLANNING_PROMPT),
        ]
    )

    # Format messages
    formatted_messages = await messages.ainvoke(
        {
            "user_query": last_message,
            "available_agents": [
                f"- {agent['name']}: {agent['description']}"
                for agent in available_agents
            ],
            "previous_conversation": previous_conversation,
            "user_feedback": last_message,
        },
        config,
    )

    # Model call
    response = await async_model_call(
        llm_client=llm_client,
        state=state,
        config=config,
        formatted_prompt=formatted_messages,
    )

    # Parse the response
    last_message = list(response.messages)[-1]
    parsed_response = orchestrator_planning_parser.parse(str(last_message.content))
    logger.info(f"Planning response: {parsed_response}")

    # Check if the plan was accepted
    state.plan_accepted = not parsed_response.modified

    return state


async def execute_step(state: ADTState, config: RunnableConfig) -> ADTState:
    """
    Execute the current step in the plan.

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
    logger.info(f"Processing step {state.current_step_index + 1}: {current_step.step}")

    return state
