from typing import Literal

from src.workflows.state import ADTState, PlanningStep
from src.settings import custom_logger


logger = custom_logger("Main Workflow Routes")


def route_user_message(
    state: ADTState,
) -> Literal["planner", "handle_plan_response"]:
    """
    Route the user message to the appropriate node.
    If the plan has not been shown to the user, route to the planner.
    If the plan has been shown to the user, route to the handle_plan_response.

    Args:
        state: The state of the agent.

    Returns:
        The name of the node to route to.
    """
    logger.info(f"Showing plan to user -> state: {state}")
    if state.plan_shown_to_user:
        return "handle_plan_response"
    else:
        return "planner"


def check_valid_query(
    state: ADTState,
) -> Literal["rephrase_query", "show_plan", "non_valid_message", "execute_step"]:
    """
    Check if the query is relevant, forbidden, or irrelevant and end the workflow if it is.
    Else, proceed to show the plan or execute the next step.
    """

    if state.is_irrelevant_query:
        logger.info("Query is irrelevant, ending workflow")
        return "non_valid_message"
    elif state.is_forbidden_query:
        logger.info("Query is forbidden, ending workflow")
        return "non_valid_message"
    elif not state.steps:
        logger.info(
            "Query is relevant and steps are empty, proceeding to rephrase query"
        )
        return "rephrase_query"
    elif not state.plan_accepted:
        logger.info(
            "Query is relevant and steps are not empty, proceeding to show plan"
        )
        return "show_plan"

    return "execute_step"


def route_to_agent(
    state: ADTState,
) -> Literal[
    "agents_subgraph",
    "finalize_task",
    "__end__",
]:
    """
    Route to the appropriate agent based on the current step.
    """
    if not state.steps:
        return "__end__"
    return "agents_subgraph"


def should_continue_execution(
    state: ADTState,
) -> Literal["execute_step", "finalize_task"]:
    """
    Determine if we should continue executing steps or end.
    """
    if state.current_step_index >= len(state.steps) - 1:
        return "finalize_task"

    return "execute_step"
