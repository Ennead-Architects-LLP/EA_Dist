"""Revit-specific MCP tool definitions."""

from __future__ import annotations

from fastmcp import FastMCP


def register_revit_tools(mcp: FastMCP, adapter):
    """Register Revit-only tools on *mcp*.

    The *adapter* must be a ``RevitAdapter`` (or compatible) instance that
    exposes the Revit-specific helper methods.
    """

    @mcp.tool()
    def list_levels() -> list[dict]:
        """List all levels defined in the active Revit model."""
        return adapter.list_levels()

    @mcp.tool()
    def list_views() -> list[dict]:
        """List all views in the active Revit model."""
        return adapter.list_views()

    @mcp.tool()
    def list_families(category: str = "") -> list[dict]:
        """List loaded families in the active Revit model, optionally filtered by category.

        Args:
            category: Revit category name to filter by (e.g. "Doors"). Leave empty for all families.
        """
        return adapter.list_families(category=category or None)

    @mcp.tool()
    def create_sheet(sheet_number: str, sheet_name: str, title_block_name: str = "") -> dict:
        """Create a new sheet in the active Revit document.

        Args:
            sheet_number: The sheet number (e.g. "A101").
            sheet_name: Display name for the sheet.
            title_block_name: Name of the title block family to use. Leave empty for the default.
        """
        return adapter.create_sheet(
            sheet_number,
            sheet_name,
            title_block_name=title_block_name or None,
        )

    @mcp.tool()
    def create_view(view_type: str, level_name: str = "", name: str = "") -> dict:
        """Create a new view of the specified type in the active Revit document.

        Args:
            view_type: Type of view to create (e.g. "FloorPlan", "CeilingPlan", "Section").
            level_name: Level to associate the view with. Leave empty if not applicable.
            name: Optional custom name for the new view.
        """
        return adapter.create_view(
            view_type,
            level_name=level_name or None,
            name=name or None,
        )

    @mcp.tool()
    def place_family(
        family_name: str,
        type_name: str,
        x: float,
        y: float,
        z: float,
        level_name: str = "",
    ) -> dict:
        """Place a family instance at the given coordinates in the active Revit model.

        Args:
            family_name: Name of the loaded family.
            type_name: Family type to place.
            x: X coordinate in project units.
            y: Y coordinate in project units.
            z: Z coordinate in project units.
            level_name: Level to place the instance on. Leave empty for automatic level detection.
        """
        return adapter.place_family(
            family_name,
            type_name,
            x,
            y,
            z,
            level_name=level_name or None,
        )

    @mcp.tool()
    def sync_with_central() -> dict:
        """Synchronize the local Revit model with central. This saves local changes to the central model."""
        return adapter.sync_with_central()
