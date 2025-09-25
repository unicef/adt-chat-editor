import os
import subprocess

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, HumanMessage

import src.api.routes.chat as chat_route
from src.api.main import create_app
from src.structs.status import WorkflowStatus


class FakeGraph:
    async def ainvoke(self, state):
        # Return a minimal output compatible with save_state_checkpoint
        return {
            "messages": [AIMessage(content="Plan acknowledged.")],
            "user_query": [HumanMessage(content="hello")],
            "status": WorkflowStatus.SUCCESS,
        }


@pytest.fixture
def client(monkeypatch):
    # Patch the graph used by the chat router before app creates routes
    chat_route.graph = FakeGraph()
    app = create_app()
    return TestClient(app)


def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_chat_edit_minimal_flow(client):
    payload = {
        "session_id": "s1",
        "user_message": "hello",
        "language": "en",
        "user_language": "en",
        "pages": [],
        "book_information": {"id": "b1", "version": "v1"},
    }
    r = client.post("/chat/edit", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] in {
        "success",
        "in_progress",
        "waiting_for_user_input",
        "failure",
    }
    assert "messages" in data and isinstance(data["messages"], list)


def test_adt_utils_run_script_success(monkeypatch, client):
    # Simulate presence of directories and successful script run
    monkeypatch.setattr(os.path, "exists", lambda p: True)
    cp = subprocess.CompletedProcess(
        args=["python"], returncode=0, stdout="All good", stderr=""
    )
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: cp)

    # Patch ADT utils discovery to avoid filesystem dependency
    import src.api.routes.adt_utils as adt_utils_route

    class FakeArg:
        def __init__(self, name, type, default):
            self.name = name
            self.type = type
            self.default = default

    class FakeScript:
        def __init__(self):
            self.id = "validate_adt"
            self.path = "validate_adt.py"
            self.arguments = [
                FakeArg("target_dir", "str", None),
                FakeArg("verbose", "bool", False),
            ]

        def model_copy(self, deep=False):
            from copy import deepcopy

            return deepcopy(self)

    monkeypatch.setattr(
        adt_utils_route,
        "_get_adt_utils",
        lambda: {"PRODUCTION_SCRIPTS": [FakeScript()]},
    )

    r = client.post(
        "/adt-utils/run-script",
        json={
            "script_id": "validate_adt",
            "arguments": {"verbose": True},
        },
    )
    assert r.status_code == 200
    js = r.json()
    assert js["status"] == "success"
