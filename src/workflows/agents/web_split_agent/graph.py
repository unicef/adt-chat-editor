from langgraph.graph import END, START, StateGraph

from src.workflows.agents.web_split_agent.actions import web_split
from src.workflows.state import ADTState

# Create the graph
web_split_workflow = StateGraph(ADTState)

# Add nodes
web_split_workflow.add_node("edit", web_split)

# Add edges
web_split_workflow.add_edge(START, "edit")
web_split_workflow.add_edge("edit", END)

# Compile the graph
web_split_workflow = web_split_workflow.compile()
