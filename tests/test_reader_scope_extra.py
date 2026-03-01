from __future__ import annotations

import pytest

from linear_mcp_fast.reader import CachedData, LinearLocalReader


def _build_cache() -> CachedData:
    cache = CachedData()
    cache.users = {
        "U1": {
            "id": "U1",
            "email": "target@example.com",
            "organizationId": "ORG1",
            "userAccountId": "ACC1",
            "name": "Target",
            "displayName": "target",
        },
        "U2": {
            "id": "U2",
            "email": "coworker@example.com",
            "organizationId": "ORG1",
            "userAccountId": "ACC2",
            "name": "Coworker",
            "displayName": "coworker",
        },
        "U3": {
            "id": "U3",
            "email": "other@example.com",
            "organizationId": "ORG2",
            "userAccountId": "ACC3",
            "name": "Other",
            "displayName": "other",
        },
        "U4": {
            "id": "U4",
            "email": "third@example.com",
            "organizationId": "ORG3",
            "userAccountId": "ACC4",
            "name": "Third",
            "displayName": "third",
        },
    }
    cache.teams = {
        "T1": {"id": "T1", "key": "ORG1", "name": "Org1 Team", "organizationId": "ORG1"},
        "T2": {"id": "T2", "key": "ORG2", "name": "Org2 Team", "organizationId": "ORG2"},
        "T3": {"id": "T3", "key": "ORG3", "name": "Org3 Team", "organizationId": "ORG3"},
    }
    cache.states = {
        "S1": {"id": "S1", "teamId": "T1", "type": "started", "name": "In Progress"},
        "S2": {"id": "S2", "teamId": "T2", "type": "started", "name": "In Progress"},
        "S3": {"id": "S3", "teamId": "T3", "type": "completed", "name": "Done"},
    }
    cache.issues = {
        "I1": {"id": "I1", "teamId": "T1", "stateId": "S1", "projectId": "P1"},
        "I2": {"id": "I2", "teamId": "T2", "stateId": "S2", "projectId": "P2"},
        "I3": {"id": "I3", "teamId": "T3", "stateId": "S3", "projectId": "P3"},
    }
    cache.issue_content = {"I1": "org1", "I2": "org2", "I3": "org3"}
    cache.comments = {
        "C1": {"id": "C1", "issueId": "I1"},
        "C2": {"id": "C2", "issueId": "I2"},
        "C3": {"id": "C3", "issueId": "I3"},
    }
    cache.comments_by_issue = {"I1": ["C1"], "I2": ["C2"], "I3": ["C3"]}
    cache.projects = {
        "P1": {"id": "P1", "teamIds": ["T1"], "statusId": "PS1", "memberIds": ["U1", "U2"]},
        "P2": {"id": "P2", "teamIds": ["T2"], "statusId": "PS2", "memberIds": ["U3"]},
        "P3": {"id": "P3", "teamIds": ["T3"], "statusId": "PS3", "memberIds": ["U4"]},
    }
    cache.labels = {
        "L1": {"id": "L1", "teamId": "T1"},
        "L2": {"id": "L2", "teamId": "T2"},
        "L3": {"id": "L3", "teamId": "T3"},
        "L_GLOBAL": {"id": "L_GLOBAL", "teamId": None},
    }
    cache.initiatives = {
        "N1": {"id": "N1", "teamIds": ["T1"], "ownerId": "U1"},
        "N2": {"id": "N2", "teamIds": ["T2"], "ownerId": "U3"},
        "N3": {"id": "N3", "teamIds": ["T3"], "ownerId": "U4"},
    }
    cache.cycles = {
        "CY1": {"id": "CY1", "teamId": "T1"},
        "CY2": {"id": "CY2", "teamId": "T2"},
        "CY3": {"id": "CY3", "teamId": "T3"},
    }
    cache.documents = {
        "D1": {"id": "D1", "projectId": "P1", "creatorId": "U2"},
        "D2": {"id": "D2", "projectId": "P2", "creatorId": "U3"},
        "D3": {"id": "D3", "projectId": "P3", "creatorId": "U4"},
        "D_NO_PROJECT": {"id": "D_NO_PROJECT", "projectId": None, "creatorId": "U1"},
    }
    cache.milestones = {
        "M1": {"id": "M1", "projectId": "P1"},
        "M2": {"id": "M2", "projectId": "P2"},
        "M3": {"id": "M3", "projectId": "P3"},
    }
    cache.project_updates = {
        "UP1": {"id": "UP1", "projectId": "P1"},
        "UP2": {"id": "UP2", "projectId": "P2"},
        "UP3": {"id": "UP3", "projectId": "P3"},
    }
    cache.project_statuses = {
        "PS1": {"id": "PS1", "name": "On Track"},
        "PS2": {"id": "PS2", "name": "At Risk"},
        "PS3": {"id": "PS3", "name": "Blocked"},
    }
    cache.document_content = {
        "DC1": {"id": "DC1", "documentContentId": "D1"},
        "DC2": {"id": "DC2", "documentContentId": "D2"},
        "DC3": {"id": "DC3", "documentContentId": "D3"},
        "DC_NO_PROJECT": {"id": "DC_NO_PROJECT", "documentContentId": "D_NO_PROJECT"},
    }
    return cache


def test_scope_by_user_account_id(monkeypatch: pytest.MonkeyPatch):
    """Test filtering using LINEAR_FAST_USER_ACCOUNT_IDS env var without email."""
    monkeypatch.delenv("LINEAR_FAST_ACCOUNT_EMAILS", raising=False)
    monkeypatch.delenv("LINEAR_FAST_ACCOUNT_EMAIL", raising=False)
    monkeypatch.setenv("LINEAR_FAST_USER_ACCOUNT_IDS", "ACC1,ACC2")
    reader = LinearLocalReader()
    cache = _build_cache()

    reader._apply_account_scope(cache)

    assert set(cache.users.keys()) == {"U1", "U2"}
    assert set(cache.teams.keys()) == {"T1"}
    assert set(cache.states.keys()) == {"S1"}
    assert set(cache.issues.keys()) == {"I1"}
    assert set(cache.comments.keys()) == {"C1"}
    assert cache.comments_by_issue == {"I1": ["C1"]}
    assert set(cache.projects.keys()) == {"P1"}
    assert set(cache.labels.keys()) == {"L1", "L_GLOBAL"}
    assert set(cache.initiatives.keys()) == {"N1"}
    assert set(cache.cycles.keys()) == {"CY1"}
    assert set(cache.documents.keys()) == {"D1", "D_NO_PROJECT"}
    assert set(cache.milestones.keys()) == {"M1"}
    assert set(cache.project_updates.keys()) == {"UP1"}
    assert set(cache.project_statuses.keys()) == {"PS1"}


def test_scope_with_no_env_vars_is_noop(monkeypatch: pytest.MonkeyPatch):
    """Test that scope is not applied when neither env var is set."""
    monkeypatch.delenv("LINEAR_FAST_ACCOUNT_EMAILS", raising=False)
    monkeypatch.delenv("LINEAR_FAST_ACCOUNT_EMAIL", raising=False)
    monkeypatch.delenv("LINEAR_FAST_USER_ACCOUNT_IDS", raising=False)
    monkeypatch.delenv("LINEAR_FAST_USER_ACCOUNT_ID", raising=False)
    reader = LinearLocalReader()
    cache = _build_cache()

    original_users = set(cache.users.keys())
    original_teams = set(cache.teams.keys())
    original_issues = set(cache.issues.keys())
    original_comments = set(cache.comments.keys())
    original_projects = set(cache.projects.keys())

    reader._apply_account_scope(cache)

    assert set(cache.users.keys()) == original_users
    assert set(cache.teams.keys()) == original_teams
    assert set(cache.issues.keys()) == original_issues
    assert set(cache.comments.keys()) == original_comments
    assert set(cache.projects.keys()) == original_projects


def test_scope_with_multiple_emails(monkeypatch: pytest.MonkeyPatch):
    """Test comma-separated emails filter to union of orgs."""
    monkeypatch.setenv("LINEAR_FAST_ACCOUNT_EMAILS", "target@example.com,other@example.com")
    monkeypatch.delenv("LINEAR_FAST_USER_ACCOUNT_IDS", raising=False)
    reader = LinearLocalReader()
    cache = _build_cache()

    reader._apply_account_scope(cache)

    assert set(cache.users.keys()) == {"U1", "U2", "U3"}
    assert set(cache.teams.keys()) == {"T1", "T2"}
    assert set(cache.states.keys()) == {"S1", "S2"}
    assert set(cache.issues.keys()) == {"I1", "I2"}
    assert set(cache.comments.keys()) == {"C1", "C2"}
    assert cache.comments_by_issue == {"I1": ["C1"], "I2": ["C2"]}
    assert set(cache.projects.keys()) == {"P1", "P2"}
    assert set(cache.labels.keys()) == {"L1", "L2", "L_GLOBAL"}
    assert set(cache.initiatives.keys()) == {"N1", "N2"}
    assert set(cache.cycles.keys()) == {"CY1", "CY2"}
    assert set(cache.documents.keys()) == {"D1", "D2", "D_NO_PROJECT"}
    assert set(cache.milestones.keys()) == {"M1", "M2"}
    assert set(cache.project_updates.keys()) == {"UP1", "UP2"}
    assert set(cache.project_statuses.keys()) == {"PS1", "PS2"}


def test_scope_preserves_project_statuses(monkeypatch: pytest.MonkeyPatch):
    """Test that project_statuses are correctly filtered based on projects."""
    monkeypatch.setenv("LINEAR_FAST_ACCOUNT_EMAILS", "target@example.com")
    monkeypatch.delenv("LINEAR_FAST_USER_ACCOUNT_IDS", raising=False)
    reader = LinearLocalReader()
    cache = _build_cache()

    reader._apply_account_scope(cache)

    allowed_status_ids = {
        project.get("statusId")
        for project in cache.projects.values()
        if project.get("statusId")
    }

    assert allowed_status_ids == {"PS1"}
    assert set(cache.project_statuses.keys()) == {"PS1"}
    assert cache.project_statuses["PS1"]["name"] == "On Track"


def test_scope_documents_filtered(monkeypatch: pytest.MonkeyPatch):
    """Test that documents are correctly filtered by scope."""
    monkeypatch.setenv("LINEAR_FAST_ACCOUNT_EMAILS", "target@example.com")
    monkeypatch.delenv("LINEAR_FAST_USER_ACCOUNT_IDS", raising=False)
    reader = LinearLocalReader()
    cache = _build_cache()

    reader._apply_account_scope(cache)

    assert set(cache.documents.keys()) == {"D1", "D_NO_PROJECT"}
    assert "D2" not in cache.documents
    assert "D3" not in cache.documents


def test_scope_with_single_account_id_env_var(monkeypatch: pytest.MonkeyPatch):
    """Test singular LINEAR_FAST_USER_ACCOUNT_ID env var."""
    monkeypatch.delenv("LINEAR_FAST_ACCOUNT_EMAILS", raising=False)
    monkeypatch.delenv("LINEAR_FAST_ACCOUNT_EMAIL", raising=False)
    monkeypatch.setenv("LINEAR_FAST_USER_ACCOUNT_ID", "ACC3")
    reader = LinearLocalReader()
    cache = _build_cache()

    reader._apply_account_scope(cache)

    assert set(cache.users.keys()) == {"U3"}
    assert set(cache.teams.keys()) == {"T2"}
    assert set(cache.issues.keys()) == {"I2"}


def test_scope_with_single_email_env_var(monkeypatch: pytest.MonkeyPatch):
    """Test singular LINEAR_FAST_ACCOUNT_EMAIL env var."""
    monkeypatch.delenv("LINEAR_FAST_ACCOUNT_EMAILS", raising=False)
    monkeypatch.setenv("LINEAR_FAST_ACCOUNT_EMAIL", "target@example.com")
    monkeypatch.delenv("LINEAR_FAST_USER_ACCOUNT_IDS", raising=False)
    reader = LinearLocalReader()
    cache = _build_cache()

    reader._apply_account_scope(cache)

    assert set(cache.users.keys()) == {"U1", "U2"}
    assert set(cache.teams.keys()) == {"T1"}


def test_scope_email_case_insensitivity(monkeypatch: pytest.MonkeyPatch):
    """Test that email matching: env var is stored as-is, user email is lowered.
    Since _parse_csv_env does not lowercase, uppercase env won't match lowercase user email.
    This tests the actual behavior (no match → ValueError)."""
    monkeypatch.setenv("LINEAR_FAST_ACCOUNT_EMAILS", "TARGET@EXAMPLE.COM")
    monkeypatch.delenv("LINEAR_FAST_USER_ACCOUNT_IDS", raising=False)
    reader = LinearLocalReader()
    cache = _build_cache()

    with pytest.raises(ValueError, match="no matching userAccountId found"):
        reader._apply_account_scope(cache)


def test_scope_with_whitespace_in_emails(monkeypatch: pytest.MonkeyPatch):
    """Test that whitespace is trimmed from email list."""
    monkeypatch.setenv("LINEAR_FAST_ACCOUNT_EMAILS", " target@example.com , other@example.com ")
    monkeypatch.delenv("LINEAR_FAST_USER_ACCOUNT_IDS", raising=False)
    reader = LinearLocalReader()
    cache = _build_cache()

    reader._apply_account_scope(cache)

    assert set(cache.users.keys()) == {"U1", "U2", "U3"}
    assert set(cache.teams.keys()) == {"T1", "T2"}


def test_scope_raises_when_user_account_id_not_found(monkeypatch: pytest.MonkeyPatch):
    """Test that ValueError is raised when account ID has no matching users."""
    monkeypatch.delenv("LINEAR_FAST_ACCOUNT_EMAILS", raising=False)
    monkeypatch.setenv("LINEAR_FAST_USER_ACCOUNT_IDS", "INVALID_ACC_ID")
    reader = LinearLocalReader()
    cache = _build_cache()

    with pytest.raises(ValueError, match="no matching organizationId found"):
        reader._apply_account_scope(cache)


def test_scope_raises_when_no_org_ids_found(monkeypatch: pytest.MonkeyPatch):
    """Test that ValueError is raised when no orgIds correspond to allowed accounts."""
    monkeypatch.setenv("LINEAR_FAST_ACCOUNT_EMAILS", "target@example.com")
    monkeypatch.delenv("LINEAR_FAST_USER_ACCOUNT_IDS", raising=False)
    reader = LinearLocalReader()
    cache = _build_cache()

    cache.users["U1"]["organizationId"] = None

    with pytest.raises(ValueError, match="no matching organizationId found"):
        reader._apply_account_scope(cache)


def test_scope_labels_with_no_team_id_included(monkeypatch: pytest.MonkeyPatch):
    """Test that labels with no teamId (global labels) are always included."""
    monkeypatch.setenv("LINEAR_FAST_ACCOUNT_EMAILS", "target@example.com")
    monkeypatch.delenv("LINEAR_FAST_USER_ACCOUNT_IDS", raising=False)
    reader = LinearLocalReader()
    cache = _build_cache()

    reader._apply_account_scope(cache)

    assert "L_GLOBAL" in cache.labels
    assert "L1" in cache.labels
    assert "L2" not in cache.labels


def test_scope_documents_with_no_project_filtered_by_creator(monkeypatch: pytest.MonkeyPatch):
    """Test that documents with no project are filtered by creator."""
    monkeypatch.setenv("LINEAR_FAST_ACCOUNT_EMAILS", "target@example.com")
    monkeypatch.delenv("LINEAR_FAST_USER_ACCOUNT_IDS", raising=False)
    reader = LinearLocalReader()
    cache = _build_cache()

    reader._apply_account_scope(cache)

    assert "D_NO_PROJECT" in cache.documents
    assert cache.documents["D_NO_PROJECT"]["creatorId"] == "U1"

    assert "D2" not in cache.documents


def test_scope_projects_with_lead_id_only(monkeypatch: pytest.MonkeyPatch):
    """Test projects that have leadId but no teamIds."""
    monkeypatch.setenv("LINEAR_FAST_ACCOUNT_EMAILS", "target@example.com")
    monkeypatch.delenv("LINEAR_FAST_USER_ACCOUNT_IDS", raising=False)
    reader = LinearLocalReader()
    cache = _build_cache()

    cache.projects["P_LEAD_ONLY"] = {
        "id": "P_LEAD_ONLY",
        "teamIds": [],
        "leadId": "U2",
        "memberIds": [],
        "statusId": "PS_LEAD",
    }
    cache.project_statuses["PS_LEAD"] = {"id": "PS_LEAD", "name": "Lead Only"}

    reader._apply_account_scope(cache)

    assert "P_LEAD_ONLY" in cache.projects
    assert "PS_LEAD" in cache.project_statuses


def test_scope_projects_with_member_ids_only(monkeypatch: pytest.MonkeyPatch):
    """Test projects that have memberIds but no teamIds."""
    monkeypatch.setenv("LINEAR_FAST_ACCOUNT_EMAILS", "target@example.com")
    monkeypatch.delenv("LINEAR_FAST_USER_ACCOUNT_IDS", raising=False)
    reader = LinearLocalReader()
    cache = _build_cache()

    cache.projects["P_MEMBER_ONLY"] = {
        "id": "P_MEMBER_ONLY",
        "teamIds": [],
        "leadId": None,
        "memberIds": ["U1", "U2"],
        "statusId": "PS_MEMBER",
    }
    cache.project_statuses["PS_MEMBER"] = {"id": "PS_MEMBER", "name": "Member Only"}

    reader._apply_account_scope(cache)

    assert "P_MEMBER_ONLY" in cache.projects


def test_scope_projects_excluded_when_members_out_of_scope(monkeypatch: pytest.MonkeyPatch):
    """Test projects excluded when all members/lead are out of scope."""
    monkeypatch.setenv("LINEAR_FAST_ACCOUNT_EMAILS", "target@example.com")
    monkeypatch.delenv("LINEAR_FAST_USER_ACCOUNT_IDS", raising=False)
    reader = LinearLocalReader()
    cache = _build_cache()

    cache.projects["P_OUT_OF_SCOPE"] = {
        "id": "P_OUT_OF_SCOPE",
        "teamIds": [],
        "leadId": "U3",
        "memberIds": ["U3"],
        "statusId": "PS_OUT",
    }

    reader._apply_account_scope(cache)

    assert "P_OUT_OF_SCOPE" not in cache.projects


def test_scope_initiatives_with_multiple_team_ids(monkeypatch: pytest.MonkeyPatch):
    """Test initiatives with multiple teamIds are included if any team is in scope."""
    monkeypatch.setenv("LINEAR_FAST_ACCOUNT_EMAILS", "target@example.com")
    monkeypatch.delenv("LINEAR_FAST_USER_ACCOUNT_IDS", raising=False)
    reader = LinearLocalReader()
    cache = _build_cache()

    cache.initiatives["N_MIXED"] = {
        "id": "N_MIXED",
        "teamIds": ["T1", "T2"],
        "ownerId": "U3",
    }

    reader._apply_account_scope(cache)

    assert "N_MIXED" in cache.initiatives


def test_scope_initiatives_excluded_when_owner_out_of_scope_and_no_teams(
    monkeypatch: pytest.MonkeyPatch,
):
    """Test initiatives excluded when owner is out of scope and no teamIds."""
    monkeypatch.setenv("LINEAR_FAST_ACCOUNT_EMAILS", "target@example.com")
    monkeypatch.delenv("LINEAR_FAST_USER_ACCOUNT_IDS", raising=False)
    reader = LinearLocalReader()
    cache = _build_cache()

    cache.initiatives["N_OUT_OF_SCOPE"] = {
        "id": "N_OUT_OF_SCOPE",
        "teamIds": [],
        "ownerId": "U3",
    }

    reader._apply_account_scope(cache)

    assert "N_OUT_OF_SCOPE" not in cache.initiatives


def test_scope_combined_email_and_account_id(monkeypatch: pytest.MonkeyPatch):
    """Test that email and account ID filters are combined with union."""
    monkeypatch.setenv("LINEAR_FAST_ACCOUNT_EMAILS", "target@example.com")
    monkeypatch.setenv("LINEAR_FAST_USER_ACCOUNT_IDS", "ACC3")
    reader = LinearLocalReader()
    cache = _build_cache()

    reader._apply_account_scope(cache)

    assert set(cache.users.keys()) == {"U1", "U2", "U3"}
    assert set(cache.teams.keys()) == {"T1", "T2"}
    assert set(cache.issues.keys()) == {"I1", "I2"}


def test_scope_comments_by_issue_rebuilt_after_filtering(monkeypatch: pytest.MonkeyPatch):
    """Test that comments_by_issue index is correctly rebuilt after filtering."""
    monkeypatch.setenv("LINEAR_FAST_ACCOUNT_EMAILS", "target@example.com")
    monkeypatch.delenv("LINEAR_FAST_USER_ACCOUNT_IDS", raising=False)
    reader = LinearLocalReader()
    cache = _build_cache()

    cache.comments_by_issue["I1"].append("ORPHAN_COMMENT")
    cache.comments["ORPHAN_COMMENT"] = {
        "id": "ORPHAN_COMMENT",
        "issueId": "I2",
    }

    reader._apply_account_scope(cache)

    assert cache.comments_by_issue == {"I1": ["C1"]}
    assert "ORPHAN_COMMENT" not in cache.comments


def test_scope_empty_team_ids_list_in_project(monkeypatch: pytest.MonkeyPatch):
    """Test projects with empty teamIds list fallback to leadId/memberIds."""
    monkeypatch.setenv("LINEAR_FAST_ACCOUNT_EMAILS", "target@example.com")
    monkeypatch.delenv("LINEAR_FAST_USER_ACCOUNT_IDS", raising=False)
    reader = LinearLocalReader()
    cache = _build_cache()

    cache.projects["P_EMPTY_TEAMS"] = {
        "id": "P_EMPTY_TEAMS",
        "teamIds": [],
        "leadId": "U1",
        "memberIds": [],
        "statusId": "PS_EMPTY",
    }
    cache.project_statuses["PS_EMPTY"] = {"id": "PS_EMPTY", "name": "Empty Teams"}

    reader._apply_account_scope(cache)

    assert "P_EMPTY_TEAMS" in cache.projects


def test_scope_is_account_scope_enabled_check(monkeypatch: pytest.MonkeyPatch):
    """Test _is_account_scope_enabled returns correct value."""
    monkeypatch.delenv("LINEAR_FAST_ACCOUNT_EMAILS", raising=False)
    monkeypatch.delenv("LINEAR_FAST_ACCOUNT_EMAIL", raising=False)
    monkeypatch.delenv("LINEAR_FAST_USER_ACCOUNT_IDS", raising=False)
    monkeypatch.delenv("LINEAR_FAST_USER_ACCOUNT_ID", raising=False)
    reader1 = LinearLocalReader()
    assert not reader1._is_account_scope_enabled()

    monkeypatch.setenv("LINEAR_FAST_ACCOUNT_EMAILS", "test@example.com")
    reader2 = LinearLocalReader()
    assert reader2._is_account_scope_enabled()

    monkeypatch.delenv("LINEAR_FAST_ACCOUNT_EMAILS")
    monkeypatch.setenv("LINEAR_FAST_USER_ACCOUNT_IDS", "ACC1")
    reader3 = LinearLocalReader()
    assert reader3._is_account_scope_enabled()
