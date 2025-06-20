from typing import Literal

from src.settings import custom_logger
from src.workflows.state import ADTState, PlanningStep


# Create logger
logger = custom_logger("Agents Subgraph Routes")


# Define the routes
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
    else:
        raise ValueError(f"Invalid agent name: {agent_name}")
