from langgraph.graph import END, StateGraph

from app.graph.nodes import (
    await_final_approval_node,
    await_project_selection_node,
    decline_node,
    mark_applied_node,
    rank_projects_node,
    route_after_final_approval,
    route_after_project_selection,
    tailor_node,
)
from app.graph.state import TailorGraphState


def build_graph(checkpointer):
    builder = StateGraph(TailorGraphState)

    builder.add_node("rank_projects", rank_projects_node)
    builder.add_node("await_project_selection", await_project_selection_node)
    builder.add_node("tailor", tailor_node)
    builder.add_node("await_final_approval", await_final_approval_node)
    builder.add_node("mark_applied", mark_applied_node)
    builder.add_node("decline", decline_node)

    builder.add_edge("__start__", "rank_projects")
    builder.add_edge("rank_projects", "await_project_selection")
    builder.add_conditional_edges(
        "await_project_selection", route_after_project_selection, {"tailor": "tailor", "decline": "decline"}
    )
    builder.add_edge("tailor", "await_final_approval")
    builder.add_conditional_edges(
        "await_final_approval",
        route_after_final_approval,
        {"mark_applied": "mark_applied", "decline": "decline"},
    )
    builder.add_edge("mark_applied", END)
    builder.add_edge("decline", END)

    return builder.compile(checkpointer=checkpointer)
