"""Shared MCP tool annotation helpers.

This module centralizes FastMCP annotation hints so tool definitions can stay
concise and consistent across domains.
"""

from mcp.types import ToolAnnotations


def readonly_annotations(title: str) -> ToolAnnotations:
    """Build annotations for read-only MCP tools.

    Args:
        title: Human-friendly tool title for MCP clients.

    Returns:
        ToolAnnotations: Annotations suitable for FastMCP's ``@tool`` decorator.

    """
    return ToolAnnotations(
        title=title,
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    )


def mutating_annotations(
    title: str,
    *,
    destructive: bool = False,
    idempotent: bool = False,
) -> ToolAnnotations:
    """Build annotations for mutating MCP tools.

    Args:
        title: Human-friendly tool title for MCP clients.
        destructive: Whether the tool performs destructive changes.
        idempotent: Whether repeated identical calls have no additional effect.

    Returns:
        ToolAnnotations: Annotations suitable for FastMCP's ``@tool`` decorator.

    """
    return ToolAnnotations(
        title=title,
        readOnlyHint=False,
        destructiveHint=destructive,
        idempotentHint=idempotent,
        openWorldHint=False,
    )
