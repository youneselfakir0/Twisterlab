import pytest
import httpx
import os

# Configuration (Overridable by Env Vars)
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
    with httpx.Client(base_url=api_url, timeout=TIMEOUT) as client:
        yield client
