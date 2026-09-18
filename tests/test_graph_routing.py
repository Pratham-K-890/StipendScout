from app.graph.nodes import route_after_final_approval, route_after_project_selection


def test_route_after_project_selection_approve():
    state = {"project_decision": {"action": "approve", "selected_repo_names": ["a"]}}
    assert route_after_project_selection(state) == "tailor"


def test_route_after_project_selection_decline():
    state = {"project_decision": {"action": "decline"}}
    assert route_after_project_selection(state) == "decline"


def test_route_after_final_approval_approve():
    state = {"final_decision": {"action": "approve"}}
    assert route_after_final_approval(state) == "mark_applied"


def test_route_after_final_approval_decline():
    state = {"final_decision": {"action": "decline"}}
    assert route_after_final_approval(state) == "decline"
