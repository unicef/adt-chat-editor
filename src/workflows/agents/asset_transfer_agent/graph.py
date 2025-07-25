from langgraph.graph import END, START, StateGraph

from src.workflows.agents.asset_transfer_agent.actions import asset_transfer
from src.workflows.state import ADTState

# Create the graph
asset_transfer_workflow = StateGraph(ADTState)

# Add nodes
asset_transfer_workflow.add_node("edit", asset_transfer)

# Add edges
asset_transfer_workflow.add_edge(START, "edit")
asset_transfer_workflow.add_edge("edit", END)

# Compile the graph
asset_transfer_workflow = asset_transfer_workflow.compile()
