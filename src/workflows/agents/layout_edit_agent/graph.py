
from langgraph.graph import END, START, StateGraph

from src.workflows.agents.layout_edit_agent.actions import edit_layout
from src.workflows.state import ADTState

# Create the graph
layout_edit_workflow = StateGraph(ADTState)

# Add nodes
layout_edit_workflow.add_node("edit", edit_layout)

# Add edges
layout_edit_workflow.add_edge(START, "edit")
layout_edit_workflow.add_edge("edit", END)

# Compile the graph
layout_edit_workflow = layout_edit_workflow.compile()
