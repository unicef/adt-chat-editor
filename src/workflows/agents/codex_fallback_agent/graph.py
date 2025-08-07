from langgraph.graph import END, START, StateGraph

from src.workflows.agents.codex_fallback_agent.actions import fallback_agent
from src.workflows.state import ADTState

# Create the graph
fallback_agent_workflow = StateGraph(ADTState)

# Add nodes
fallback_agent_workflow.add_node("edit", fallback_agent)

# Add edges
fallback_agent_workflow.add_edge(START, "edit")
fallback_agent_workflow.add_edge("edit", END)

# Compile the graph
fallback_agent_workflow = fallback_agent_workflow.compile()
