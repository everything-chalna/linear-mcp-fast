"""
Unified MCP server for Linear local-fast reads + official MCP fallback/writes.
"""

from __future__ import annotations

import atexit
from typing import Any

from mcp.server.fastmcp import FastMCP

from .official_session import OfficialMcpSessionManager
from .reader import LinearLocalReader
from .router import ToolRouter

mcp = FastMCP(
    "OhMyLinearMCP (Fast + Official)",
    instructions=(
        "OhMyLinearMCP unified server. "
        "Read operations are served from local Linear.app cache first for speed, "
        "and automatically fall back to official Linear MCP when local cache is "
        "unsupported, degraded, or stale-sensitive. "
        "Write operations use official Linear MCP."
    ),
)

_reader: LinearLocalReader | None = None
_official: OfficialMcpSessionManager | None = None
_router: ToolRouter | None = None


def get_reader() -> LinearLocalReader:
    global _reader
    if _reader is None:
        _reader = LinearLocalReader()
    return _reader


def get_official() -> OfficialMcpSessionManager:
    global _official
    if _official is None:
        _official = OfficialMcpSessionManager()
    return _official


def get_router() -> ToolRouter:
    global _router
    if _router is None:
        _router = ToolRouter(get_reader(), get_official())
    return _router


def _shutdown() -> None:
    if _official is not None:
        _official.close()


atexit.register(_shutdown)


def _read(tool_name: str, **kwargs: Any) -> Any:
    return get_router().call_read(tool_name, kwargs)


@mcp.tool()
def list_issues(
    assignee: str | None = None,
    team: str | None = None,
    state: str | None = None,
    priority: int | None = None,
    project: str | None = None,
    query: str | None = None,
    orderBy: str = "updatedAt",
    limit: int = 50,
) -> dict[str, Any]:
    return _read(
        "list_issues",
        assignee=assignee,
        team=team,
        state=state,
        priority=priority,
        project=project,
        query=query,
        orderBy=orderBy,
        limit=limit,
    )


@mcp.tool()
def get_issue(id: str) -> dict[str, Any] | None:
    return _read("get_issue", id=id)


@mcp.tool()
def list_teams() -> list[dict[str, Any]]:
    return _read("list_teams")


@mcp.tool()
def list_projects(team: str | None = None) -> list[dict[str, Any]]:
    return _read("list_projects", team=team)


@mcp.tool()
def get_team(query: str) -> dict[str, Any] | None:
    return _read("get_team", query=query)


@mcp.tool()
def get_project(query: str) -> dict[str, Any] | None:
    return _read("get_project", query=query)


@mcp.tool()
def list_users() -> list[dict[str, Any]]:
    return _read("list_users")


@mcp.tool()
def get_user(query: str) -> dict[str, Any] | None:
    return _read("get_user", query=query)


@mcp.tool()
def list_issue_statuses(team: str) -> list[dict[str, Any]]:
    return _read("list_issue_statuses", team=team)


@mcp.tool()
def get_issue_status(
    team: str,
    name: str | None = None,
    id: str | None = None,
) -> dict[str, Any] | None:
    return _read("get_issue_status", team=team, name=name, id=id)


@mcp.tool()
def list_comments(issueId: str) -> list[dict[str, Any]]:
    return _read("list_comments", issueId=issueId)


@mcp.tool()
def list_issue_labels(team: str | None = None) -> list[dict[str, Any]]:
    return _read("list_issue_labels", team=team)


@mcp.tool()
def list_initiatives() -> list[dict[str, Any]]:
    return _read("list_initiatives")


@mcp.tool()
def get_initiative(query: str) -> dict[str, Any] | None:
    return _read("get_initiative", query=query)


@mcp.tool()
def list_cycles(teamId: str) -> list[dict[str, Any]]:
    return _read("list_cycles", teamId=teamId)


@mcp.tool()
def list_documents(project: str | None = None) -> list[dict[str, Any]]:
    return _read("list_documents", project=project)


@mcp.tool()
def get_document(id: str) -> dict[str, Any] | None:
    return _read("get_document", id=id)


@mcp.tool()
def list_milestones(project: str) -> list[dict[str, Any]]:
    return _read("list_milestones", project=project)


@mcp.tool()
def get_milestone(project: str, query: str) -> dict[str, Any] | None:
    return _read("get_milestone", project=project, query=query)


@mcp.tool()
def get_status_updates(
    type: str,
    id: str | None = None,
    project: str | None = None,
    initiative: str | None = None,
    user: str | None = None,
    includeArchived: bool | None = None,
    orderBy: str = "createdAt",
    limit: int = 50,
    cursor: str | None = None,
    createdAt: str | None = None,
    updatedAt: str | None = None,
) -> dict[str, Any] | None:
    return _read(
        "get_status_updates",
        type=type,
        id=id,
        project=project,
        initiative=initiative,
        user=user,
        includeArchived=includeArchived,
        orderBy=orderBy,
        limit=limit,
        cursor=cursor,
        createdAt=createdAt,
        updatedAt=updatedAt,
    )


@mcp.tool()
def list_project_updates(project: str) -> list[dict[str, Any]]:
    return _read("list_project_updates", project=project)


@mcp.tool()
def official_call_tool(name: str, args: dict[str, Any] | None = None) -> Any:
    """
    Call any official Linear MCP tool by name.

    Use this for write operations and any official-only tools.
    """
    return get_router().call_official(name, args or {})


@mcp.tool()
def list_official_tools() -> list[str]:
    """List tool names currently available from official Linear MCP."""
    return get_official().list_tools()


@mcp.tool()
def refresh_cache() -> dict[str, Any]:
    """Force reload of local cache and return health state."""
    return get_router().refresh_local_cache()


@mcp.tool()
def get_cache_health() -> dict[str, Any]:
    """Return local+official health and coherence-window state."""
    return get_router().get_health()


def main() -> None:
    mcp.run()
