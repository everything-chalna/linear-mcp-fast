"""Unit tests for LinearLocalReader helper methods (state/user/project lookups, cycles, milestones)."""

from __future__ import annotations

import time

from linear_mcp_fast.reader import CachedData, LinearLocalReader


def _make_reader_with_cache() -> LinearLocalReader:
    """Create a reader with pre-populated cache (no DB loading)."""
    reader = LinearLocalReader.__new__(LinearLocalReader)
    reader._force_next_refresh = False
    cache = CachedData(loaded_at=time.time())
    cache.teams = {
        "T1": {"id": "T1", "key": "DEV", "name": "Dev Team"},
        "T2": {"id": "T2", "key": "QA", "name": "QA Team"},
    }
    cache.users = {
        "U1": {"id": "U1", "name": "Alice", "displayName": "alice"},
        "U2": {"id": "U2", "name": "Bob"},
        "U3": {"id": "U3", "displayName": "charlie"},
    }
    cache.states = {
        "S1": {"id": "S1", "name": "In Progress", "type": "started"},
        "S2": {"id": "S2", "name": "Backlog", "type": "backlog"},
        "S3": {"id": "S3", "name": "Done", "type": "completed"},
    }
    cache.issues = {
        "I1": {"id": "I1", "identifier": "DEV-1", "title": "Bug fix",
               "teamId": "T1", "stateId": "S1", "assigneeId": "U1"},
        "I2": {"id": "I2", "identifier": "DEV-2", "title": "Feature work",
               "teamId": "T1", "stateId": "S2", "assigneeId": "U1"},
        "I3": {"id": "I3", "identifier": "QA-1", "title": "Test case",
               "teamId": "T2", "stateId": "S1", "assigneeId": "U2"},
        "I4": {"id": "I4", "identifier": "DEV-3", "title": "Another bug",
               "teamId": "T1", "stateId": "S3", "assigneeId": None},
    }
    cache.projects = {
        "P1": {"id": "P1", "name": "Alpha", "teamIds": ["T1"]},
        "P2": {"id": "P2", "name": "Beta", "teamIds": ["T2"]},
    }
    cache.cycles = {
        "CY1": {"id": "CY1", "teamId": "T1", "number": 3},
        "CY2": {"id": "CY2", "teamId": "T1", "number": 1},
        "CY3": {"id": "CY3", "teamId": "T1", "number": 2},
        "CY4": {"id": "CY4", "teamId": "T2", "number": 1},
    }
    cache.milestones = {
        "M1": {"id": "M1", "projectId": "P1", "sortOrder": 2, "name": "Beta"},
        "M2": {"id": "M2", "projectId": "P1", "sortOrder": 1, "name": "Alpha"},
        "M3": {"id": "M3", "projectId": "P2", "sortOrder": 1, "name": "V1"},
    }
    cache.comments = {}
    cache.comments_by_issue = {}
    cache.issue_content = {}
    cache.labels = {}
    cache.initiatives = {}
    cache.documents = {}
    cache.project_updates = {}
    cache.project_statuses = {}
    cache.document_content = {}
    reader._cache = cache
    return reader


class TestGetStateName:
    def test_known_state(self):
        reader = _make_reader_with_cache()
        assert reader.get_state_name("S1") == "In Progress"

    def test_unknown_state(self):
        reader = _make_reader_with_cache()
        assert reader.get_state_name("MISSING") == "Unknown"

    def test_empty_string_id(self):
        reader = _make_reader_with_cache()
        assert reader.get_state_name("") == "Unknown"


class TestGetStateType:
    def test_known_state(self):
        reader = _make_reader_with_cache()
        assert reader.get_state_type("S1") == "started"

    def test_unknown_state(self):
        reader = _make_reader_with_cache()
        assert reader.get_state_type("MISSING") == "unknown"

    def test_completed_type(self):
        reader = _make_reader_with_cache()
        assert reader.get_state_type("S3") == "completed"


class TestGetUserName:
    def test_known_user(self):
        reader = _make_reader_with_cache()
        assert reader.get_user_name("U1") == "Alice"

    def test_none_user_id(self):
        reader = _make_reader_with_cache()
        assert reader.get_user_name(None) == "Unassigned"

    def test_empty_string_user_id(self):
        reader = _make_reader_with_cache()
        assert reader.get_user_name("") == "Unassigned"

    def test_display_name_fallback(self):
        """User U3 has no 'name' but has 'displayName'."""
        reader = _make_reader_with_cache()
        assert reader.get_user_name("U3") == "charlie"

    def test_unknown_user(self):
        reader = _make_reader_with_cache()
        assert reader.get_user_name("MISSING") == "Unknown"


class TestGetProjectName:
    def test_known_project(self):
        reader = _make_reader_with_cache()
        assert reader.get_project_name("P1") == "Alpha"

    def test_none_project_id(self):
        reader = _make_reader_with_cache()
        assert reader.get_project_name(None) == ""

    def test_unknown_project(self):
        reader = _make_reader_with_cache()
        assert reader.get_project_name("MISSING") == ""


class TestGetIssuesForUser:
    def test_user_with_issues(self):
        reader = _make_reader_with_cache()
        issues = reader.get_issues_for_user("U1")
        ids = {i["id"] for i in issues}
        assert ids == {"I1", "I2"}

    def test_user_with_no_issues(self):
        reader = _make_reader_with_cache()
        issues = reader.get_issues_for_user("U3")
        assert issues == []

    def test_nonexistent_user(self):
        reader = _make_reader_with_cache()
        issues = reader.get_issues_for_user("MISSING")
        assert issues == []


class TestGetCyclesForTeam:
    def test_returns_cycles_sorted_desc_by_number(self):
        reader = _make_reader_with_cache()
        cycles = reader.get_cycles_for_team("T1")
        numbers = [c["number"] for c in cycles]
        assert numbers == [3, 2, 1]

    def test_single_cycle_team(self):
        reader = _make_reader_with_cache()
        cycles = reader.get_cycles_for_team("T2")
        assert len(cycles) == 1
        assert cycles[0]["number"] == 1

    def test_no_cycles_for_team(self):
        reader = _make_reader_with_cache()
        cycles = reader.get_cycles_for_team("MISSING")
        assert cycles == []


class TestGetMilestonesForProject:
    def test_returns_milestones_sorted_by_sort_order(self):
        reader = _make_reader_with_cache()
        milestones = reader.get_milestones_for_project("P1")
        names = [m["name"] for m in milestones]
        assert names == ["Alpha", "Beta"]

    def test_single_milestone(self):
        reader = _make_reader_with_cache()
        milestones = reader.get_milestones_for_project("P2")
        assert len(milestones) == 1
        assert milestones[0]["name"] == "V1"

    def test_no_milestones(self):
        reader = _make_reader_with_cache()
        milestones = reader.get_milestones_for_project("MISSING")
        assert milestones == []


class TestSearchIssues:
    def test_search_by_title_substring(self):
        reader = _make_reader_with_cache()
        results = reader.search_issues("bug")
        ids = {i["id"] for i in results}
        assert ids == {"I1", "I4"}

    def test_search_case_insensitive(self):
        reader = _make_reader_with_cache()
        results = reader.search_issues("BUG")
        assert len(results) == 2

    def test_search_no_results(self):
        reader = _make_reader_with_cache()
        results = reader.search_issues("nonexistent")
        assert results == []

    def test_search_with_limit(self):
        reader = _make_reader_with_cache()
        results = reader.search_issues("bug", limit=1)
        assert len(results) == 1


class TestGetTeamKey:
    def test_known_team(self):
        reader = _make_reader_with_cache()
        assert reader.get_team_key("T1") == "DEV"

    def test_none_team_id(self):
        reader = _make_reader_with_cache()
        assert reader.get_team_key(None) == "???"

    def test_unknown_team(self):
        reader = _make_reader_with_cache()
        assert reader.get_team_key("MISSING") == "???"
