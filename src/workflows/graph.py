from langgraph.graph import END, START, StateGraph

from src.settings import custom_logger
from src.workflows.actions import (
    add_non_valid_message,
    execute_next_step,
    handle_plan_response,
    finalize_task_execution,
    plan_steps,
    rephrase_query,
    show_plan_to_user,
)
from src.workflows.agents.subgraph.graph import agents_subgraph
from src.workflows.routes import (
    check_valid_query,
    route_to_agent,
    route_user_message,
    should_continue_execution,
)
from src.workflows.state import ADTState


# Create logger
logger = custom_logger("Main Workflow Graph")

# Define a new graph
logger.info("Defining graph")
workflow = StateGraph(ADTState)

# Define the graph nodes
logger.info("Defining graph nodes")
workflow.add_node("planner", plan_steps)
workflow.add_node("finalize_task", finalize_task_execution)
workflow.add_node("non_valid_message", add_non_valid_message)
workflow.add_node("rephrase_query", rephrase_query)
workflow.add_node("show_plan", show_plan_to_user)
workflow.add_node("handle_plan_response", handle_plan_response)
workflow.add_node("execute_step", execute_next_step)
workflow.add_node("agents_subgraph", agents_subgraph)


# Define the graph edges
logger.info("Defining graph edges")
workflow.add_conditional_edges(
    START,
    route_user_message,
    {
        "planner": "planner",
        "handle_plan_response": "handle_plan_response",
    },
)
workflow.add_conditional_edges(
    "planner",
    check_valid_query,
    {
        "rephrase_query": "rephrase_query",
        "show_plan": "show_plan",
        "non_valid_message": "non_valid_message",
        "execute_step": "execute_step",
    },
)
workflow.add_edge("rephrase_query", END)

workflow.add_conditional_edges(
    "handle_plan_response",
    check_valid_query,
    {
        "rephrase_query": "rephrase_query",
        "show_plan": "show_plan",
        "non_valid_message": "non_valid_message",
        "execute_step": "execute_step",
    },
)
workflow.add_conditional_edges(
    "execute_step",
    route_to_agent,
    {
        "agents_subgraph": "agents_subgraph",
        END: END,
    },
)

workflow.add_conditional_edges(
    "agents_subgraph",
    should_continue_execution,
    {
        "execute_step": "execute_step",
        "finalize_task": "finalize_task",
    },
)
workflow.add_edge("show_plan", END)
workflow.add_edge("non_valid_message", END)
workflow.add_edge("finalize_task", END)

# Compile the workflow into an executable graph
graph = workflow.compile()
graph.name = "ADT Fixer Agentic Graph"
logger.info("Graph compiled!")
