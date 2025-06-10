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
) -> Literal["rephrase_query", "show_plan", "non_valid_message"]:
    """
    Check if the query is relevant, forbidden, or irrelevant and end the workflow if it is.
    If the query is relevant and steps are not empty, proceed to show the plan.
    If the query is relevant and steps are empty, proceed to rephrase the query.
    If the query is forbidden, end the workflow.
    If the query is irrelevant, end the workflow.
    """

    if state.is_irrelevant_query:
        logger.info("Query is irrelevant, ending workflow")
        return "non_valid_message"
    elif state.is_forbidden_query:
        logger.info("Query is forbidden, ending workflow")
        return "non_valid_message"
    elif state.steps:
        logger.info(
            "Query is relevant and steps are not empty, proceeding to show plan"
        )
        return "show_plan"

    logger.info("Query is relevant and steps are empty, proceeding to rephrase query")
    return "rephrase_query"


def should_adjust_plan(
    state: ADTState,
) -> Literal["show_plan", "execute_step", "__end__"]:
    """
    Determine if we should adjust the plan or proceed with execution.
    """

    if state.plan_accepted:
        return "execute_step"
    else:
        return "show_plan"


def route_to_agent(
    state: ADTState,
) -> Literal[
    "text_edit_agent",
    "layout_edit_agent",
    "layout_mirror_agent",
    "web_merge_agent",
    "web_split_agent",
    "web_delete_agent",
    "finalize_task",
    "__end__",
]:
    """
    Route to the appropriate agent based on the current step.
    """
    if not state.steps:
        return "__end__"

    current_step: PlanningStep = state.steps[state.current_step_index]
    agent_name = current_step.agent.lstrip("- ").strip()

    if "Text Edit Agent" in agent_name:
        return "text_edit_agent"
    elif "Layout Edit Agent" in agent_name:
        return "layout_edit_agent"
    elif "Layout Mirror Agent" in agent_name:
        return "layout_mirror_agent"
    elif "Web Merge Agent" in agent_name:
        return "web_merge_agent"
    elif "Web Split Agent" in agent_name:
        return "web_split_agent"
    elif "Web Delete Agent" in agent_name:
        return "web_delete_agent"

    return "finalize_task"


def should_continue_execution(state: ADTState) -> Literal["execute_step", "__end__"]:
    """
    Determine if we should continue executing steps or end.
    """
    if (not state.steps) or (state.current_step_index >= len(state.steps) - 1):
        return "__end__"

    return "execute_step"
