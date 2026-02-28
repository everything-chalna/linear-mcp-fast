"""
Local tool handlers backed by Linear's IndexedDB cache.

These handlers contain only local-read logic. Routing/fallback decisions live in
`router.py`.
"""

from __future__ import annotations

import heapq
from typing import Any, Callable

from .reader import LinearLocalReader


class LocalFallbackRequested(RuntimeError):
    """Raised when local execution should fall back to the official MCP."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def _empty_total(key: str) -> dict[str, Any]:
    return {key: [], "totalCount": 0}


def _serialize_progress(progress: dict[str, Any] | None) -> dict[str, int] | None:
    if not progress:
        return None
    return {
        "completed": progress.get("completedIssueCount", 0),
        "started": progress.get("startedIssueCount", 0),
        "unstarted": progress.get("unstartedIssueCount", 0),
        "total": progress.get("scopeCount", 0),
    }


def _serialize_status_update(
    reader: LinearLocalReader, update: dict[str, Any]
) -> dict[str, Any]:
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
    updates = list(reader.project_updates.values())

    if project_id:
        updates = [u for u in updates if u.get("projectId") == project_id]
    if user_id:
        updates = [u for u in updates if u.get("userId") == user_id]

    sort_key = "updatedAt" if order_by == "updatedAt" else "createdAt"
    updates.sort(key=lambda x: x.get(sort_key) or "", reverse=True)
    return updates


def list_issues(
    reader: LinearLocalReader,
    assignee: str | None = None,
    team: str | None = None,
    state: str | None = None,
    priority: int | None = None,
    project: str | None = None,
    query: str | None = None,
    orderBy: str = "updatedAt",
    limit: int = 50,
) -> dict[str, Any]:
    assignee_id = None
    if assignee:
        user = reader.find_user(assignee)
        if user:
            assignee_id = user["id"]
        else:
            return _empty_total("issues")

    team_id = None
    if team:
        team_obj = reader.find_team(team)
        if team_obj:
            team_id = team_obj["id"]
        else:
            return _empty_total("issues")

    project_id = None
    if project:
        project_obj = reader.find_project(project)
        if project_obj:
            project_id = project_obj["id"]
        else:
            return _empty_total("issues")

    query_lower = query.lower() if query else None
    state_lower = state.lower() if state else None
    sort_key = "createdAt" if orderBy == "createdAt" else "updatedAt"

    filtered: list[dict[str, Any]] = []
    for issue in reader.issues.values():
        if assignee_id and issue.get("assigneeId") != assignee_id:
            continue
        if team_id and issue.get("teamId") != team_id:
            continue
        if state_lower:
            issue_state_type = reader.get_state_type(issue.get("stateId", ""))
            issue_state_name = reader.get_state_name(issue.get("stateId", ""))
            if state_lower != issue_state_type and state_lower != (
                issue_state_name or ""
            ).lower():
                continue
        if project_id and issue.get("projectId") != project_id:
            continue
        if query_lower and query_lower not in (issue.get("title") or "").lower():
            continue
        if priority is not None and issue.get("priority") != priority:
            continue
        filtered.append(issue)

    total_count = len(filtered)
    if limit and limit > 0:
        page = heapq.nlargest(limit, filtered, key=lambda x: x.get(sort_key) or "")
    else:
        page = sorted(filtered, key=lambda x: x.get(sort_key) or "", reverse=True)

    results = []
    for issue in page:
        results.append(
            {
                "identifier": issue.get("identifier"),
                "title": issue.get("title"),
                "priority": issue.get("priority"),
                "state": reader.get_state_name(issue.get("stateId", "")),
                "stateType": reader.get_state_type(issue.get("stateId", "")),
                "assignee": reader.get_user_name(issue.get("assigneeId")),
                "dueDate": issue.get("dueDate"),
            }
        )

    return {"issues": results, "totalCount": total_count}


def get_issue(reader: LinearLocalReader, id: str) -> dict[str, Any] | None:
    issue = reader.get_issue_by_identifier(id)
    if not issue:
        return None

    comments = reader.get_comments_for_issue(issue["id"])
    enriched_comments = []
    for comment in comments:
        user = reader.users.get(comment.get("userId", ""), {})
        enriched_comments.append(
            {
                "author": user.get("name", "Unknown"),
                "body": comment.get("body", ""),
                "createdAt": comment.get("createdAt"),
            }
        )

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


def list_teams(reader: LinearLocalReader) -> list[dict[str, Any]]:
    results = []
    for team in reader.teams.values():
        results.append(
            {
                "key": team.get("key"),
                "name": team.get("name"),
                "issueCount": reader.get_issue_count_for_team(team.get("id")),
            }
        )
    results.sort(key=lambda x: x.get("key", ""))
    return results


def list_projects(
    reader: LinearLocalReader, team: str | None = None
) -> list[dict[str, Any]]:
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

        results.append(
            {
                "name": project.get("name"),
                "state": project.get("state"),
                "issueCount": reader.get_issue_count_for_project(project.get("id")),
                "startDate": project.get("startDate"),
                "targetDate": project.get("targetDate"),
            }
        )

    results.sort(key=lambda x: x.get("name", "") or "")
    return results


def get_team(reader: LinearLocalReader, query: str) -> dict[str, Any] | None:
    team_obj = reader.find_team(query)
    if not team_obj:
        return None

    return {
        "id": team_obj.get("id"),
        "key": team_obj.get("key"),
        "name": team_obj.get("name"),
        "description": team_obj.get("description"),
        "issueCount": reader.get_issue_count_for_team(team_obj.get("id")),
        "issuesByState": reader.get_issue_state_counts_for_team(team_obj.get("id")),
    }


def get_project(reader: LinearLocalReader, query: str) -> dict[str, Any] | None:
    project = reader.find_project(query)
    if not project:
        return None

    return {
        "id": project.get("id"),
        "name": project.get("name"),
        "description": project.get("description"),
        "state": project.get("state"),
        "startDate": project.get("startDate"),
        "targetDate": project.get("targetDate"),
        "issueCount": reader.get_issue_count_for_project(project.get("id")),
        "issuesByState": reader.get_issue_state_counts_for_project(project.get("id")),
    }


def list_users(reader: LinearLocalReader) -> list[dict[str, Any]]:
    results = []
    for user in reader.users.values():
        results.append(
            {
                "id": user.get("id"),
                "name": user.get("name"),
                "email": user.get("email"),
                "displayName": user.get("displayName"),
                "assignedIssueCount": reader.get_issue_count_for_user(user.get("id")),
            }
        )
    results.sort(key=lambda x: x.get("name", "") or "")
    return results


def get_user(reader: LinearLocalReader, query: str) -> dict[str, Any] | None:
    user = reader.find_user(query)
    if not user:
        return None

    state_counts = reader.get_issue_state_counts_for_user(user.get("id"))
    return {
        "id": user.get("id"),
        "name": user.get("name"),
        "email": user.get("email"),
        "displayName": user.get("displayName"),
        "assignedIssueCount": sum(state_counts.values()),
        "issuesByState": state_counts,
    }


def list_issue_statuses(reader: LinearLocalReader, team: str) -> list[dict[str, Any]]:
    team_obj = reader.find_team(team)
    if not team_obj:
        return []

    results = []
    for state in reader.states.values():
        if state.get("teamId") == team_obj["id"]:
            results.append(
                {
                    "id": state.get("id"),
                    "name": state.get("name"),
                    "type": state.get("type"),
                    "color": state.get("color"),
                    "position": state.get("position"),
                }
            )

    results.sort(key=lambda x: (x.get("position") or 0))
    return results


def get_issue_status(
    reader: LinearLocalReader,
    team: str,
    name: str | None = None,
    id: str | None = None,
) -> dict[str, Any] | None:
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


def list_comments(reader: LinearLocalReader, issueId: str) -> list[dict[str, Any]]:
    issue = reader.get_issue_by_identifier(issueId)
    if not issue:
        return []

    comments = reader.get_comments_for_issue(issue["id"])
    results = []
    for comment in comments:
        user = reader.users.get(comment.get("userId", ""), {})
        results.append(
            {
                "id": comment.get("id"),
                "author": user.get("name", "Unknown"),
                "body": comment.get("body", ""),
                "createdAt": comment.get("createdAt"),
                "updatedAt": comment.get("updatedAt"),
            }
        )

    return results


def list_issue_labels(
    reader: LinearLocalReader, team: str | None = None
) -> list[dict[str, Any]]:
    team_id = None
    if team:
        team_obj = reader.find_team(team)
        if team_obj:
            team_id = team_obj["id"]

    results = []
    for label in reader.labels.values():
        if team_id and label.get("teamId") and label.get("teamId") != team_id:
            continue
        results.append(
            {
                "id": label.get("id"),
                "name": label.get("name"),
                "color": label.get("color"),
                "isGroup": label.get("isGroup"),
            }
        )

    results.sort(key=lambda x: x.get("name", "") or "")
    return results


def list_initiatives(reader: LinearLocalReader) -> list[dict[str, Any]]:
    results = []
    for initiative in reader.initiatives.values():
        results.append(
            {
                "id": initiative.get("id"),
                "name": initiative.get("name"),
                "slugId": initiative.get("slugId"),
                "color": initiative.get("color"),
                "status": initiative.get("status"),
                "owner": reader.get_user_name(initiative.get("ownerId")),
            }
        )

    results.sort(key=lambda x: x.get("name", "") or "")
    return results


def get_initiative(reader: LinearLocalReader, query: str) -> dict[str, Any] | None:
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


def list_cycles(reader: LinearLocalReader, teamId: str) -> list[dict[str, Any]]:
    team_obj = reader.find_team(teamId)
    if not team_obj:
        return []

    cycles = reader.get_cycles_for_team(team_obj["id"])
    results = []
    for cycle in cycles:
        results.append(
            {
                "id": cycle.get("id"),
                "number": cycle.get("number"),
                "startsAt": cycle.get("startsAt"),
                "endsAt": cycle.get("endsAt"),
                "completedAt": cycle.get("completedAt"),
                "progress": _serialize_progress(cycle.get("currentProgress")),
            }
        )

    return results


def list_documents(
    reader: LinearLocalReader, project: str | None = None
) -> list[dict[str, Any]]:
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
        results.append(
            {
                "id": doc.get("id"),
                "title": doc.get("title"),
                "slugId": doc.get("slugId"),
                "project": reader.get_project_name(doc.get("projectId")),
                "createdAt": doc.get("createdAt"),
                "updatedAt": doc.get("updatedAt"),
            }
        )

    results.sort(key=lambda x: x.get("updatedAt", "") or "", reverse=True)
    return results


def get_document(reader: LinearLocalReader, id: str) -> dict[str, Any] | None:
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


def list_milestones(reader: LinearLocalReader, project: str) -> list[dict[str, Any]]:
    project_obj = reader.find_project(project)
    if not project_obj:
        return []

    milestones = reader.get_milestones_for_project(project_obj["id"])
    results = []
    for milestone in milestones:
        results.append(
            {
                "id": milestone.get("id"),
                "name": milestone.get("name"),
                "targetDate": milestone.get("targetDate"),
                "progress": _serialize_progress(milestone.get("currentProgress")),
            }
        )

    return results


def get_milestone(
    reader: LinearLocalReader, project: str, query: str
) -> dict[str, Any] | None:
    project_obj = reader.find_project(project)
    if not project_obj:
        return None

    milestone = reader.find_milestone(project_obj["id"], query)
    if not milestone:
        return None

    return {
        "id": milestone.get("id"),
        "name": milestone.get("name"),
        "project": project_obj.get("name"),
        "targetDate": milestone.get("targetDate"),
        "sortOrder": milestone.get("sortOrder"),
        "progress": _serialize_progress(milestone.get("currentProgress")),
    }


def get_status_updates(
    reader: LinearLocalReader,
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
    if type != "project":
        raise LocalFallbackRequested(
            "unsupported_type",
            "local cache supports only get_status_updates(type='project')",
        )

    if initiative or cursor or createdAt or updatedAt or includeArchived:
        raise LocalFallbackRequested(
            "unsupported_filter",
            "one or more filters are unsupported by local cache",
        )

    project_id = None
    if project:
        project_obj = reader.find_project(project)
        if not project_obj:
            return _empty_total("statusUpdates")
        project_id = project_obj["id"]

    user_id = None
    if user:
        user_obj = reader.find_user(user)
        if not user_obj:
            return _empty_total("statusUpdates")
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


def list_project_updates(reader: LinearLocalReader, project: str) -> list[dict[str, Any]]:
    project_obj = reader.find_project(project)
    if not project_obj:
        return []

    response = get_status_updates(reader, type="project", project=project, limit=0)
    if not isinstance(response, dict):
        return []
    return response.get("statusUpdates", [])


LOCAL_READ_HANDLERS: dict[str, Callable[..., Any]] = {
    "list_issues": list_issues,
    "get_issue": get_issue,
    "list_teams": list_teams,
    "list_projects": list_projects,
    "get_team": get_team,
    "get_project": get_project,
    "list_users": list_users,
    "get_user": get_user,
    "list_issue_statuses": list_issue_statuses,
    "get_issue_status": get_issue_status,
    "list_comments": list_comments,
    "list_issue_labels": list_issue_labels,
    "list_initiatives": list_initiatives,
    "get_initiative": get_initiative,
    "list_cycles": list_cycles,
    "list_documents": list_documents,
    "get_document": get_document,
    "list_milestones": list_milestones,
    "get_milestone": get_milestone,
    "get_status_updates": get_status_updates,
    "list_project_updates": list_project_updates,
}

