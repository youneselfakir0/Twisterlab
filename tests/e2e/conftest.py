import pytest
import httpx
import os

# Configuration (Overridable by Env Vars)
# Set E2E_LOCAL=1 to use FastAPI TestClient instead of remote httpx client
USE_LOCAL = os.getenv("E2E_LOCAL", "0").lower() in ("1", "true", "yes")
BASE_URL = os.getenv("MCP_API_URL", "http://192.168.0.30:30001")
TIMEOUT = 10.0


@pytest.fixture(scope="session")
def api_url():
    return BASE_URL


@pytest.fixture(scope="session")
def admin_headers():
    return {
        "Authorization": "Bearer dev-token-admin",
        "Content-Type": "application/json"
    }


@pytest.fixture(scope="session")
def viewer_headers():
    return {
        "Authorization": "Bearer dev-token-user",
        "Content-Type": "application/json"
    }


@pytest.fixture(scope="session")
def anonymous_headers():
    return {
        "Content-Type": "application/json"
    }


@pytest.fixture(scope="module")
def client(api_url):
    """
    HTTP client for E2E tests.
    
    Set E2E_LOCAL=1 to use FastAPI TestClient (faster, no network required).
    Otherwise uses httpx to connect to the remote API.
    """
    if USE_LOCAL:
        # Use FastAPI TestClient for local testing
        from fastapi.testclient import TestClient
        from twisterlab.api.main import app
        with TestClient(app) as local_client:
            yield local_client
    else:
        # Use httpx for remote testing against deployed API
        with httpx.Client(base_url=api_url, timeout=TIMEOUT) as remote_client:
            yield remote_client
