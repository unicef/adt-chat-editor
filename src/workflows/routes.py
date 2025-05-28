from typing import Literal

from src.workflows.state import ADTState, PlanningStep
from src.settings import custom_logger


logger = custom_logger("Main Workflow Routes")


def check_valid_query(state: ADTState) -> Literal["show_plan", "__end__"]:
    """
    Check if the query is valid and end the workflow if it is not.
    """

    if state.is_irrelevant_query:
        logger.info("Query is irrelevant, ending workflow")
        return "__end__"
    elif state.is_forbidden_query:
        logger.info("Query is forbidden, ending workflow")
        return "__end__"

    logger.info("Query is relevant, proceeding to show plan")
    return "show_plan"


def should_rephrase_query(state: ADTState) -> Literal["rephrase_query", "show_plan"]:
    """
    Determine if the user should rephrase the query or the system should show the plan.
    """
    if state.steps:
        return "show_plan"
    else:
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
) -> Literal["text_edit_agent", "layout_edit_agent", "layout_mirror_agent", "__end__"]:
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

    return "__end__"


def should_continue_execution(state: ADTState) -> Literal["execute_step", "__end__"]:
    """
    Determine if we should continue executing steps or end.
    """
    if (not state.steps) or (state.current_step_index >= len(state.steps) - 1):
        return "__end__"

    return "execute_step"
