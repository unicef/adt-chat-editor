import os
import sys
import pytest

from fastapi.testclient import TestClient
from src.api.main import create_app
from src.utils.auth import create_jwt_token

# Ensure repository root is on sys.path so 'src' package imports work consistently
repo_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)


@pytest.fixture()
def authorized_client():
    client = TestClient(create_app())
    token = create_jwt_token(subject="api_access")
    client.headers = {**client.headers, "Authorization": f"Bearer {token}"}
    return client
