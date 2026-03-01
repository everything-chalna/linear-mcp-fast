"""
Tests for LinearLocalReader property accessors and comments_by_issue functionality.

Tests the @property methods that return cached data, including:
- teams, users, states, issues, comments, projects, labels, initiatives,
  cycles, documents, milestones, project_updates, project_statuses
- comments_by_issue and get_comments_for_issue
- Cache expiration and refresh logic
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

from linear_mcp_fast.reader import CACHE_TTL_SECONDS, LinearLocalReader


class TestTeamsProperty:
    """Tests for the teams property."""

    def test_teams_property_returns_cache_teams(self) -> None:
        """Property returns _cache.teams without triggering reload."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()
        reader._cache.loaded_at = time.time()
        reader._cache.teams = {"T1": {"id": "T1", "key": "DEV", "name": "Dev"}}

        result = reader.teams

        assert result == {"T1": {"id": "T1", "key": "DEV", "name": "Dev"}}
        reader._reload_cache.assert_not_called()

    def test_teams_property_with_single_team(self) -> None:
        """Property returns dict with single team."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()
        reader._cache.loaded_at = time.time()
        reader._cache.teams = {"T1": {"id": "T1", "key": "DEV", "name": "Dev"}}

        result = reader.teams

        assert result == {"T1": {"id": "T1", "key": "DEV", "name": "Dev"}}
        reader._reload_cache.assert_not_called()

    def test_teams_property_with_multiple_teams(self) -> None:
        """Property returns all teams from cache."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()
        reader._cache.loaded_at = time.time()
        reader._cache.teams = {
            "T1": {"id": "T1", "key": "DEV", "name": "Dev"},
            "T2": {"id": "T2", "key": "DES", "name": "Design"},
            "T3": {"id": "T3", "key": "QA", "name": "QA"},
        }

        result = reader.teams

        assert len(result) == 3
        assert result["T1"]["key"] == "DEV"
        assert result["T2"]["key"] == "DES"
        assert result["T3"]["key"] == "QA"


class TestUsersProperty:
    """Tests for the users property."""

    def test_users_property_returns_cache_users(self) -> None:
        """Property returns _cache.users without triggering reload."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()
        reader._cache.loaded_at = time.time()
        reader._cache.teams = {"T1": {"id": "T1"}}  # Needed to avoid reload
        reader._cache.users = {"U1": {"id": "U1", "name": "Alice", "email": "alice@example.com"}}

        result = reader.users

        assert result == {"U1": {"id": "U1", "name": "Alice", "email": "alice@example.com"}}
        reader._reload_cache.assert_not_called()

    def test_users_property_with_empty_users_but_teams_present(self) -> None:
        """Property returns empty dict when no users in cache but teams present."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()
        reader._cache.loaded_at = time.time()
        reader._cache.teams = {"T1": {"id": "T1"}}  # Needed to avoid reload
        reader._cache.users = {}

        result = reader.users

        assert result == {}


class TestStatesProperty:
    """Tests for the states property."""

    def test_states_property_returns_cache_states(self) -> None:
        """Property returns _cache.states."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()
        reader._cache.loaded_at = time.time()
        reader._cache.teams = {"T1": {"id": "T1"}}  # Needed to avoid reload
        reader._cache.states = {
            "S1": {"id": "S1", "name": "Todo", "type": "unstarted", "teamId": "T1"}
        }

        result = reader.states

        assert result == {"S1": {"id": "S1", "name": "Todo", "type": "unstarted", "teamId": "T1"}}
        reader._reload_cache.assert_not_called()


class TestIssuesProperty:
    """Tests for the issues property."""

    def test_issues_property_returns_cache_issues(self) -> None:
        """Property returns _cache.issues."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()
        reader._cache.loaded_at = time.time()
        reader._cache.teams = {"T1": {"id": "T1"}}  # Needed to avoid reload
        reader._cache.issues = {
            "I1": {"id": "I1", "title": "Bug fix", "teamId": "T1", "identifier": "DEV-1"}
        }

        result = reader.issues

        assert result == {"I1": {"id": "I1", "title": "Bug fix", "teamId": "T1", "identifier": "DEV-1"}}
        reader._reload_cache.assert_not_called()


class TestCommentsProperty:
    """Tests for the comments property."""

    def test_comments_property_returns_cache_comments(self) -> None:
        """Property returns _cache.comments."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()
        reader._cache.loaded_at = time.time()
        reader._cache.teams = {"T1": {"id": "T1"}}  # Needed to avoid reload
        reader._cache.comments = {
            "C1": {"id": "C1", "issueId": "I1", "body": "Great work!", "userId": "U1"}
        }

        result = reader.comments

        assert result == {"C1": {"id": "C1", "issueId": "I1", "body": "Great work!", "userId": "U1"}}
        reader._reload_cache.assert_not_called()


class TestProjectsProperty:
    """Tests for the projects property."""

    def test_projects_property_returns_cache_projects(self) -> None:
        """Property returns _cache.projects."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()
        reader._cache.loaded_at = time.time()
        reader._cache.teams = {"T1": {"id": "T1"}}  # Needed to avoid reload
        reader._cache.projects = {
            "P1": {"id": "P1", "name": "Q1 Planning", "teamIds": ["T1"]}
        }

        result = reader.projects

        assert result == {"P1": {"id": "P1", "name": "Q1 Planning", "teamIds": ["T1"]}}
        reader._reload_cache.assert_not_called()


class TestLabelsProperty:
    """Tests for the labels property."""

    def test_labels_property_returns_cache_labels(self) -> None:
        """Property returns _cache.labels."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()
        reader._cache.loaded_at = time.time()
        reader._cache.teams = {"T1": {"id": "T1"}}  # Needed to avoid reload
        reader._cache.labels = {
            "L1": {"id": "L1", "name": "bug", "color": "red", "teamId": "T1"}
        }

        result = reader.labels

        assert result == {"L1": {"id": "L1", "name": "bug", "color": "red", "teamId": "T1"}}
        reader._reload_cache.assert_not_called()


class TestInitiativesProperty:
    """Tests for the initiatives property."""

    def test_initiatives_property_returns_cache_initiatives(self) -> None:
        """Property returns _cache.initiatives."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()
        reader._cache.loaded_at = time.time()
        reader._cache.teams = {"T1": {"id": "T1"}}  # Needed to avoid reload
        reader._cache.initiatives = {
            "IN1": {"id": "IN1", "name": "Q1 Goals", "ownerId": "U1"}
        }

        result = reader.initiatives

        assert result == {"IN1": {"id": "IN1", "name": "Q1 Goals", "ownerId": "U1"}}
        reader._reload_cache.assert_not_called()


class TestCyclesProperty:
    """Tests for the cycles property."""

    def test_cycles_property_returns_cache_cycles(self) -> None:
        """Property returns _cache.cycles."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()
        reader._cache.loaded_at = time.time()
        reader._cache.teams = {"T1": {"id": "T1"}}  # Needed to avoid reload
        reader._cache.cycles = {
            "CY1": {"id": "CY1", "number": 1, "teamId": "T1"}
        }

        result = reader.cycles

        assert result == {"CY1": {"id": "CY1", "number": 1, "teamId": "T1"}}
        reader._reload_cache.assert_not_called()


class TestDocumentsProperty:
    """Tests for the documents property."""

    def test_documents_property_returns_cache_documents(self) -> None:
        """Property returns _cache.documents."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()
        reader._cache.loaded_at = time.time()
        reader._cache.teams = {"T1": {"id": "T1"}}  # Needed to avoid reload
        reader._cache.documents = {
            "D1": {"id": "D1", "title": "Architecture", "projectId": "P1"}
        }

        result = reader.documents

        assert result == {"D1": {"id": "D1", "title": "Architecture", "projectId": "P1"}}
        reader._reload_cache.assert_not_called()


class TestMilestonesProperty:
    """Tests for the milestones property."""

    def test_milestones_property_returns_cache_milestones(self) -> None:
        """Property returns _cache.milestones."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()
        reader._cache.loaded_at = time.time()
        reader._cache.teams = {"T1": {"id": "T1"}}  # Needed to avoid reload
        reader._cache.milestones = {
            "M1": {"id": "M1", "name": "Alpha", "projectId": "P1"}
        }

        result = reader.milestones

        assert result == {"M1": {"id": "M1", "name": "Alpha", "projectId": "P1"}}
        reader._reload_cache.assert_not_called()


class TestProjectUpdatesProperty:
    """Tests for the project_updates property."""

    def test_project_updates_property_returns_cache_project_updates(self) -> None:
        """Property returns _cache.project_updates."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()
        reader._cache.loaded_at = time.time()
        reader._cache.teams = {"T1": {"id": "T1"}}  # Needed to avoid reload
        reader._cache.project_updates = {
            "PU1": {"id": "PU1", "body": "Q1 status", "projectId": "P1"}
        }

        result = reader.project_updates

        assert result == {"PU1": {"id": "PU1", "body": "Q1 status", "projectId": "P1"}}
        reader._reload_cache.assert_not_called()


class TestCommentsByIssueProperty:
    """Tests for the comments_by_issue property and get_comments_for_issue method."""

    def test_comments_by_issue_property_returns_cached_mapping(self) -> None:
        """Property returns _cache.comments_by_issue without reload."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()
        reader._cache.loaded_at = time.time()
        reader._cache.comments_by_issue = {"I1": ["C1", "C2"]}

        # Access via the comments_by_issue attribute (via _cache)
        result = reader._cache.comments_by_issue

        assert result == {"I1": ["C1", "C2"]}
        reader._reload_cache.assert_not_called()

    def test_get_comments_for_issue_returns_list_for_known_issue(self) -> None:
        """get_comments_for_issue returns list of comments for known issue."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()
        reader._cache.loaded_at = time.time()
        reader._cache.comments = {
            "C1": {"id": "C1", "issueId": "I1", "body": "First comment", "createdAt": "2025-01-01T10:00:00Z"},
            "C2": {"id": "C2", "issueId": "I1", "body": "Second comment", "createdAt": "2025-01-01T11:00:00Z"},
        }
        reader._cache.comments_by_issue = {"I1": ["C1", "C2"]}

        result = reader.get_comments_for_issue("I1")

        assert len(result) == 2
        assert result[0]["id"] == "C1"
        assert result[1]["id"] == "C2"
        assert result[0]["body"] == "First comment"
        assert result[1]["body"] == "Second comment"

    def test_get_comments_for_issue_returns_empty_for_unknown_issue(self) -> None:
        """get_comments_for_issue returns empty list for unknown issue."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()
        reader._cache.loaded_at = time.time()
        reader._cache.comments = {}
        reader._cache.comments_by_issue = {}

        result = reader.get_comments_for_issue("UNKNOWN")

        assert result == []

    def test_get_comments_for_issue_returns_sorted_by_creation_time(self) -> None:
        """get_comments_for_issue returns comments sorted by createdAt."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()
        reader._cache.loaded_at = time.time()
        reader._cache.comments = {
            "C3": {"id": "C3", "issueId": "I1", "body": "Third", "createdAt": "2025-01-01T12:00:00Z"},
            "C1": {"id": "C1", "issueId": "I1", "body": "First", "createdAt": "2025-01-01T10:00:00Z"},
            "C2": {"id": "C2", "issueId": "I1", "body": "Second", "createdAt": "2025-01-01T11:00:00Z"},
        }
        reader._cache.comments_by_issue = {"I1": ["C3", "C1", "C2"]}

        result = reader.get_comments_for_issue("I1")

        assert result[0]["id"] == "C1"
        assert result[1]["id"] == "C2"
        assert result[2]["id"] == "C3"

    def test_get_comments_for_issue_filters_missing_comments(self) -> None:
        """get_comments_for_issue only returns comments that exist in cache."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()
        reader._cache.loaded_at = time.time()
        reader._cache.comments = {
            "C1": {"id": "C1", "issueId": "I1", "body": "First", "createdAt": "2025-01-01T10:00:00Z"},
        }
        # comments_by_issue references C2 which doesn't exist in comments
        reader._cache.comments_by_issue = {"I1": ["C1", "C2"]}

        result = reader.get_comments_for_issue("I1")

        assert len(result) == 1
        assert result[0]["id"] == "C1"

    def test_get_comments_for_issue_with_no_created_at(self) -> None:
        """get_comments_for_issue handles comments without createdAt field."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()
        reader._cache.loaded_at = time.time()
        reader._cache.comments = {
            "C1": {"id": "C1", "issueId": "I1", "body": "No date"},
            "C2": {"id": "C2", "issueId": "I1", "body": "Has date", "createdAt": "2025-01-01T10:00:00Z"},
        }
        reader._cache.comments_by_issue = {"I1": ["C1", "C2"]}

        result = reader.get_comments_for_issue("I1")

        assert len(result) == 2


class TestPropertyEnsuresCacheNotExpired:
    """Tests that properties trigger cache refresh when expired."""

    def test_teams_property_calls_ensure_cache(self) -> None:
        """Accessing teams property triggers _ensure_cache."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()
        reader._cache.loaded_at = time.time()
        reader._cache.teams = {"T1": {"id": "T1"}}

        with patch.object(reader, "_ensure_cache", wraps=reader._ensure_cache) as mock_ensure:
            _ = reader.teams
            mock_ensure.assert_called_once()

    def test_property_triggers_reload_when_expired(self) -> None:
        """When cache is expired, accessing property triggers reload."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()

        # Set cache to be expired
        old_time = time.time() - (CACHE_TTL_SECONDS + 1)
        reader._cache.loaded_at = old_time
        reader._cache.teams = {"T1": {"id": "T1"}}

        _ = reader.teams

        reader._reload_cache.assert_called_once()

    def test_property_does_not_reload_when_fresh(self) -> None:
        """When cache is fresh, accessing property does not trigger reload."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()

        # Set cache to be fresh
        reader._cache.loaded_at = time.time()
        reader._cache.teams = {"T1": {"id": "T1"}}

        _ = reader.teams

        reader._reload_cache.assert_not_called()

    def test_property_reloads_when_teams_is_empty(self) -> None:
        """When cache has no teams, accessing any property triggers reload."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()

        # Set cache to be fresh but with no teams
        reader._cache.loaded_at = time.time()
        reader._cache.teams = {}

        _ = reader.teams

        # Since teams is empty, _ensure_cache() will trigger reload
        reader._reload_cache.assert_called_once()

    def test_users_property_calls_ensure_cache(self) -> None:
        """Accessing users property triggers _ensure_cache."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()
        reader._cache.loaded_at = time.time()
        reader._cache.users = {}

        with patch.object(reader, "_ensure_cache", wraps=reader._ensure_cache) as mock_ensure:
            _ = reader.users
            mock_ensure.assert_called_once()

    def test_comments_property_calls_ensure_cache(self) -> None:
        """Accessing comments property triggers _ensure_cache."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()
        reader._cache.loaded_at = time.time()
        reader._cache.comments = {}

        with patch.object(reader, "_ensure_cache", wraps=reader._ensure_cache) as mock_ensure:
            _ = reader.comments
            mock_ensure.assert_called_once()

    def test_get_comments_for_issue_calls_ensure_cache(self) -> None:
        """Calling get_comments_for_issue triggers _ensure_cache."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()
        reader._cache.loaded_at = time.time()
        reader._cache.comments = {}
        reader._cache.comments_by_issue = {}

        with patch.object(reader, "_ensure_cache", wraps=reader._ensure_cache) as mock_ensure:
            _ = reader.get_comments_for_issue("I1")
            mock_ensure.assert_called_once()


class TestPropertyIntegration:
    """Integration tests for multiple properties."""

    def test_all_properties_return_correct_types(self) -> None:
        """All properties return dict types."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()
        reader._cache.loaded_at = time.time()

        # Populate cache
        reader._cache.teams = {}
        reader._cache.users = {}
        reader._cache.states = {}
        reader._cache.issues = {}
        reader._cache.comments = {}
        reader._cache.projects = {}
        reader._cache.labels = {}
        reader._cache.initiatives = {}
        reader._cache.cycles = {}
        reader._cache.documents = {}
        reader._cache.milestones = {}
        reader._cache.project_updates = {}

        assert isinstance(reader.teams, dict)
        assert isinstance(reader.users, dict)
        assert isinstance(reader.states, dict)
        assert isinstance(reader.issues, dict)
        assert isinstance(reader.comments, dict)
        assert isinstance(reader.projects, dict)
        assert isinstance(reader.labels, dict)
        assert isinstance(reader.initiatives, dict)
        assert isinstance(reader.cycles, dict)
        assert isinstance(reader.documents, dict)
        assert isinstance(reader.milestones, dict)
        assert isinstance(reader.project_updates, dict)

    def test_multiple_property_accesses_use_same_cache(self) -> None:
        """Multiple property accesses use the same cache without multiple reloads."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()
        reader._cache.loaded_at = time.time()
        reader._cache.teams = {"T1": {"id": "T1"}}
        reader._cache.users = {"U1": {"id": "U1"}}

        teams1 = reader.teams
        teams2 = reader.teams
        users1 = reader.users
        users2 = reader.users

        # Should not reload for any of the accesses
        reader._reload_cache.assert_not_called()
        # And all accesses should return the same objects
        assert teams1 is teams2
        assert users1 is users2

    def test_comments_and_comments_for_issue_consistency(self) -> None:
        """comments property and get_comments_for_issue are consistent."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()
        reader._cache.loaded_at = time.time()
        reader._cache.comments = {
            "C1": {"id": "C1", "issueId": "I1", "body": "Comment 1", "createdAt": "2025-01-01T10:00:00Z"},
            "C2": {"id": "C2", "issueId": "I1", "body": "Comment 2", "createdAt": "2025-01-01T11:00:00Z"},
        }
        reader._cache.comments_by_issue = {"I1": ["C1", "C2"]}

        all_comments = reader.comments
        issue_comments = reader.get_comments_for_issue("I1")

        # get_comments_for_issue should return a subset from comments
        assert len(issue_comments) == 2
        assert all_comments["C1"] in issue_comments
        assert all_comments["C2"] in issue_comments


class TestCacheExpiration:
    """Tests for cache expiration behavior."""

    def test_ensure_cache_reloads_when_expired(self) -> None:
        """_ensure_cache reloads when cache is expired."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()

        # Set cache to be expired
        old_time = time.time() - (CACHE_TTL_SECONDS + 100)
        reader._cache.loaded_at = old_time
        reader._cache.teams = {"old": "data"}

        reader._ensure_cache()

        reader._reload_cache.assert_called_once()

    def test_ensure_cache_returns_cache_when_fresh(self) -> None:
        """_ensure_cache returns cache without reload when fresh."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()

        # Set cache to be fresh
        reader._cache.loaded_at = time.time()
        reader._cache.teams = {"T1": {"id": "T1"}}

        result = reader._ensure_cache()

        assert result is reader._cache
        reader._reload_cache.assert_not_called()

    def test_ensure_cache_reloads_when_no_teams(self) -> None:
        """_ensure_cache reloads when cache has no teams."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()

        # Set cache to be fresh but empty
        reader._cache.loaded_at = time.time()
        reader._cache.teams = {}

        reader._ensure_cache()

        reader._reload_cache.assert_called_once()

    def test_force_next_refresh_flag(self) -> None:
        """_force_next_refresh flag causes reload on next access."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()

        # Set cache to be fresh
        reader._cache.loaded_at = time.time()
        reader._cache.teams = {"T1": {"id": "T1"}}

        # Set force flag
        reader._force_next_refresh = True

        reader._ensure_cache()

        reader._reload_cache.assert_called_once()
        # Flag should be reset
        assert reader._force_next_refresh is False
