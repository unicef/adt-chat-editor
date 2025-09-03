import json

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig

from src.workflows import actions as actions_mod
from src.workflows.actions import handle_plan_response, plan_steps
from src.workflows.state import ADTState


class DummyAI(AIMessage):
    pass


def orchestrator_response(steps, modified=False, irrelevant=False, forbidden=False):
    return json.dumps({
        "is_irrelevant": irrelevant,
        "is_forbidden": forbidden,
        "steps": steps,
        "modified": modified,
        "comments": ""
    })


@pytest.mark.asyncio
async def test_plan_steps_happy_path(monkeypatch):
    # Prepare state to bypass initialization side effects

    state = ADTState(
        messages=[HumanMessage(content="please plan")],
        user_query="",
        available_languages=["en"],
        language="en",
    )
    state.tailwind_status = state.tailwind_status.INSTALLED
    state.translated_html_status = state.translated_html_status.INSTALLED

    # Mock files loading

    async def fake_load_translated_html_contents(language: str):
        return [{"/tmp/a.html": [{"k": "v"}]}]

    monkeypatch.setattr(actions_mod, "load_translated_html_contents", fake_load_translated_html_contents)

    # Mock model call to return a deterministic planning JSON

    async def fake_async_model_call(llm_client, config, formatted_prompt):
        payload = orchestrator_response([
            {
                "step": "Edit text in (a.html)",
                "non_technical_description": "Improve wording",
                "agent": "Text Edit Agent",
                "html_files": ["/tmp/a.html"],
                "layout_template_files": [],
            }
        ])
        return AIMessage(content=payload)

    monkeypatch.setattr(actions_mod, "async_model_call", fake_async_model_call)

    out = await plan_steps(state, RunnableConfig({}))
    assert len(out.steps) == 1
    assert out.steps[0].agent == "Text Edit Agent"
    assert "/tmp/a.html" in out.steps[0].html_files


@pytest.mark.asyncio
async def test_handle_plan_response_modified(monkeypatch):

    state = ADTState(
        messages=[HumanMessage(content="feedback: modify plan")],
        user_query="",
        available_languages=["en"],
        language="en",
        steps=[],
        completed_steps=[],
    )
    state.tailwind_status = state.tailwind_status.INSTALLED
    state.translated_html_status = state.translated_html_status.INSTALLED

    # Fake files

    async def fake_load_translated_html_contents(language: str):
        return [{"/tmp/a.html": [{"k": "v"}]}]

    monkeypatch.setattr(actions_mod, "load_translated_html_contents", fake_load_translated_html_contents)

    # User feedback triggers a modified plan

    async def fake_async_model_call(llm_client, config, formatted_prompt):
        payload = orchestrator_response([
            {
                "step": "Mirror layout (a.html) from (templ.html)",
                "non_technical_description": "Copy layout",
                "agent": "Layout Mirror Agent",
                "html_files": ["/tmp/a.html"],
                "layout_template_files": ["/tmp/templ.html"],
            }
        ], modified=True)
        return AIMessage(content=payload)

    monkeypatch.setattr(actions_mod, "async_model_call", fake_async_model_call)

    out = await handle_plan_response(state, RunnableConfig({}))
    assert out.plan_accepted is False
    assert len(out.steps) == 1
    assert out.steps[0].agent == "Layout Mirror Agent"
