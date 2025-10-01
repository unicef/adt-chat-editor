import pytest
from fastapi.testclient import TestClient

import src.api.routes.publish as publish_mod
from src.api.main import create_app


class FakeGitManager:
    def __init__(self):
        self.commits = [{"hash": "abc", "message": "msg"}]

    async def commit_changes(self, message: str) -> bool:
        return True

    async def current_branch(self) -> str:
        return "feature/test"

    async def list_commits(self, branch_name: str, limit: int = 50, author_email: str = "bot@example.com", since_last_push: bool = True):
        return self.commits

    async def safe_push(self, branch_name: str):
        return None

    async def tag_last_published_commit(self, tag_name: str = "last_published"):
        return None

    async def pull_request_exists(self, branch_name: str) -> bool:
        return False

    async def create_pull_request(self, title: str, body: str = "", base: str = "main") -> str:
        return "https://github.com/org/repo/pull/1"

    async def checkout_commit(self, commit_hash: str):
        return None


@pytest.fixture
def authorized_client(monkeypatch):
    # Patch provider to return our fake manager
    async def fake_get_git_manager():
        return FakeGitManager()

    publish_mod.get_git_manager = fake_get_git_manager

    from src.utils.auth import create_jwt_token
    app = create_app()
    client = TestClient(app)
    token = create_jwt_token(subject="api_access")
    client.headers = {**client.headers, "Authorization": f"Bearer {token}"}
    return client


def test_publish_commit_endpoint(authorized_client):
    payload = {"message": "test", "book_information": {"id": "id", "version": "v"}}
    r = authorized_client.post("/publish/commit", json=payload)
    assert r.status_code == 200
    assert r.json()["status"] in {"committed", "not-committed", "error"}


def test_publish_changes_endpoint(authorized_client):
    payload = {"message": "version_1", "book_information": {"id": "id", "version": "v"}}
    r = authorized_client.post("/publish", json=payload)
    assert r.status_code == 200
    assert r.json()["status"] in {"published", "not-published", "error"}


def test_publish_commits_list(authorized_client):
    r = authorized_client.get("/publish/commits")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
