from langgraph.graph import END, START, StateGraph

from src.settings import custom_logger
from src.workflows.actions import (
    execute_step,
    handle_plan_response,
    plan_steps,
    show_plan_to_user,
)
from src.workflows.agents.layout_edit_agent.graph import layout_edit_workflow
from src.workflows.agents.text_edit_agent.graph import text_edit_workflow
from src.workflows.routes import (
    check_irrelevant_query,
    should_adjust_plan,
    route_to_agent,
    should_continue_execution,
)
from src.workflows.state import ADTState, BaseState

logger = custom_logger("Main Workflow Graph")

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
workflow.add_node("layout_edit_agent", layout_edit_workflow)


# Define the graph edges
logger.info("Defining graph edges")
workflow.add_edge(START, "planner")
workflow.add_conditional_edges(
    "planner",
    check_irrelevant_query,
    {
        "show_plan": "show_plan",
        END: END,
    },
)
workflow.add_edge("show_plan", "handle_plan_response")
workflow.add_conditional_edges(
    "handle_plan_response",
    should_adjust_plan,
    {
        "show_plan": "show_plan",
        "execute_step": "execute_step",
    },
)
workflow.add_conditional_edges(
    "execute_step",
    route_to_agent,
    {
        "text_edit_agent": "text_edit_agent",
        "layout_edit_agent": "layout_edit_agent",
        END: END
    },
)
workflow.add_conditional_edges(
    "text_edit_agent",
    should_continue_execution,
    {
        "execute_step": "execute_step",
        END: END,
    },
)
workflow.add_conditional_edges(
    "layout_edit_agent",
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
