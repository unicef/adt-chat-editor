from typing import Annotated

from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END, START

from src.workflows.agents.text_edit_agent.actions import edit_text
from src.workflows.state import ADTState


# Create the graph
text_edit_workflow = StateGraph(ADTState)

# Add nodes
text_edit_workflow.add_node("edit", edit_text)

# Add edges
text_edit_workflow.add_edge(START, "edit")
text_edit_workflow.add_edge("edit", END)

# Compile the graph
text_edit_workflow = text_edit_workflow.compile()
