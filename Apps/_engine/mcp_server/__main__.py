"""EnneadTab MCP Server entry point.

Usage:
    python -m mcp_server --app revit
    python -m mcp_server              # auto-detect
"""

import argparse
import sys

from fastmcp import FastMCP

from .error_reporter import report_error
from .revit_adapter import RevitAdapter
from .rhino_adapter import RhinoAdapter
from .tools.common import register_common_tools
from .tools.revit_tools import register_revit_tools
from .tools.rhino_tools import register_rhino_tools


def detect_app() -> str:
    """Probe localhost ports to detect which app is running."""
    import httpx
    try:
        resp = httpx.get("http://localhost:48884/enneadtab/status/", timeout=3.0)
        if resp.status_code == 200:
            return "revit"
    except Exception:
        pass
    # Try Rhino (RPC server on :48885)
    try:
        resp = httpx.get("http://localhost:48885/enneadtab/status/", timeout=3.0)
        if resp.status_code == 200:
            return "rhino"
    except Exception:
        pass
    print("ERROR: No supported app detected.", file=sys.stderr)
    print("Is Revit (port 48884) or Rhino (port 48885) running with the RPC server enabled?", file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="EnneadTab MCP Server")
    parser.add_argument("--app", choices=["revit", "rhino"], default=None,
                        help="Target application (default: auto-detect)")
    args = parser.parse_args()

    app = args.app or detect_app()

    mcp = FastMCP(
        "EnneadTab",
        description="EnneadTab MCP Server — control Revit or Rhino from Claude Code. "
                    "Query models, modify parameters, execute code, and run EnneadTab tools.",
    )

    if app == "revit":
        try:
            adapter = RevitAdapter()
            adapter.get_status()  # verify connection
        except Exception as e:
            msg = "Failed to connect to Revit: {}".format(e)
            report_error(msg, "startup", {"adapter": "revit"})
            print("ERROR: {}".format(msg), file=sys.stderr)
            sys.exit(1)

        register_common_tools(mcp, adapter)
        register_revit_tools(mcp, adapter)
        print("EnneadTab MCP Server started (app=revit)", file=sys.stderr)
    elif app == "rhino":
        try:
            adapter = RhinoAdapter()
            adapter.get_status()
        except Exception as e:
            msg = "Failed to connect to Rhino: {}".format(e)
            report_error(msg, "startup", {"adapter": "rhino"})
            print("ERROR: {}".format(msg), file=sys.stderr)
            sys.exit(1)

        register_common_tools(mcp, adapter)
        register_rhino_tools(mcp, adapter)
        print("EnneadTab MCP Server started (app=rhino)", file=sys.stderr)
    else:
        print("ERROR: Unknown app: {}".format(app), file=sys.stderr)
        sys.exit(1)

    mcp.run()


if __name__ == "__main__":
    main()
