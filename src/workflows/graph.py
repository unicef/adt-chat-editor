from langgraph.graph import END, START, StateGraph

from src.settings import custom_logger
from src.workflows.actions import (
    plan_steps,
    show_plan_to_user,
    handle_plan_response,
    execute_step,
)
from src.workflows.agents.text_edit_agent.graph import text_edit_workflow
from src.workflows.state import ADTState, BaseState
from src.structs.planning import PlanningStep


logger = custom_logger("Main Graph")

# Define a new graph
logger.info("Defining graph")
workflow = StateGraph(ADTState, input=BaseState)

# Define the graph nodes
logger.info("Defining graph nodes")
workflow.add_node("planner", plan_steps)
workflow.add_node("show_plan", show_plan_to_user)
workflow.add_node("handle_plan_response", handle_plan_response)
workflow.add_node("execute_step", execute_step)
workflow.add_node("text_edit_agent", text_edit_workflow)


# Define the graph edges
logger.info("Defining graph edges")
workflow.add_edge(START, "planner")


def check_irrelevant_query(state: ADTState) -> str:
    """
    Check if the query is irrelevant and end the workflow if it is.
    """
    logger.info(f"Checking if query is irrelevant. State: {state}")
    logger.info(f"Steps: {state.steps}")
    logger.info(f"Is irrelevant: {state.is_irrelevant_query}")

    if state.is_irrelevant_query:
        logger.info("Query is irrelevant, ending workflow")
        return END

    logger.info("Query is relevant, proceeding to show plan")
    return "show_plan"


def should_adjust_plan(state: ADTState) -> str:
    """
    Determine if we need to show the plan again based on the PlanAdjustment response.
    If the plan was modified, we show it again. If not, we proceed to execution.
    """
    # Get the last message from the user
    last_message = str(state.messages[-1].content).lower().strip()

    # If it's a simple "no", proceed with execution
    if last_message == "no":
        return "execute_step"

    # If the last message indicates the plan was modified, show it
    if "Plan has been modified" in str(state.messages[-1].content):
        return "show_plan"

    # Otherwise proceed with execution
    return "execute_step"


def route_to_agent(state: ADTState) -> str:
    """
    Route to the appropriate agent based on the current step.
    """
    if not state.steps:
        return END

    current_step: PlanningStep = state.steps[state.current_step_index]
    if current_step.agent == "Text Edit Agent":
        return "text_edit_agent"
    return END


def should_continue_execution(state: ADTState) -> str:
    """
    Determine if we should continue executing steps or end.
    """
    if not state.steps:
        return END

    if state.current_step_index >= len(state.steps) - 1:
        return END

    return "execute_step"


# Add conditional edges
# After planner, check if query is irrelevant
workflow.add_conditional_edges(
    "planner",
    check_irrelevant_query,
    {
        "show_plan": "show_plan",
        END: END,
    },
)

# After showing plan, handle user response
workflow.add_edge("show_plan", "handle_plan_response")

# After handling plan response, check if we need to show plan again
workflow.add_conditional_edges(
    "handle_plan_response",
    should_adjust_plan,
    {
        "show_plan": "show_plan",  # Show plan again if modified
        "execute_step": "execute_step",  # Proceed to execution if no changes needed
    },
)

# After executing step, route to appropriate agent
workflow.add_conditional_edges(
    "execute_step",
    route_to_agent,
    {"text_edit_agent": "text_edit_agent", END: END},
)

# After agent execution, check if we should continue
workflow.add_conditional_edges(
    "text_edit_agent",
    should_continue_execution,
    {
        "execute_step": "execute_step",
        END: END,
    },
)

# Compile the workflow into an executable graph
graph = workflow.compile()
graph.name = "ADT Fixer Agentic Graph"
logger.info("Graph compiled!")
