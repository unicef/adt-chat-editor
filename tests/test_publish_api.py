import pytest
from fastapi.testclient import TestClient


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
def client(monkeypatch):
    from src.api.main import create_app

    # Patch provider to return our fake manager
    async def fake_get_git_manager():
        return FakeGitManager()

    import src.api.routes.publish as publish_mod
    publish_mod.get_git_manager = fake_get_git_manager

    app = create_app()
    return TestClient(app)


def test_publish_commit_endpoint(client):
    payload = {"message": "test", "book_information": {"id": "id", "version": "v"}}
    r = client.post("/publish/commit", json=payload)
    assert r.status_code == 200
    assert r.json()["status"] in {"committed", "not-committed", "error"}


def test_publish_changes_endpoint(client):
    payload = {"message": "version_1", "book_information": {"id": "id", "version": "v"}}
    r = client.post("/publish", json=payload)
    assert r.status_code == 200
    assert r.json()["status"] in {"published", "not-published", "error"}


def test_publish_commits_list(client):
    r = client.get("/publish/commits")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
