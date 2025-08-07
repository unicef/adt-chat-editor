from langgraph.graph import END, START, StateGraph

from src.workflows.agents.codex_fallback_agent.graph import fallback_agent_workflow
from src.workflows.agents.asset_transfer_agent.graph import asset_transfer_workflow
from src.workflows.agents.layout_edit_agent.graph import layout_edit_workflow
from src.workflows.agents.layout_mirror_agent.graph import layout_mirror_workflow
from src.workflows.agents.subgraph.routes import route_to_agent
from src.workflows.agents.text_edit_agent.graph import text_edit_workflow
from src.workflows.agents.web_delete_agent.graph import web_delete_workflow
from src.workflows.agents.web_merge_agent.graph import web_merge_workflow
from src.workflows.agents.web_split_agent.graph import web_split_workflow
from src.workflows.state import ADTState

# Create the graph
agents_subgraph = StateGraph(ADTState)

# Add nodes
agents_subgraph.add_node("text_edit_agent", text_edit_workflow)
agents_subgraph.add_node("layout_edit_agent", layout_edit_workflow)
agents_subgraph.add_node("layout_mirror_agent", layout_mirror_workflow)
agents_subgraph.add_node("web_merge_agent", web_merge_workflow)
agents_subgraph.add_node("web_split_agent", web_split_workflow)
agents_subgraph.add_node("web_delete_agent", web_delete_workflow)
agents_subgraph.add_node("asset_transfer_agent", asset_transfer_workflow)
agents_subgraph.add_node("codex_fallback_agent", fallback_agent_workflow)

# Add edges
agents_subgraph.add_conditional_edges(
    START,
    route_to_agent,
    {
        "text_edit_agent": "text_edit_agent",
        "layout_edit_agent": "layout_edit_agent",
        "layout_mirror_agent": "layout_mirror_agent",
        "web_merge_agent": "web_merge_agent",
        "web_split_agent": "web_split_agent",
        "web_delete_agent": "web_delete_agent",
        "asset_transfer_agent": "asset_transfer_agent",
        "codex_fallback_agent": "codex_fallback_agent",
    },
)
agents_subgraph.add_edge("text_edit_agent", END)
agents_subgraph.add_edge("layout_edit_agent", END)
agents_subgraph.add_edge("layout_mirror_agent", END)
agents_subgraph.add_edge("web_merge_agent", END)
agents_subgraph.add_edge("web_split_agent", END)
agents_subgraph.add_edge("web_delete_agent", END)
agents_subgraph.add_edge("asset_transfer_agent", END)
agents_subgraph.add_edge("codex_fallback_agent", END)

# Compile the graph
agents_subgraph = agents_subgraph.compile()
