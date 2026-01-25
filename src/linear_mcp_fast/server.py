"""
MCP Server for Linear Local Cache.

Provides fast, read-only access to Linear data from local cache.
For write operations, use the official Linear MCP server.
"""

from typing import Any

from mcp.server.fastmcp import FastMCP

from .reader import LinearLocalReader

mcp = FastMCP(
    "Linear Local Cache",
    instructions=(
        "Fast, read-only access to Linear data from the local Linear.app cache on macOS. "
        "Data freshness depends on Linear.app's last sync. "
        "For write operations (comments, updates), use the official Linear MCP server."
    ),
)

_reader: LinearLocalReader | None = None


def get_reader() -> LinearLocalReader:
    """Get or create the LinearLocalReader instance."""
    global _reader
    if _reader is None:
        _reader = LinearLocalReader()
    return _reader


def _parse_datetime(dt_value: Any) -> float | None:
    """Parse a datetime value to Unix timestamp."""
    if dt_value is None:
        return None
    if isinstance(dt_value, (int, float)):
        if dt_value > 1e12:
            return dt_value / 1000
        return dt_value
    if isinstance(dt_value, str):
        from datetime import datetime
        try:
            dt_str = dt_value.replace("Z", "+00:00")
            dt = datetime.fromisoformat(dt_str)
            return dt.timestamp()
        except ValueError:
            return None
    return None


@mcp.tool()
def list_issues(
    assignee: str | None = None,
    team: str | None = None,
    state_type: str | None = None,
    priority: int | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """
    List issues from local cache with optional filters.

    Args:
        assignee: Filter by assignee name (partial match)
        team: Filter by team key (e.g., 'UK')
        state_type: Filter by state type (started, unstarted, completed, canceled, backlog)
        priority: Filter by priority (1=Urgent, 2=High, 3=Medium, 4=Low)
        limit: Maximum number of issues (default 50, max 100)

    Returns:
        Dictionary with issues array and totalCount
    """
    reader = get_reader()
    limit = min(limit, 100)

    assignee_id = None
    if assignee:
        user = reader.find_user(assignee)
        if user:
            assignee_id = user["id"]
        else:
            return {"issues": [], "totalCount": 0}

    team_id = None
    if team:
        team_obj = reader.find_team(team)
        if team_obj:
            team_id = team_obj["id"]
        else:
            return {"issues": [], "totalCount": 0}

    all_issues = sorted(
        reader.issues.values(),
        key=lambda x: (x.get("priority") or 4, x.get("updatedAt") or ""),
    )

    filtered = []
    for issue in all_issues:
        if assignee_id and issue.get("assigneeId") != assignee_id:
            continue
        if team_id and issue.get("teamId") != team_id:
            continue
        if state_type and reader.get_state_type(issue.get("stateId", "")) != state_type:
            continue
        if priority is not None and issue.get("priority") != priority:
            continue
        filtered.append(issue)

    total_count = len(filtered)
    page = filtered[:limit]

    results = []
    for issue in page:
        results.append({
            "identifier": issue.get("identifier"),
            "title": issue.get("title"),
            "priority": issue.get("priority"),
            "state": reader.get_state_name(issue.get("stateId", "")),
            "stateType": reader.get_state_type(issue.get("stateId", "")),
            "assignee": reader.get_user_name(issue.get("assigneeId")),
            "dueDate": issue.get("dueDate"),
        })

    return {"issues": results, "totalCount": total_count}


@mcp.tool()
def get_issue(identifier: str) -> dict[str, Any] | None:
    """
    Get issue details by identifier (e.g., 'UK-55').

    Args:
        identifier: Issue identifier like 'UK-55'

    Returns:
        Issue details with comments, or None if not found
    """
    reader = get_reader()
    issue = reader.get_issue_by_identifier(identifier)

    if not issue:
        return None

    comments = reader.get_comments_for_issue(issue["id"])
    enriched_comments = []
    for comment in comments:
        user = reader.users.get(comment.get("userId", ""), {})
        enriched_comments.append({
            "author": user.get("name", "Unknown"),
            "body": comment.get("body", ""),
            "createdAt": comment.get("createdAt"),
        })

    return {
        "identifier": issue.get("identifier"),
        "title": issue.get("title"),
        "description": issue.get("description"),
        "priority": issue.get("priority"),
        "estimate": issue.get("estimate"),
        "state": reader.get_state_name(issue.get("stateId", "")),
        "stateType": reader.get_state_type(issue.get("stateId", "")),
        "assignee": reader.get_user_name(issue.get("assigneeId")),
        "project": reader.get_project_name(issue.get("projectId")),
        "dueDate": issue.get("dueDate"),
        "createdAt": issue.get("createdAt"),
        "updatedAt": issue.get("updatedAt"),
        "comments": enriched_comments,
        "url": f"https://linear.app/issue/{issue.get('identifier')}",
    }


@mcp.tool()
def search_issues(query: str, limit: int = 20) -> dict[str, Any]:
    """
    Search issues by title.

    Args:
        query: Search query (case-insensitive)
        limit: Maximum results (default 20, max 100)

    Returns:
        Dictionary with matching issues
    """
    reader = get_reader()
    limit = min(limit, 100)
    query_lower = query.lower()

    all_issues = sorted(
        reader.issues.values(),
        key=lambda x: (x.get("priority") or 4, x.get("id", "")),
    )

    filtered = []
    for issue in all_issues:
        title = issue.get("title", "") or ""
        identifier = issue.get("identifier", "") or ""
        if query_lower in title.lower() or query_lower in identifier.lower():
            filtered.append(issue)

    match_count = len(filtered)
    page = filtered[:limit]

    results = []
    for issue in page:
        results.append({
            "identifier": issue.get("identifier"),
            "title": issue.get("title"),
            "state": reader.get_state_name(issue.get("stateId", "")),
            "stateType": reader.get_state_type(issue.get("stateId", "")),
        })

    return {"issues": results, "matchCount": match_count}


@mcp.tool()
def get_my_issues(
    name: str,
    state_type: str | None = None,
    limit: int = 30,
) -> dict[str, Any]:
    """
    Get issues assigned to a user.

    Args:
        name: User name to search for
        state_type: Optional filter (started, unstarted, completed, canceled, backlog)
        limit: Maximum issues (default 30, max 100)

    Returns:
        User info with their issues
    """
    reader = get_reader()
    limit = min(limit, 100)

    user = reader.find_user(name)
    if not user:
        return {"error": f"User '{name}' not found"}

    all_issues = sorted(
        reader.get_issues_for_user(user["id"]),
        key=lambda x: (x.get("priority") or 4, x.get("id", "")),
    )

    counts_by_state: dict[str, int] = {}
    for issue in all_issues:
        issue_state_type = reader.get_state_type(issue.get("stateId", ""))
        counts_by_state[issue_state_type] = counts_by_state.get(issue_state_type, 0) + 1

    if state_type:
        all_issues = [
            i for i in all_issues
            if reader.get_state_type(i.get("stateId", "")) == state_type
        ]

    page = all_issues[:limit]

    results = []
    for issue in page:
        results.append({
            "identifier": issue.get("identifier"),
            "title": issue.get("title"),
            "priority": issue.get("priority"),
            "state": reader.get_state_name(issue.get("stateId", "")),
            "stateType": reader.get_state_type(issue.get("stateId", "")),
            "dueDate": issue.get("dueDate"),
        })

    return {
        "user": {"name": user.get("name"), "email": user.get("email")},
        "totalIssues": sum(counts_by_state.values()),
        "countsByState": counts_by_state,
        "issues": results,
    }


@mcp.tool()
def list_teams() -> list[dict[str, Any]]:
    """
    List all teams with issue counts.

    Returns:
        List of teams
    """
    reader = get_reader()
    results = []

    for team in reader.teams.values():
        issue_count = sum(
            1 for i in reader.issues.values() if i.get("teamId") == team["id"]
        )
        results.append({
            "key": team.get("key"),
            "name": team.get("name"),
            "issueCount": issue_count,
        })

    results.sort(key=lambda x: x.get("key", ""))
    return results


@mcp.tool()
def list_projects(team: str | None = None) -> list[dict[str, Any]]:
    """
    List all projects with issue counts.

    Args:
        team: Optional team key to filter

    Returns:
        List of projects
    """
    reader = get_reader()

    team_id = None
    if team:
        team_obj = reader.find_team(team)
        if team_obj:
            team_id = team_obj["id"]
        else:
            return []

    results = []
    for project in reader.projects.values():
        if team_id and team_id not in project.get("teamIds", []):
            continue

        issue_count = sum(
            1 for i in reader.issues.values() if i.get("projectId") == project["id"]
        )

        results.append({
            "name": project.get("name"),
            "state": project.get("state"),
            "issueCount": issue_count,
            "startDate": project.get("startDate"),
            "targetDate": project.get("targetDate"),
        })

    results.sort(key=lambda x: x.get("name", "") or "")
    return results


@mcp.tool()
def get_summary() -> dict[str, Any]:
    """
    Get a summary of local cache data.

    Returns:
        Counts of teams, users, issues, projects, comments
    """
    reader = get_reader()
    summary = reader.get_summary()

    # Add state breakdown
    state_counts: dict[str, int] = {}
    for issue in reader.issues.values():
        state_type = reader.get_state_type(issue.get("stateId", ""))
        state_counts[state_type] = state_counts.get(state_type, 0) + 1

    summary["issuesByState"] = state_counts
    return summary


def main():
    """Run the MCP server."""
    mcp.run()
