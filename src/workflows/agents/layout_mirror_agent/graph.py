from langgraph.graph import END, START, StateGraph

from src.workflows.agents.layout_mirror_agent.actions import mirror_layout
from src.workflows.state import ADTState


# Create the graph
layout_mirror_workflow = StateGraph(ADTState)

# Add nodes
layout_mirror_workflow.add_node("edit", mirror_layout)

# Add edges
layout_mirror_workflow.add_edge(START, "edit")
layout_mirror_workflow.add_edge("edit", END)

# Compile the graph
layout_mirror_workflow = layout_mirror_workflow.compile()
