import ast
import os
import pytest

# Registry of known agent IDs and aliases that should NOT be hardcoded in plans
BANNED_AGENT_LITERALS = {
    "classifier", "sentiment", "summarizer", "translation", "cortex", 
    "code-review", "vba-expert", "resolver", "monitoring", "backup", 
    "sync", "archive", "commander", "browser", "n8n-navigator", 
    "invoke-ai", "notion", "database", "real-browser", "real-archive",
    "real-classifier", "real-code-review", "real-desktop-commander",
    "web-desktop-navigator"
}

MAESTRO_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", "src", "twisterlab", "agents", "real", "real_maestro_agent.py"
))

class MaestroArchVisitor(ast.NodeVisitor):
    def __init__(self):
        self.errors = []
        self.in_create_plan = False

    def visit_FunctionDef(self, node):
        if node.name == "_create_plan":
            self.in_create_plan = True
            self.generic_visit(node)
            self.in_create_plan = False
        else:
            self.generic_visit(node)

    def visit_Dict(self, node):
        if not self.in_create_plan:
            return

        # Look for dictionaries representing steps
        keys = []
        for k in node.keys:
            if isinstance(k, ast.Constant):
                keys.append(k.value)
            elif isinstance(k, ast.Str): # Support older python
                keys.append(k.s)

        if "agent" in keys:
            # We found a step with an 'agent' key!
            # Check its value
            idx = keys.index("agent")
            val_node = node.values[idx]
            
            if isinstance(val_node, (ast.Constant, ast.Str)):
                val = getattr(val_node, 'value', getattr(val_node, 's', None))
                if val in BANNED_AGENT_LITERALS:
                    self.errors.append(
                        f"Line {node.lineno}: Hardcoded agent ID '{val}' found in _create_plan. "
                        f"Use 'requirement' (capability) instead."
                    )
        
        # Also check if it's missing 'requirement'
        if "requirement" not in keys and "agent" in keys:
             self.errors.append(
                f"Line {node.lineno}: Step missing 'requirement' key. Found 'agent' instead."
            )

        self.generic_visit(node)

def test_maestro_is_decoupled():
    """Architecture Guardrail: Ensures Maestro uses capabilities, not hardcoded agent names."""
    if not os.path.exists(MAESTRO_PATH):
        pytest.fail(f"Could not find Maestro source at {MAESTRO_PATH}")

    with open(MAESTRO_PATH, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())

    visitor = MaestroArchVisitor()
    visitor.visit(tree)

    if visitor.errors:
        pytest.fail("Architecture Violation: Maestro is direct-coupling to agent names:\n" + "\n".join(visitor.errors))

if __name__ == "__main__":
    test_maestro_is_decoupled()
    print("SUCCESS: Maestro Architecture Guardrail: PASS")
