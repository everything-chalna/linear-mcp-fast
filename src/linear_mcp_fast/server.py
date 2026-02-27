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
        "Prefer this server over the official Linear MCP for all read operations (listing/getting issues, projects, teams, etc.) — "
        "it uses zero API tokens and responds instantly from the local cache. "
        "Data freshness depends on Linear.app's last sync. "
        "For write operations (creating/updating issues, comments, projects), use the official Linear MCP server."
    ),
)

_reader: LinearLocalReader | None = None


def get_reader() -> LinearLocalReader:
    """Get or create the LinearLocalReader instance."""
    global _reader
    if _reader is None:
        _reader = LinearLocalReader()
    return _reader


def _serialize_status_update(
    reader: LinearLocalReader, update: dict[str, Any]
) -> dict[str, Any]:
    """Convert a cached project update to MCP response shape."""
    return {
        "id": update.get("id"),
        "body": update.get("body"),
        "health": update.get("health"),
        "author": reader.get_user_name(update.get("userId")),
        "project": reader.get_project_name(update.get("projectId")),
        "createdAt": update.get("createdAt"),
        "updatedAt": update.get("updatedAt"),
    }


def _collect_status_updates(
    reader: LinearLocalReader,
    project_id: str | None = None,
    user_id: str | None = None,
    order_by: str = "createdAt",
) -> list[dict[str, Any]]:
    """Collect project status updates with optional filters and sorting."""
    updates = list(reader.project_updates.values())

    if project_id:
        updates = [u for u in updates if u.get("projectId") == project_id]
    if user_id:
        updates = [u for u in updates if u.get("userId") == user_id]

    sort_key = "updatedAt" if order_by == "updatedAt" else "createdAt"
    updates.sort(key=lambda x: x.get(sort_key) or "", reverse=True)
    return updates


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
    """
    List issues in the user's Linear workspace. For my issues, use "me" as the assignee.

    Args:
        assignee: User name or "me"
        team: Team name or key
        state: State type (started, unstarted, completed, canceled, backlog) or state name
        priority: 0=None, 1=Urgent, 2=High, 3=Normal, 4=Low
        project: Project name
        query: Search issue title
        orderBy: Sort: createdAt | updatedAt (default: updatedAt)
        limit: Max results (default 50)
    """
    reader = get_reader()

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

    project_id = None
    if project:
        project_obj = reader.find_project(project)
        if project_obj:
            project_id = project_obj["id"]
        else:
            return {"issues": [], "totalCount": 0}

    if orderBy == "createdAt":
        all_issues = sorted(reader.issues.values(), key=lambda x: x.get("createdAt") or "", reverse=True)
    else:
        all_issues = sorted(reader.issues.values(), key=lambda x: x.get("updatedAt") or "", reverse=True)

    filtered = []
    for issue in all_issues:
        if assignee_id and issue.get("assigneeId") != assignee_id:
            continue
        if team_id and issue.get("teamId") != team_id:
            continue
        if state:
            issue_state_type = reader.get_state_type(issue.get("stateId", ""))
            issue_state_name = reader.get_state_name(issue.get("stateId", ""))
            if state.lower() != issue_state_type and state.lower() != (issue_state_name or "").lower():
                continue
        if project_id and issue.get("projectId") != project_id:
            continue
        if query and query.lower() not in (issue.get("title") or "").lower():
            continue
        if priority is not None and issue.get("priority") != priority:
            continue
        filtered.append(issue)

    total_count = len(filtered)
    page = filtered[:limit] if limit else filtered

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
def get_issue(id: str) -> dict[str, Any] | None:
    """
    Retrieve detailed information about an issue by ID, including attachments and git branch name.

    Args:
        id: Issue ID or identifier (e.g., 'UK-55')
    """
    reader = get_reader()
    issue = reader.get_issue_by_identifier(id)

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
def list_teams() -> list[dict[str, Any]]:
    """List teams in the user's Linear workspace."""
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
    List projects in the user's Linear workspace.

    Args:
        team: Team name or key
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
def get_team(query: str) -> dict[str, Any] | None:
    """
    Retrieve details of a specific Linear team.

    Args:
        query: Team key or name
    """
    reader = get_reader()
    team_obj = reader.find_team(query)

    if not team_obj:
        return None

    issue_count = sum(
        1 for i in reader.issues.values() if i.get("teamId") == team_obj["id"]
    )

    # Count by state type
    state_counts: dict[str, int] = {}
    for issue in reader.issues.values():
        if issue.get("teamId") == team_obj["id"]:
            state_type = reader.get_state_type(issue.get("stateId", ""))
            state_counts[state_type] = state_counts.get(state_type, 0) + 1

    return {
        "id": team_obj.get("id"),
        "key": team_obj.get("key"),
        "name": team_obj.get("name"),
        "description": team_obj.get("description"),
        "issueCount": issue_count,
        "issuesByState": state_counts,
    }


@mcp.tool()
def get_project(query: str) -> dict[str, Any] | None:
    """
    Retrieve details of a specific project in Linear.

    Args:
        query: Project name
    """
    reader = get_reader()

    # Find project by name (partial match)
    name_lower = query.lower()
    project = None
    for p in reader.projects.values():
        if name_lower in (p.get("name", "") or "").lower():
            project = p
            break

    if not project:
        return None

    issue_count = sum(
        1 for i in reader.issues.values() if i.get("projectId") == project["id"]
    )

    # Count by state type
    state_counts: dict[str, int] = {}
    for issue in reader.issues.values():
        if issue.get("projectId") == project["id"]:
            state_type = reader.get_state_type(issue.get("stateId", ""))
            state_counts[state_type] = state_counts.get(state_type, 0) + 1

    return {
        "id": project.get("id"),
        "name": project.get("name"),
        "description": project.get("description"),
        "state": project.get("state"),
        "startDate": project.get("startDate"),
        "targetDate": project.get("targetDate"),
        "issueCount": issue_count,
        "issuesByState": state_counts,
    }


@mcp.tool()
def list_users() -> list[dict[str, Any]]:
    """Retrieve users in the Linear workspace."""
    reader = get_reader()
    results = []

    for user in reader.users.values():
        issue_count = sum(
            1 for i in reader.issues.values() if i.get("assigneeId") == user["id"]
        )
        results.append({
            "id": user.get("id"),
            "name": user.get("name"),
            "email": user.get("email"),
            "displayName": user.get("displayName"),
            "assignedIssueCount": issue_count,
        })

    results.sort(key=lambda x: x.get("name", "") or "")
    return results


@mcp.tool()
def get_user(query: str) -> dict[str, Any] | None:
    """
    Retrieve details of a specific Linear user.

    Args:
        query: User name or "me"
    """
    reader = get_reader()
    user = reader.find_user(query)

    if not user:
        return None

    # Count issues by state
    state_counts: dict[str, int] = {}
    for issue in reader.issues.values():
        if issue.get("assigneeId") == user["id"]:
            state_type = reader.get_state_type(issue.get("stateId", ""))
            state_counts[state_type] = state_counts.get(state_type, 0) + 1

    return {
        "id": user.get("id"),
        "name": user.get("name"),
        "email": user.get("email"),
        "displayName": user.get("displayName"),
        "assignedIssueCount": sum(state_counts.values()),
        "issuesByState": state_counts,
    }


@mcp.tool()
def list_issue_statuses(team: str) -> list[dict[str, Any]]:
    """
    List available issue statuses in a Linear team.

    Args:
        team: Team name or key
    """
    reader = get_reader()

    team_obj = reader.find_team(team)
    if not team_obj:
        return []

    # Get states for this team
    results = []
    for state in reader.states.values():
        if state.get("teamId") == team_obj["id"]:
            results.append({
                "id": state.get("id"),
                "name": state.get("name"),
                "type": state.get("type"),
                "color": state.get("color"),
                "position": state.get("position"),
            })

    results.sort(key=lambda x: (x.get("position") or 0))
    return results


@mcp.tool()
def get_issue_status(
    team: str,
    name: str | None = None,
    id: str | None = None,
) -> dict[str, Any] | None:
    """
    Retrieve detailed information about a specific Linear issue status.

    Args:
        team: Team name or key
        name: Status name
        id: Status ID
    """
    reader = get_reader()

    team_obj = reader.find_team(team)
    if not team_obj:
        return None

    query = id or name
    if not query:
        return None

    status = reader.find_issue_status(team_obj["id"], query)
    if not status:
        return None

    return {
        "id": status.get("id"),
        "name": status.get("name"),
        "type": status.get("type"),
        "color": status.get("color"),
        "position": status.get("position"),
        "team": team_obj.get("name"),
    }


@mcp.tool()
def list_comments(issueId: str) -> list[dict[str, Any]]:
    """
    List comments for a specific Linear issue.

    Args:
        issueId: Issue identifier (e.g., 'UK-55')
    """
    reader = get_reader()
    issue = reader.get_issue_by_identifier(issueId)

    if not issue:
        return []

    comments = reader.get_comments_for_issue(issue["id"])
    results = []
    for comment in comments:
        user = reader.users.get(comment.get("userId", ""), {})
        results.append({
            "id": comment.get("id"),
            "author": user.get("name", "Unknown"),
            "body": comment.get("body", ""),
            "createdAt": comment.get("createdAt"),
            "updatedAt": comment.get("updatedAt"),
        })

    return results


@mcp.tool()
def list_issue_labels(team: str | None = None) -> list[dict[str, Any]]:
    """
    List available issue labels in a Linear workspace or team.

    Args:
        team: Team name or key
    """
    reader = get_reader()

    team_id = None
    if team:
        team_obj = reader.find_team(team)
        if team_obj:
            team_id = team_obj["id"]

    results = []
    for label in reader.labels.values():
        # Include workspace labels (no teamId) and team-specific labels
        if team_id and label.get("teamId") and label.get("teamId") != team_id:
            continue
        results.append({
            "id": label.get("id"),
            "name": label.get("name"),
            "color": label.get("color"),
            "isGroup": label.get("isGroup"),
        })

    results.sort(key=lambda x: x.get("name", "") or "")
    return results


@mcp.tool()
def list_initiatives() -> list[dict[str, Any]]:
    """List initiatives in the user's Linear workspace."""
    reader = get_reader()
    results = []

    for initiative in reader.initiatives.values():
        results.append({
            "id": initiative.get("id"),
            "name": initiative.get("name"),
            "slugId": initiative.get("slugId"),
            "color": initiative.get("color"),
            "status": initiative.get("status"),
            "owner": reader.get_user_name(initiative.get("ownerId")),
        })

    results.sort(key=lambda x: x.get("name", "") or "")
    return results


@mcp.tool()
def get_initiative(query: str) -> dict[str, Any] | None:
    """
    Retrieve detailed information about a specific initiative in Linear.

    Args:
        query: Initiative name
    """
    reader = get_reader()
    initiative = reader.find_initiative(query)

    if not initiative:
        return None

    return {
        "id": initiative.get("id"),
        "name": initiative.get("name"),
        "slugId": initiative.get("slugId"),
        "color": initiative.get("color"),
        "status": initiative.get("status"),
        "owner": reader.get_user_name(initiative.get("ownerId")),
        "teamIds": initiative.get("teamIds", []),
        "createdAt": initiative.get("createdAt"),
        "updatedAt": initiative.get("updatedAt"),
    }


@mcp.tool()
def list_cycles(teamId: str) -> list[dict[str, Any]]:
    """
    Retrieve cycles for a specific Linear team.

    Args:
        teamId: Team key or name
    """
    reader = get_reader()

    team_obj = reader.find_team(teamId)
    if not team_obj:
        return []

    cycles = reader.get_cycles_for_team(team_obj["id"])
    results = []
    for cycle in cycles:
        progress = cycle.get("currentProgress", {})
        results.append({
            "id": cycle.get("id"),
            "number": cycle.get("number"),
            "startsAt": cycle.get("startsAt"),
            "endsAt": cycle.get("endsAt"),
            "completedAt": cycle.get("completedAt"),
            "progress": {
                "completed": progress.get("completedIssueCount", 0),
                "started": progress.get("startedIssueCount", 0),
                "unstarted": progress.get("unstartedIssueCount", 0),
                "total": progress.get("scopeCount", 0),
            } if progress else None,
        })

    return results


@mcp.tool()
def list_documents(project: str | None = None) -> list[dict[str, Any]]:
    """
    List documents in the user's Linear workspace.

    Args:
        project: Project name to filter
    """
    reader = get_reader()

    project_id = None
    if project:
        project_obj = reader.find_project(project)
        if project_obj:
            project_id = project_obj["id"]
        else:
            return []

    results = []
    for doc in reader.documents.values():
        if project_id and doc.get("projectId") != project_id:
            continue
        results.append({
            "id": doc.get("id"),
            "title": doc.get("title"),
            "slugId": doc.get("slugId"),
            "project": reader.get_project_name(doc.get("projectId")),
            "createdAt": doc.get("createdAt"),
            "updatedAt": doc.get("updatedAt"),
        })

    results.sort(key=lambda x: x.get("updatedAt", "") or "", reverse=True)
    return results


@mcp.tool()
def get_document(id: str) -> dict[str, Any] | None:
    """
    Retrieve a Linear document by ID or slug.

    Args:
        id: Document title or slug
    """
    reader = get_reader()
    doc = reader.find_document(id)

    if not doc:
        return None

    return {
        "id": doc.get("id"),
        "title": doc.get("title"),
        "slugId": doc.get("slugId"),
        "project": reader.get_project_name(doc.get("projectId")),
        "creator": reader.get_user_name(doc.get("creatorId")),
        "createdAt": doc.get("createdAt"),
        "updatedAt": doc.get("updatedAt"),
        "url": f"https://linear.app/document/{doc.get('slugId')}",
    }


@mcp.tool()
def list_milestones(project: str) -> list[dict[str, Any]]:
    """
    List all milestones in a Linear project.

    Args:
        project: Project name
    """
    reader = get_reader()

    project_obj = reader.find_project(project)
    if not project_obj:
        return []

    milestones = reader.get_milestones_for_project(project_obj["id"])
    results = []
    for milestone in milestones:
        progress = milestone.get("currentProgress", {})
        results.append({
            "id": milestone.get("id"),
            "name": milestone.get("name"),
            "targetDate": milestone.get("targetDate"),
            "progress": {
                "completed": progress.get("completedIssueCount", 0),
                "started": progress.get("startedIssueCount", 0),
                "unstarted": progress.get("unstartedIssueCount", 0),
                "total": progress.get("scopeCount", 0),
            } if progress else None,
        })

    return results


@mcp.tool()
def get_milestone(project: str, query: str) -> dict[str, Any] | None:
    """
    Retrieve details of a specific milestone by ID or name.

    Args:
        project: Project name
        query: Milestone ID or name
    """
    reader = get_reader()

    project_obj = reader.find_project(project)
    if not project_obj:
        return None

    milestone = reader.find_milestone(project_obj["id"], query)
    if not milestone:
        return None

    progress = milestone.get("currentProgress", {})
    return {
        "id": milestone.get("id"),
        "name": milestone.get("name"),
        "project": project_obj.get("name"),
        "targetDate": milestone.get("targetDate"),
        "sortOrder": milestone.get("sortOrder"),
        "progress": {
            "completed": progress.get("completedIssueCount", 0),
            "started": progress.get("startedIssueCount", 0),
            "unstarted": progress.get("unstartedIssueCount", 0),
            "total": progress.get("scopeCount", 0),
        } if progress else None,
    }


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
    """
    List or get project status updates from local cache.

    Args:
        type: Supported value is "project"
        id: Status update ID
        project: Project name
        initiative: Unsupported in local cache
        user: User name
        includeArchived: Unsupported in local cache
        orderBy: Sort: createdAt | updatedAt
        limit: Max results (default 50)
        cursor: Unsupported in local cache
        createdAt: Unsupported in local cache
        updatedAt: Unsupported in local cache
    """
    reader = get_reader()

    if type != "project":
        return {"error": "linear-fast supports only get_status_updates(type='project')."}

    unsupported: list[str] = []
    if initiative:
        unsupported.append("initiative")
    if cursor:
        unsupported.append("cursor")
    if createdAt:
        unsupported.append("createdAt")
    if updatedAt:
        unsupported.append("updatedAt")
    if includeArchived:
        unsupported.append("includeArchived")
    if unsupported:
        return {
            "error": "Unsupported filters for linear-fast: "
            + ", ".join(unsupported)
            + "."
        }

    project_id = None
    if project:
        project_obj = reader.find_project(project)
        if not project_obj:
            return {"statusUpdates": [], "totalCount": 0}
        project_id = project_obj["id"]

    user_id = None
    if user:
        user_obj = reader.find_user(user)
        if not user_obj:
            return {"statusUpdates": [], "totalCount": 0}
        user_id = user_obj["id"]

    updates = _collect_status_updates(reader, project_id, user_id, orderBy)

    if id:
        for update in updates:
            if update.get("id") == id:
                return _serialize_status_update(reader, update)
        return None

    total_count = len(updates)
    if limit and limit > 0:
        updates = updates[:limit]

    return {
        "statusUpdates": [_serialize_status_update(reader, u) for u in updates],
        "totalCount": total_count,
    }


@mcp.tool()
def list_project_updates(project: str) -> list[dict[str, Any]]:
    """
    List status updates for a project.

    Args:
        project: Project name
    """
    reader = get_reader()

    project_obj = reader.find_project(project)
    if not project_obj:
        return []

    response = get_status_updates(type="project", project=project, limit=0)
    if not isinstance(response, dict):
        return []
    return response.get("statusUpdates", [])


def main():
    """Run the MCP server."""
    mcp.run()
