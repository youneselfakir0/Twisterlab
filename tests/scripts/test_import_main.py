import importlib
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

try:
    m = importlib.import_module("twisterlab.api.main")
    print("Imported main OK")
except Exception:
    traceback.print_exc()
try:
    mod = importlib.import_module("twisterlab.api.routes.system")
    print("system module file:", mod.__file__)
    with open(mod.__file__, "r", encoding="utf-8") as fh:  # type: ignore
        for i, line in enumerate(fh):
            if i > 40:
                break
            print(i + 1, line.rstrip())
except Exception:
    traceback.print_exc()
try:
    pkg = importlib.import_module("twisterlab.api")
    print(
        "twisterlab.api", getattr(pkg, "__file__", None), getattr(pkg, "__path__", None)
    )
except Exception:
    traceback.print_exc()
