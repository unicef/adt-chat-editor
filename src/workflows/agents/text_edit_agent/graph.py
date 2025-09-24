"""LangGraph definition for the Text Edit Agent with TTS regeneration node."""

from langgraph.graph import END, START, StateGraph

from src.workflows.agents.text_edit_agent.actions import (
    detect_text_edits,
    edit_texts,
    regenerate_tts_for_edits,
)
from src.workflows.state import ADTState

# Create the graph
text_edit_workflow = StateGraph(ADTState)

# Add nodes
text_edit_workflow.add_node("detect_text_edits", detect_text_edits)
text_edit_workflow.add_node("edit_texts", edit_texts)
text_edit_workflow.add_node("regenerate_tts_for_edits", regenerate_tts_for_edits)


# Add edges
text_edit_workflow.add_edge(START, "detect_text_edits")
text_edit_workflow.add_edge("detect_text_edits", "edit_texts")
text_edit_workflow.add_edge("edit_texts", "regenerate_tts_for_edits")
text_edit_workflow.add_edge("regenerate_tts_for_edits", END)

# Compile the graph
text_edit_workflow = text_edit_workflow.compile()
