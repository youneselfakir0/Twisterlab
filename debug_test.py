import pytest
import sys
import os

# Set Env
os.environ["MCP_API_URL"] = "http://192.168.0.30:30001"

# Run pytest programmatically
retcode = pytest.main(["tests/e2e/test_2_agents.py", "-k", "code_review", "-v", "--tb=short"])
sys.exit(retcode)
