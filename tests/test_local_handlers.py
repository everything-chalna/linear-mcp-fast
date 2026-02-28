from __future__ import annotations

from typing import Any

import pytest

from linear_mcp_fast import local_handlers


class MiniReader:
    def __init__(self):
        self.teams = {
            "T1": {"id": "T1", "key": "DEV", "name": "Dev Team", "description": "desc"},
        }
        self.users = {
            "U1": {"id": "U1", "name": "Alice", "displayName": "Alice", "email": "a@test"},
            "U2": {"id": "U2", "name": "Bob", "displayName": "Bob", "email": "b@test"},
        }
        self.states = {
            "S1": {"id": "S1", "name": "In Progress", "type": "started", "teamId": "T1", "position": 1},
            "S2": {"id": "S2", "name": "Backlog", "type": "backlog", "teamId": "T1", "position": 2},
        }
        self.projects = {
            "P1": {"id": "P1", "name": "Platform", "slugId": "platform", "state": "active", "description": "desc"},
        }
        self.issues = {
            "I1": {
                "id": "I1",
                "identifier": "DEV-1",
                "title": "Fix bug",
                "priority": 1,
                "estimate": 2,
                "stateId": "S1",
                "assigneeId": "U1",
                "teamId": "T1",
                "projectId": "P1",
                "dueDate": None,
                "description": "Issue 1",
                "createdAt": "2025-01-01T00:00:00Z",
                "updatedAt": "2025-01-03T00:00:00Z",
            },
            "I2": {
                "id": "I2",
                "identifier": "DEV-2",
                "title": "Write docs",
                "priority": 3,
                "estimate": 1,
                "stateId": "S2",
                "assigneeId": "U2",
                "teamId": "T1",
                "projectId": "P1",
                "dueDate": None,
                "description": "Issue 2",
                "createdAt": "2025-01-02T00:00:00Z",
                "updatedAt": "2025-01-02T00:00:00Z",
            },
        }
        self.labels = {"L1": {"id": "L1", "name": "bug", "color": "red", "isGroup": False, "teamId": "T1"}}
        self.initiatives = {
            "N1": {"id": "N1", "name": "North Star", "slugId": "north", "ownerId": "U1", "status": "active"}
        }
        self.cycles = {"C1": {"id": "C1", "number": 10, "teamId": "T1", "currentProgress": {"scopeCount": 2}}}
        self.documents = {
            "D1": {
                "id": "D1",
                "title": "Platform RFC",
                "slugId": "platform-rfc",
                "projectId": "P1",
                "creatorId": "U1",
                "createdAt": "2025-01-01",
                "updatedAt": "2025-01-05",
            }
        }
        self.milestones = {
            "M1": {
                "id": "M1",
                "name": "Alpha",
                "projectId": "P1",
                "sortOrder": 1,
                "targetDate": "2025-02-01",
                "currentProgress": {"completedIssueCount": 1, "scopeCount": 2},
            }
        }
        self.project_updates = {
            "UP1": {
                "id": "UP1",
                "body": "All good",
                "health": "onTrack",
                "projectId": "P1",
                "userId": "U1",
                "createdAt": "2025-01-04",
                "updatedAt": "2025-01-04",
            }
        }
        self._comments = {
            "I1": [{"id": "CMT1", "userId": "U1", "body": "LGTM", "createdAt": "2025-01-03", "updatedAt": "2025-01-03"}]
        }

    def _count(self, key: str, value: str | None) -> int:
        if not value:
            return 0
        return sum(1 for issue in self.issues.values() if issue.get(key) == value)

    def _state_counts(self, key: str, value: str | None) -> dict[str, int]:
        if not value:
            return {}
        out: dict[str, int] = {}
        for issue in self.issues.values():
            if issue.get(key) != value:
                continue
            state_type = self.get_state_type(issue.get("stateId", ""))
            out[state_type] = out.get(state_type, 0) + 1
        return out

    def find_user(self, search: str) -> dict[str, Any] | None:
        for user in self.users.values():
            if search.lower() in user["name"].lower():
                return user
        return None

    def find_team(self, search: str) -> dict[str, Any] | None:
        for team in self.teams.values():
            if search.upper() == team["key"] or search.lower() in team["name"].lower():
                return team
        return None

    def find_project(self, search: str) -> dict[str, Any] | None:
        for project in self.projects.values():
            if search.lower() in project["name"].lower() or search.lower() == project["slugId"]:
                return project
        return None

    def find_issue_status(self, team_id: str, query: str) -> dict[str, Any] | None:
        for state in self.states.values():
            if state.get("teamId") == team_id and query.lower() in state["name"].lower():
                return state
        return None

    def get_issue_by_identifier(self, identifier: str) -> dict[str, Any] | None:
        ident = identifier.upper()
        for issue in self.issues.values():
            if issue["identifier"].upper() == ident:
                return issue
        return None

    def get_comments_for_issue(self, issue_id: str) -> list[dict[str, Any]]:
        return list(self._comments.get(issue_id, []))

    def get_state_name(self, state_id: str) -> str:
        return self.states.get(state_id, {}).get("name", "Unknown")

    def get_state_type(self, state_id: str) -> str:
        return self.states.get(state_id, {}).get("type", "unknown")

    def get_user_name(self, user_id: str | None) -> str:
        if not user_id:
            return "Unassigned"
        return self.users.get(user_id, {}).get("name", "Unknown")

    def get_project_name(self, project_id: str | None) -> str:
        if not project_id:
            return ""
        return self.projects.get(project_id, {}).get("name", "")

    def get_issue_count_for_team(self, team_id: str | None) -> int:
        return self._count("teamId", team_id)

    def get_issue_count_for_project(self, project_id: str | None) -> int:
        return self._count("projectId", project_id)

    def get_issue_count_for_user(self, user_id: str | None) -> int:
        return self._count("assigneeId", user_id)

    def get_issue_state_counts_for_team(self, team_id: str | None) -> dict[str, int]:
        return self._state_counts("teamId", team_id)

    def get_issue_state_counts_for_project(self, project_id: str | None) -> dict[str, int]:
        return self._state_counts("projectId", project_id)

    def get_issue_state_counts_for_user(self, user_id: str | None) -> dict[str, int]:
        return self._state_counts("assigneeId", user_id)

    def get_cycles_for_team(self, team_id: str) -> list[dict[str, Any]]:
        return [c for c in self.cycles.values() if c.get("teamId") == team_id]

    def find_milestone(self, project_id: str, query: str) -> dict[str, Any] | None:
        for m in self.milestones.values():
            if m["projectId"] == project_id and query.lower() in m["name"].lower():
                return m
        return None

    def get_milestones_for_project(self, project_id: str) -> list[dict[str, Any]]:
        return [m for m in self.milestones.values() if m.get("projectId") == project_id]

    def find_initiative(self, query: str) -> dict[str, Any] | None:
        for initiative in self.initiatives.values():
            if query.lower() in initiative["name"].lower():
                return initiative
        return None

    def find_document(self, query: str) -> dict[str, Any] | None:
        for doc in self.documents.values():
            if query.lower() in doc["title"].lower() or query.lower() == doc["slugId"]:
                return doc
        return None


@pytest.fixture()
def reader() -> MiniReader:
    return MiniReader()


def test_list_issues_filters_and_limit(reader: MiniReader):
    result = local_handlers.list_issues(reader, assignee="Alice", limit=1, orderBy="updatedAt")
    assert result["totalCount"] == 1
    assert result["issues"][0]["identifier"] == "DEV-1"


def test_get_issue_returns_comments(reader: MiniReader):
    result = local_handlers.get_issue(reader, "DEV-1")
    assert result is not None
    assert result["comments"][0]["author"] == "Alice"


def test_get_team_uses_precomputed_counts(reader: MiniReader):
    result = local_handlers.get_team(reader, "DEV")
    assert result is not None
    assert result["issueCount"] == 2
    assert result["issuesByState"]["started"] == 1


def test_get_project_uses_find_project_and_state_counts(reader: MiniReader):
    result = local_handlers.get_project(reader, "platform")
    assert result is not None
    assert result["issueCount"] == 2
    assert result["issuesByState"]["backlog"] == 1


def test_get_status_updates_unsupported_filter_raises(reader: MiniReader):
    with pytest.raises(local_handlers.LocalFallbackRequested):
        local_handlers.get_status_updates(reader, type="project", initiative="north")


def test_get_status_updates_by_id(reader: MiniReader):
    result = local_handlers.get_status_updates(reader, type="project", id="UP1")
    assert result is not None
    assert result["id"] == "UP1"
    assert result["author"] == "Alice"


def test_get_document_by_slug(reader: MiniReader):
    result = local_handlers.get_document(reader, "platform-rfc")
    assert result is not None
    assert result["url"].endswith("/platform-rfc")


def test_list_milestones_serializes_progress(reader: MiniReader):
    result = local_handlers.list_milestones(reader, "Platform")
    assert len(result) == 1
    assert result[0]["progress"]["completed"] == 1
