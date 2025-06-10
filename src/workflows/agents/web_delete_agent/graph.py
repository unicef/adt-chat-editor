from langgraph.graph import END, START, StateGraph

from src.workflows.agents.web_delete_agent.actions import web_delete
from src.workflows.state import ADTState

# Create the graph
web_delete_workflow = StateGraph(ADTState)

# Add nodes
web_delete_workflow.add_node("edit", web_delete)

# Add edges
web_delete_workflow.add_edge(START, "edit")
web_delete_workflow.add_edge("edit", END)

# Compile the graph
web_delete_workflow = web_delete_workflow.compile()
