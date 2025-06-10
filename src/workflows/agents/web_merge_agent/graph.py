from langgraph.graph import END, START, StateGraph

from src.workflows.agents.web_merge_agent.actions import web_merge
from src.workflows.state import ADTState

# Create the graph
web_merge_workflow = StateGraph(ADTState)

# Add nodes
web_merge_workflow.add_node("edit", web_merge)

# Add edges
web_merge_workflow.add_edge(START, "edit")
web_merge_workflow.add_edge("edit", END)

# Compile the graph
web_merge_workflow = web_merge_workflow.compile()
