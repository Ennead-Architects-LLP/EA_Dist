"""Common MCP tool definitions shared across all application adapters."""

from __future__ import annotations

import base64
import json

from fastmcp import FastMCP

from ..adapter import AppAdapter


def register_common_tools(mcp: FastMCP, adapter: AppAdapter):
    """Register application-agnostic tools on *mcp*."""

    @mcp.tool()
    def get_app_status() -> dict:
        """Get the connected application's status: app name, version, active document, and connection health."""
        return adapter.get_status()

    @mcp.tool()
    def get_model_info() -> dict:
        """Get high-level information about the active model or document, such as file path, units, and element counts."""
        return adapter.get_model_info()

    @mcp.tool()
    def list_elements(category: str, filters: str = "") -> list[dict]:
        """List elements of the given category in the active model.

        Args:
            category: Element category to query (e.g. "Walls", "Doors").
            filters: Optional JSON object of additional filter key/value pairs.
                     Pass an empty string for no filtering.
        """
        parsed_filters: dict | None = None
        if filters:
            parsed_filters = json.loads(filters)
        return adapter.list_elements(category, filters=parsed_filters)

    @mcp.tool()
    def get_element_parameters(element_id: str) -> dict:
        """Return all parameters for a single element identified by its ID."""
        return adapter.get_element_parameters(element_id)

    @mcp.tool()
    def set_element_parameter(element_id: str, param_name: str, value: str) -> dict:
        """Set a parameter on an element and return the updated state.

        Args:
            element_id: The unique identifier of the element.
            param_name: Name of the parameter to set.
            value: New value for the parameter (always passed as a string).
        """
        return adapter.set_element_parameter(element_id, param_name, value)

    @mcp.tool()
    def execute_code(code: str) -> dict:
        """Execute arbitrary code inside the connected application and return stdout, stderr, and error info.

        WARNING: This tool runs code directly in the host application process.
        It can modify the model, change application state, or cause data loss.
        Use with extreme caution and always review the code before execution.

        Args:
            code: Source code string to execute in the host application's scripting environment.
        """
        return adapter.execute_code(code)

    @mcp.tool()
    def get_view_image(view_name: str = "") -> str:
        """Capture a PNG screenshot of the specified view (or the active view) and return it as a base64-encoded string.

        Args:
            view_name: Name of the view to capture. Leave empty for the active view.
        """
        image_bytes = adapter.get_view_image(view_name or None)
        return base64.b64encode(image_bytes).decode("ascii")

    @mcp.tool()
    def list_enneadtab_tools() -> list[dict]:
        """List all available EnneadTab tool modules and their descriptions."""
        return adapter.list_enneadtab_tools()

    @mcp.tool()
    def run_enneadtab_tool(module: str, function: str, args: str = "{}") -> dict:
        """Invoke an EnneadTab tool function by module and function name.

        Args:
            module: The EnneadTab module name (e.g. "COLOR").
            function: The function to call within the module.
            args: JSON object of keyword arguments to pass to the function.
                  Defaults to empty object.
        """
        parsed_args: dict | None = None
        if args and args != "{}":
            parsed_args = json.loads(args)
        return adapter.run_enneadtab_tool(module, function, args=parsed_args)
