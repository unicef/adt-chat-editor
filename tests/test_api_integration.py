import pytest
from fastapi.testclient import TestClient

from src.api.main import create_app
from src.structs.status import WorkflowStatus


class FakeGraph:
    async def ainvoke(self, state):
        # Return a minimal output compatible with save_state_checkpoint
        from langchain_core.messages import HumanMessage, AIMessage
        return {
            "messages": [AIMessage(content="Plan acknowledged.")],
            "user_query": [HumanMessage(content="hello")],
            "status": WorkflowStatus.SUCCESS,
        }


@pytest.fixture
def client(monkeypatch):
    # Patch the graph used by the chat router before app creates routes
    import src.api.routes.chat as chat_route
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
    assert data["status"] in {"success", "in_progress", "waiting_for_user_input", "failure"}
    assert "messages" in data and isinstance(data["messages"], list)


def test_adt_utils_run_script_success(monkeypatch, client):
    # Simulate presence of directories and successful script run
    import os
    import subprocess
    import src.api.routes.adt_utils as adt_mod

    monkeypatch.setattr(os.path, "exists", lambda p: True)
    cp = subprocess.CompletedProcess(args=["python"], returncode=0, stdout="All good", stderr="")
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: cp)

    r = client.post(
        "/adt-utils/run-script",
        json={
            "script_type": "validate_adt",
            "verbose": True
        },
    )
    assert r.status_code == 200
    js = r.json()
    assert js["status"] == "success"

