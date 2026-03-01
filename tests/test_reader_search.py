from __future__ import annotations

import time

from linear_mcp_fast.reader import LinearLocalReader


def _build_reader_with_cache() -> LinearLocalReader:
    reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
    reader._reload_cache = lambda: None
    reader._cache.loaded_at = time.time()
    return reader


class TestFindTeam:
    def test_find_team_by_exact_key_uppercase(self):
        reader = _build_reader_with_cache()
        reader._cache.teams = {
            "T1": {"id": "T1", "key": "DEV", "name": "Development Team"},
            "T2": {"id": "T2", "key": "QA", "name": "QA Team"},
        }

        result = reader.find_team("DEV")
        assert result is not None
        assert result["id"] == "T1"
        assert result["key"] == "DEV"

    def test_find_team_by_key_case_insensitive(self):
        reader = _build_reader_with_cache()
        reader._cache.teams = {
            "T1": {"id": "T1", "key": "DEV", "name": "Team A"},
        }

        result = reader.find_team("dev")
        assert result is not None
        assert result["id"] == "T1"

    def test_find_team_by_name_substring_case_insensitive(self):
        reader = _build_reader_with_cache()
        reader._cache.teams = {
            "T1": {"id": "T1", "key": "DEV", "name": "Development Team"},
            "T2": {"id": "T2", "key": "QA", "name": "QA Team"},
        }

        result = reader.find_team("development")
        assert result is not None
        assert result["id"] == "T1"

    def test_find_team_by_name_partial_match(self):
        reader = _build_reader_with_cache()
        reader._cache.teams = {
            "T1": {"id": "T1", "key": "DEV", "name": "Development Team"},
        }

        result = reader.find_team("Dev")
        assert result is not None
        assert result["id"] == "T1"

    def test_find_team_key_takes_priority_over_name(self):
        reader = _build_reader_with_cache()
        reader._cache.teams = {
            "T1": {"id": "T1", "key": "BACKEND", "name": "Frontend Team"},
            "T2": {"id": "T2", "key": "FRONTEND", "name": "Backend Team"},
        }

        result = reader.find_team("BACKEND")
        assert result is not None
        assert result["id"] == "T1"
        assert result["key"] == "BACKEND"

    def test_find_team_no_match_returns_none(self):
        reader = _build_reader_with_cache()
        reader._cache.teams = {
            "T1": {"id": "T1", "key": "DEV", "name": "Development Team"},
        }

        result = reader.find_team("NONEXISTENT")
        assert result is None

    def test_find_team_empty_cache(self):
        reader = _build_reader_with_cache()
        reader._cache.teams = {}

        result = reader.find_team("DEV")
        assert result is None

    def test_find_team_returns_first_match_on_name(self):
        reader = _build_reader_with_cache()
        reader._cache.teams = {
            "T1": {"id": "T1", "key": "DEV", "name": "Team Dev"},
            "T2": {"id": "T2", "key": "QA", "name": "Team Dev Test"},
        }

        result = reader.find_team("dev")
        assert result is not None
        assert result["id"] in ("T1", "T2")


class TestFindProject:
    def test_find_project_by_name_exact_match(self):
        reader = _build_reader_with_cache()
        reader._cache.projects = {
            "P1": {"id": "P1", "name": "Web App", "slugId": "web-app"},
            "P2": {"id": "P2", "name": "Mobile App", "slugId": "mobile-app"},
        }

        result = reader.find_project("Web App")
        assert result is not None
        assert result["id"] == "P1"

    def test_find_project_by_name_substring(self):
        reader = _build_reader_with_cache()
        reader._cache.projects = {
            "P1": {"id": "P1", "name": "Web App", "slugId": "web-app"},
        }

        result = reader.find_project("web")
        assert result is not None
        assert result["id"] == "P1"

    def test_find_project_by_name_case_insensitive(self):
        reader = _build_reader_with_cache()
        reader._cache.projects = {
            "P1": {"id": "P1", "name": "Web App", "slugId": "web-app"},
        }

        result = reader.find_project("WEB APP")
        assert result is not None
        assert result["id"] == "P1"

    def test_find_project_by_slugid_exact_match(self):
        reader = _build_reader_with_cache()
        reader._cache.projects = {
            "P1": {"id": "P1", "name": "Web App", "slugId": "web-app"},
            "P2": {"id": "P2", "name": "Mobile App", "slugId": "mobile-app"},
        }

        result = reader.find_project("web-app")
        assert result is not None
        assert result["id"] == "P1"

    def test_find_project_by_slugid_case_insensitive(self):
        reader = _build_reader_with_cache()
        reader._cache.projects = {
            "P1": {"id": "P1", "name": "Web App", "slugId": "WEB-APP"},
        }

        result = reader.find_project("web-app")
        assert result is not None
        assert result["id"] == "P1"

    def test_find_project_exact_name_takes_priority_over_substring(self):
        reader = _build_reader_with_cache()
        reader._cache.projects = {
            "P1": {"id": "P1", "name": "Web", "slugId": "web"},
            "P2": {"id": "P2", "name": "Web App", "slugId": "web-app"},
        }

        result = reader.find_project("Web App")
        assert result is not None
        assert result["id"] == "P2"

    def test_find_project_no_match_returns_none(self):
        reader = _build_reader_with_cache()
        reader._cache.projects = {
            "P1": {"id": "P1", "name": "Web App", "slugId": "web-app"},
        }

        result = reader.find_project("nonexistent")
        assert result is None

    def test_find_project_empty_cache(self):
        reader = _build_reader_with_cache()
        reader._cache.projects = {}

        result = reader.find_project("Web App")
        assert result is None

    def test_find_project_name_starts_with_priority_over_slug_exact(self):
        reader = _build_reader_with_cache()
        reader._cache.projects = {
            "P1": {"id": "P1", "name": "Web", "slugId": "app"},
            "P2": {"id": "P2", "name": "App Web", "slugId": "web"},
        }

        result = reader.find_project("web")
        assert result is not None
        assert result["id"] == "P1"


class TestFindUser:
    def test_find_user_by_name_exact_match(self):
        reader = _build_reader_with_cache()
        reader._cache.users = {
            "U1": {"id": "U1", "name": "Alice", "displayName": "alice", "email": "alice@example.com"},
            "U2": {"id": "U2", "name": "Bob", "displayName": "bob", "email": "bob@example.com"},
        }

        result = reader.find_user("Alice")
        assert result is not None
        assert result["id"] == "U1"

    def test_find_user_by_name_substring(self):
        reader = _build_reader_with_cache()
        reader._cache.users = {
            "U1": {"id": "U1", "name": "Alice Smith", "displayName": "asmith", "email": "alice@example.com"},
        }

        result = reader.find_user("Alice")
        assert result is not None
        assert result["id"] == "U1"

    def test_find_user_by_name_case_insensitive(self):
        reader = _build_reader_with_cache()
        reader._cache.users = {
            "U1": {"id": "U1", "name": "Alice", "displayName": "alice", "email": "alice@example.com"},
        }

        result = reader.find_user("alice")
        assert result is not None
        assert result["id"] == "U1"

    def test_find_user_by_display_name_case_insensitive(self):
        reader = _build_reader_with_cache()
        reader._cache.users = {
            "U1": {"id": "U1", "name": "Alice", "displayName": "alice", "email": "alice@example.com"},
        }

        result = reader.find_user("alice")
        assert result is not None
        assert result["id"] == "U1"

    def test_find_user_name_substring_priority_over_display_name(self):
        reader = _build_reader_with_cache()
        reader._cache.users = {
            "U1": {"id": "U1", "name": "Alice Cooper", "displayName": "alice", "email": "alice@example.com"},
            "U2": {"id": "U2", "name": "Bob", "displayName": "Alice", "email": "bob@example.com"},
        }

        result = reader.find_user("Alice")
        assert result is not None
        assert result["id"] == "U1"

    def test_find_user_partial_name_match(self):
        reader = _build_reader_with_cache()
        reader._cache.users = {
            "U1": {"id": "U1", "name": "Alice Smith", "displayName": "asmith", "email": "alice@example.com"},
        }

        result = reader.find_user("Smith")
        assert result is not None
        assert result["id"] == "U1"

    def test_find_user_no_match_returns_none(self):
        reader = _build_reader_with_cache()
        reader._cache.users = {
            "U1": {"id": "U1", "name": "Alice", "displayName": "alice", "email": "alice@example.com"},
        }

        result = reader.find_user("Bob")
        assert result is None

    def test_find_user_empty_cache(self):
        reader = _build_reader_with_cache()
        reader._cache.users = {}

        result = reader.find_user("Alice")
        assert result is None

    def test_find_user_with_bytes_name(self):
        reader = _build_reader_with_cache()
        reader._cache.users = {
            "U1": {"id": "U1", "name": b"Alice", "displayName": "alice", "email": "alice@example.com"},
        }

        result = reader.find_user("Alice")
        assert result is not None
        assert result["id"] == "U1"

    def test_find_user_scoring_name_start(self):
        reader = _build_reader_with_cache()
        reader._cache.users = {
            "U1": {"id": "U1", "name": "Alice Lee", "displayName": "alice", "email": "alice@example.com"},
            "U2": {"id": "U2", "name": "Bob Lee", "displayName": "lee", "email": "bob@example.com"},
        }

        result = reader.find_user("Lee")
        assert result is not None
        assert result["id"] == "U1"


class TestGetIssueByIdentifier:
    def test_get_issue_by_identifier_exact_match(self):
        reader = _build_reader_with_cache()
        reader._cache.issues = {
            "I1": {"id": "I1", "identifier": "DEV-123", "title": "Test Issue"},
            "I2": {"id": "I2", "identifier": "QA-456", "title": "Another Issue"},
        }

        result = reader.get_issue_by_identifier("DEV-123")
        assert result is not None
        assert result["id"] == "I1"

    def test_get_issue_by_identifier_case_insensitive(self):
        reader = _build_reader_with_cache()
        reader._cache.issues = {
            "I1": {"id": "I1", "identifier": "DEV-123", "title": "Test Issue"},
        }

        result = reader.get_issue_by_identifier("dev-123")
        assert result is not None
        assert result["id"] == "I1"

    def test_get_issue_by_identifier_uppercase_input_lowercase_cache(self):
        reader = _build_reader_with_cache()
        reader._cache.issues = {
            "I1": {"id": "I1", "identifier": "dev-123", "title": "Test Issue"},
        }

        result = reader.get_issue_by_identifier("DEV-123")
        assert result is not None
        assert result["id"] == "I1"

    def test_get_issue_by_identifier_no_match_returns_none(self):
        reader = _build_reader_with_cache()
        reader._cache.issues = {
            "I1": {"id": "I1", "identifier": "DEV-123", "title": "Test Issue"},
        }

        result = reader.get_issue_by_identifier("QA-123")
        assert result is None

    def test_get_issue_by_identifier_empty_cache(self):
        reader = _build_reader_with_cache()
        reader._cache.issues = {}

        result = reader.get_issue_by_identifier("DEV-123")
        assert result is None

    def test_get_issue_by_identifier_with_spaces(self):
        reader = _build_reader_with_cache()
        reader._cache.issues = {
            "I1": {"id": "I1", "identifier": "DEV-123", "title": "Test Issue"},
        }

        result = reader.get_issue_by_identifier(" DEV-123 ")
        assert result is None

    def test_get_issue_by_identifier_partial_match_fails(self):
        reader = _build_reader_with_cache()
        reader._cache.issues = {
            "I1": {"id": "I1", "identifier": "DEV-123", "title": "Test Issue"},
        }

        result = reader.get_issue_by_identifier("DEV-12")
        assert result is None


class TestFindInitiative:
    def test_find_initiative_by_name_substring(self):
        reader = _build_reader_with_cache()
        reader._cache.initiatives = {
            "N1": {"id": "N1", "name": "Q1 2025 Roadmap", "slugId": "q1-2025"},
            "N2": {"id": "N2", "name": "Performance", "slugId": "perf"},
        }

        result = reader.find_initiative("Q1 2025")
        assert result is not None
        assert result["id"] == "N1"

    def test_find_initiative_by_name_case_insensitive(self):
        reader = _build_reader_with_cache()
        reader._cache.initiatives = {
            "N1": {"id": "N1", "name": "Q1 2025 Roadmap", "slugId": "q1-2025"},
        }

        result = reader.find_initiative("q1 2025")
        assert result is not None
        assert result["id"] == "N1"

    def test_find_initiative_by_slugid_exact_match(self):
        reader = _build_reader_with_cache()
        reader._cache.initiatives = {
            "N1": {"id": "N1", "name": "Q1 2025 Roadmap", "slugId": "q1-2025"},
        }

        result = reader.find_initiative("q1-2025")
        assert result is not None
        assert result["id"] == "N1"

    def test_find_initiative_slugid_case_insensitive(self):
        reader = _build_reader_with_cache()
        reader._cache.initiatives = {
            "N1": {"id": "N1", "name": "Q1 2025 Roadmap", "slugId": "Q1-2025"},
        }

        result = reader.find_initiative("q1-2025")
        assert result is not None
        assert result["id"] == "N1"

    def test_find_initiative_no_match_returns_none(self):
        reader = _build_reader_with_cache()
        reader._cache.initiatives = {
            "N1": {"id": "N1", "name": "Q1 2025 Roadmap", "slugId": "q1-2025"},
        }

        result = reader.find_initiative("Q3 2025")
        assert result is None

    def test_find_initiative_empty_cache(self):
        reader = _build_reader_with_cache()
        reader._cache.initiatives = {}

        result = reader.find_initiative("Q1 2025")
        assert result is None


class TestFindDocument:
    def test_find_document_by_title_substring(self):
        reader = _build_reader_with_cache()
        reader._cache.documents = {
            "D1": {"id": "D1", "title": "API Design Document", "slugId": "api-design"},
            "D2": {"id": "D2", "title": "UI Guidelines", "slugId": "ui-guide"},
        }

        result = reader.find_document("API Design")
        assert result is not None
        assert result["id"] == "D1"

    def test_find_document_by_title_case_insensitive(self):
        reader = _build_reader_with_cache()
        reader._cache.documents = {
            "D1": {"id": "D1", "title": "API Design Document", "slugId": "api-design"},
        }

        result = reader.find_document("api design")
        assert result is not None
        assert result["id"] == "D1"

    def test_find_document_by_slugid_exact_match(self):
        reader = _build_reader_with_cache()
        reader._cache.documents = {
            "D1": {"id": "D1", "title": "API Design Document", "slugId": "api-design"},
        }

        result = reader.find_document("api-design")
        assert result is not None
        assert result["id"] == "D1"

    def test_find_document_slugid_case_insensitive(self):
        reader = _build_reader_with_cache()
        reader._cache.documents = {
            "D1": {"id": "D1", "title": "API Design Document", "slugId": "API-DESIGN"},
        }

        result = reader.find_document("api-design")
        assert result is not None
        assert result["id"] == "D1"

    def test_find_document_no_match_returns_none(self):
        reader = _build_reader_with_cache()
        reader._cache.documents = {
            "D1": {"id": "D1", "title": "API Design Document", "slugId": "api-design"},
        }

        result = reader.find_document("Database Schema")
        assert result is None

    def test_find_document_empty_cache(self):
        reader = _build_reader_with_cache()
        reader._cache.documents = {}

        result = reader.find_document("API Design")
        assert result is None


class TestFindIssueStatus:
    def test_find_issue_status_by_id_exact_match(self):
        reader = _build_reader_with_cache()
        reader._cache.states = {
            "S1": {"id": "S1", "teamId": "T1", "name": "Todo", "type": "backlog"},
            "S2": {"id": "S2", "teamId": "T1", "name": "In Progress", "type": "started"},
        }

        result = reader.find_issue_status("T1", "S1")
        assert result is not None
        assert result["id"] == "S1"

    def test_find_issue_status_by_id_case_insensitive(self):
        reader = _build_reader_with_cache()
        reader._cache.states = {
            "S1": {"id": "S1", "teamId": "T1", "name": "Todo", "type": "backlog"},
        }

        result = reader.find_issue_status("T1", "s1")
        assert result is not None
        assert result["id"] == "S1"

    def test_find_issue_status_by_name_exact_match(self):
        reader = _build_reader_with_cache()
        reader._cache.states = {
            "S1": {"id": "S1", "teamId": "T1", "name": "In Progress", "type": "started"},
        }

        result = reader.find_issue_status("T1", "In Progress")
        assert result is not None
        assert result["id"] == "S1"

    def test_find_issue_status_by_name_case_insensitive(self):
        reader = _build_reader_with_cache()
        reader._cache.states = {
            "S1": {"id": "S1", "teamId": "T1", "name": "In Progress", "type": "started"},
        }

        result = reader.find_issue_status("T1", "in progress")
        assert result is not None
        assert result["id"] == "S1"

    def test_find_issue_status_by_name_starts_with(self):
        reader = _build_reader_with_cache()
        reader._cache.states = {
            "S1": {"id": "S1", "teamId": "T1", "name": "In Progress", "type": "started"},
        }

        result = reader.find_issue_status("T1", "In")
        assert result is not None
        assert result["id"] == "S1"

    def test_find_issue_status_by_name_substring(self):
        reader = _build_reader_with_cache()
        reader._cache.states = {
            "S1": {"id": "S1", "teamId": "T1", "name": "In Progress", "type": "started"},
        }

        result = reader.find_issue_status("T1", "Progress")
        assert result is not None
        assert result["id"] == "S1"

    def test_find_issue_status_id_takes_priority_over_name(self):
        reader = _build_reader_with_cache()
        reader._cache.states = {
            "S1": {"id": "S1", "teamId": "T1", "name": "Todo", "type": "backlog"},
            "S2": {"id": "S2", "teamId": "T1", "name": "S1", "type": "started"},
        }

        result = reader.find_issue_status("T1", "S1")
        assert result is not None
        assert result["id"] == "S1"

    def test_find_issue_status_only_searches_team(self):
        reader = _build_reader_with_cache()
        reader._cache.states = {
            "S1": {"id": "S1", "teamId": "T1", "name": "Todo", "type": "backlog"},
            "S2": {"id": "S2", "teamId": "T2", "name": "Todo", "type": "backlog"},
        }

        result = reader.find_issue_status("T1", "Todo")
        assert result is not None
        assert result["id"] == "S1"

    def test_find_issue_status_no_match_returns_none(self):
        reader = _build_reader_with_cache()
        reader._cache.states = {
            "S1": {"id": "S1", "teamId": "T1", "name": "Todo", "type": "backlog"},
        }

        result = reader.find_issue_status("T1", "Done")
        assert result is None

    def test_find_issue_status_empty_cache(self):
        reader = _build_reader_with_cache()
        reader._cache.states = {}

        result = reader.find_issue_status("T1", "Todo")
        assert result is None

    def test_find_issue_status_wrong_team_returns_none(self):
        reader = _build_reader_with_cache()
        reader._cache.states = {
            "S1": {"id": "S1", "teamId": "T1", "name": "Todo", "type": "backlog"},
        }

        result = reader.find_issue_status("T2", "Todo")
        assert result is None


class TestFindMilestone:
    def test_find_milestone_by_id_exact_match(self):
        reader = _build_reader_with_cache()
        reader._cache.milestones = {
            "M1": {"id": "M1", "projectId": "P1", "name": "v1.0", "sortOrder": 0},
            "M2": {"id": "M2", "projectId": "P1", "name": "v2.0", "sortOrder": 1},
        }

        result = reader.find_milestone("P1", "M1")
        assert result is not None
        assert result["id"] == "M1"

    def test_find_milestone_by_id_case_insensitive(self):
        reader = _build_reader_with_cache()
        reader._cache.milestones = {
            "M1": {"id": "M1", "projectId": "P1", "name": "v1.0", "sortOrder": 0},
        }

        result = reader.find_milestone("P1", "m1")
        assert result is not None
        assert result["id"] == "M1"

    def test_find_milestone_by_name_exact_match(self):
        reader = _build_reader_with_cache()
        reader._cache.milestones = {
            "M1": {"id": "M1", "projectId": "P1", "name": "v1.0 Release", "sortOrder": 0},
        }

        result = reader.find_milestone("P1", "v1.0 Release")
        assert result is not None
        assert result["id"] == "M1"

    def test_find_milestone_by_name_case_insensitive(self):
        reader = _build_reader_with_cache()
        reader._cache.milestones = {
            "M1": {"id": "M1", "projectId": "P1", "name": "v1.0 Release", "sortOrder": 0},
        }

        result = reader.find_milestone("P1", "v1.0 release")
        assert result is not None
        assert result["id"] == "M1"

    def test_find_milestone_by_name_starts_with(self):
        reader = _build_reader_with_cache()
        reader._cache.milestones = {
            "M1": {"id": "M1", "projectId": "P1", "name": "v1.0 Release", "sortOrder": 0},
        }

        result = reader.find_milestone("P1", "v1.0")
        assert result is not None
        assert result["id"] == "M1"

    def test_find_milestone_by_name_substring(self):
        reader = _build_reader_with_cache()
        reader._cache.milestones = {
            "M1": {"id": "M1", "projectId": "P1", "name": "v1.0 Release", "sortOrder": 0},
        }

        result = reader.find_milestone("P1", "Release")
        assert result is not None
        assert result["id"] == "M1"

    def test_find_milestone_id_takes_priority_over_name(self):
        reader = _build_reader_with_cache()
        reader._cache.milestones = {
            "M1": {"id": "M1", "projectId": "P1", "name": "v1.0", "sortOrder": 0},
            "M2": {"id": "M2", "projectId": "P1", "name": "M1", "sortOrder": 1},
        }

        result = reader.find_milestone("P1", "M1")
        assert result is not None
        assert result["id"] == "M1"

    def test_find_milestone_only_searches_project(self):
        reader = _build_reader_with_cache()
        reader._cache.milestones = {
            "M1": {"id": "M1", "projectId": "P1", "name": "v1.0", "sortOrder": 0},
            "M2": {"id": "M2", "projectId": "P2", "name": "v1.0", "sortOrder": 0},
        }

        result = reader.find_milestone("P1", "v1.0")
        assert result is not None
        assert result["id"] == "M1"

    def test_find_milestone_no_match_returns_none(self):
        reader = _build_reader_with_cache()
        reader._cache.milestones = {
            "M1": {"id": "M1", "projectId": "P1", "name": "v1.0", "sortOrder": 0},
        }

        result = reader.find_milestone("P1", "v2.0")
        assert result is None

    def test_find_milestone_empty_cache(self):
        reader = _build_reader_with_cache()
        reader._cache.milestones = {}

        result = reader.find_milestone("P1", "v1.0")
        assert result is None

    def test_find_milestone_wrong_project_returns_none(self):
        reader = _build_reader_with_cache()
        reader._cache.milestones = {
            "M1": {"id": "M1", "projectId": "P1", "name": "v1.0", "sortOrder": 0},
        }

        result = reader.find_milestone("P2", "v1.0")
        assert result is None
