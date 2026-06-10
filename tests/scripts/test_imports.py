import importlib
import traceback


def main():
    modules = [
        "twisterlab.api.main",
        "twisterlab.api.routes.agents",
        "twisterlab.api.routes.browser",
        "twisterlab.agents.real.browser_screenshot_agent",
    ]
    for m in modules:
        print("Importing", m)
        try:
            importlib.import_module(m)
            print("OK")
        except Exception:
            traceback.print_exc()


if __name__ == "__main__":
    main()
