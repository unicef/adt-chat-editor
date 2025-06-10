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
from src.workflows.agents.layout_edit_agent.graph import layout_edit_workflow
from src.workflows.agents.layout_mirror_agent.graph import layout_mirror_workflow
from src.workflows.agents.text_edit_agent.graph import text_edit_workflow
from src.workflows.agents.web_merge_agent.graph import web_merge_workflow
from src.workflows.agents.web_split_agent.graph import web_split_workflow
from src.workflows.agents.web_delete_agent.graph import web_delete_workflow

from src.workflows.routes import (
    check_valid_query,
    should_adjust_plan,
    should_continue_execution,
    route_to_agent,
    route_user_message,
)
from src.workflows.state import ADTState, BaseState


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
workflow.add_node("text_edit_agent", text_edit_workflow)
workflow.add_node("layout_edit_agent", layout_edit_workflow)
workflow.add_node("layout_mirror_agent", layout_mirror_workflow)
workflow.add_node("web_merge_agent", web_merge_workflow)
workflow.add_node("web_split_agent", web_split_workflow)
workflow.add_node("web_delete_agent", web_delete_workflow)


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
    },
)
workflow.add_conditional_edges(
    "rephrase_query",
    rephrase_query,
    {
        "planner": "planner",
        "__end__": END,
    },
)
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
        "layout_mirror_agent": "layout_mirror_agent",
        "web_merge_agent": "web_merge_agent",
        "web_split_agent": "web_split_agent",
        "web_delete_agent": "web_delete_agent",
        "finalize_task": "finalize_task",
        END: END,
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
workflow.add_conditional_edges(
    "layout_mirror_agent",
    should_continue_execution,
    {
        "execute_step": "execute_step",
        END: END,
    },
)
workflow.add_conditional_edges(
    "web_merge_agent",
    should_continue_execution,
    {
        "execute_step": "execute_step",
        END: END,
    },
)
workflow.add_conditional_edges(
    "web_split_agent",
    should_continue_execution,
    {
        "execute_step": "execute_step",
        END: END,
    },
)
workflow.add_conditional_edges(
    "web_delete_agent",
    should_continue_execution,
    {
        "execute_step": "execute_step",
        END: END,
    },
)
workflow.add_edge("show_plan", END)
workflow.add_edge("non_valid_message", END)
workflow.add_edge("finalize_task", END)

# Compile the workflow into an executable graph
graph = workflow.compile()
graph.name = "ADT Fixer Agentic Graph"
logger.info("Graph compiled!")
