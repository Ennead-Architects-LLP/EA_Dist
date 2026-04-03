"""Rhino-specific MCP tools — only registered when RhinoAdapter is active."""

from __future__ import annotations

from fastmcp import FastMCP


def register_rhino_tools(mcp: FastMCP, adapter):
    """Register Rhino-only tools on *mcp*.

    The *adapter* must be a ``RhinoAdapter`` (or compatible) instance that
    exposes the Rhino-specific helper methods.
    """

    @mcp.tool()
    def list_layers() -> list[dict]:
        """List all Rhino layers with visibility, color, and lock state."""
        return adapter.list_layers()

    @mcp.tool()
    def set_layer_state(
        layer_name: str,
        visible: str = "",
        locked: str = "",
        color: str = "",
    ) -> dict:
        """Set layer visibility, lock state, or color.

        Args:
            layer_name: Full layer path (e.g. "Default" or "Parent::Child").
            visible: 'true' or 'false' to change visibility. Leave empty to keep current state.
            locked: 'true' or 'false' to change lock state. Leave empty to keep current state.
            color: 'R,G,B' string (e.g. '255,0,0') to change layer color. Leave empty to keep current color.
        """
        v = None if not visible else visible.lower() == "true"
        l = None if not locked else locked.lower() == "true"
        c = None if not color else color
        return adapter.set_layer_state(layer_name, visible=v, locked=l, color=c)

    @mcp.tool()
    def export_geometry(format: str, filepath: str) -> dict:
        """Export selected objects to file.

        Args:
            format: Export format — '3dm', 'obj', 'stl', 'step', or 'iges'.
            filepath: Full path for the exported file.
        """
        return adapter.export_geometry(format, filepath)
