from src.workflows.routes import (
    route_user_message,
    check_valid_query,
    route_to_agent,
    should_continue_execution,
)
from src.workflows.state import ADTState
from src.structs.planning import PlanningStep


def make_state(**kwargs) -> ADTState:
    # Provide minimal valid state; ADTState has defaults for most fields
    return ADTState(**kwargs)


def test_route_user_message():
    s = make_state(plan_shown_to_user=False)
    assert route_user_message(s) == "planner"
    s.plan_shown_to_user = True
    assert route_user_message(s) == "handle_plan_response"


def test_check_valid_query_paths():
    s = make_state(is_irrelevant_query=True)
    assert check_valid_query(s) == "non_valid_message"

    s = make_state(is_irrelevant_query=False, is_forbidden_query=True)
    assert check_valid_query(s) == "non_valid_message"

    s = make_state(is_irrelevant_query=False, is_forbidden_query=False, steps=[])
    assert check_valid_query(s) == "rephrase_query"

    # Steps exist but plan not accepted yet
    step = PlanningStep(step="do x", non_technical_description="", agent="Text Edit Agent", html_files=[], layout_template_files=[])
    s = make_state(is_irrelevant_query=False, is_forbidden_query=False, steps=[step], plan_accepted=False)
    assert check_valid_query(s) == "show_plan"

    # Plan accepted, proceed to execute
    s.plan_accepted = True
    assert check_valid_query(s) == "execute_step"


def test_route_to_agent_and_continue():
    # No steps => end
    s = make_state(steps=[])
    assert route_to_agent(s) == "__end__"

    # With steps => go to agents_subgraph
    step = PlanningStep(step="do x", non_technical_description="", agent="Text Edit Agent", html_files=[], layout_template_files=[])
    s = make_state(steps=[step], current_step_index=0)
    assert route_to_agent(s) == "agents_subgraph"

    # Continue execution logic
    s = make_state(steps=[step, step], current_step_index=0)
    assert should_continue_execution(s) == "execute_step"
    # When current_step_index at last index with single step
    t = make_state(steps=[step], current_step_index=0)
    assert should_continue_execution(t) == "finalize_task"
