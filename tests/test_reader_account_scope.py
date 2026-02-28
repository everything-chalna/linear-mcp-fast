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
    }
    cache.teams = {
        "T1": {"id": "T1", "key": "ORG1", "name": "Org1 Team", "organizationId": "ORG1"},
        "T2": {"id": "T2", "key": "ORG2", "name": "Org2 Team", "organizationId": "ORG2"},
    }
    cache.states = {
        "S1": {"id": "S1", "teamId": "T1", "type": "started", "name": "In Progress"},
        "S2": {"id": "S2", "teamId": "T2", "type": "started", "name": "In Progress"},
    }
    cache.issues = {
        "I1": {"id": "I1", "teamId": "T1", "stateId": "S1", "projectId": "P1"},
        "I2": {"id": "I2", "teamId": "T2", "stateId": "S2", "projectId": "P2"},
    }
    cache.issue_content = {"I1": "org1", "I2": "org2"}
    cache.comments = {
        "C1": {"id": "C1", "issueId": "I1"},
        "C2": {"id": "C2", "issueId": "I2"},
    }
    cache.comments_by_issue = {"I1": ["C1"], "I2": ["C2"]}
    cache.projects = {
        "P1": {"id": "P1", "teamIds": ["T1"], "statusId": "PS1", "memberIds": ["U2"]},
        "P2": {"id": "P2", "teamIds": ["T2"], "statusId": "PS2", "memberIds": ["U3"]},
    }
    cache.labels = {
        "L1": {"id": "L1", "teamId": "T1"},
        "L2": {"id": "L2", "teamId": "T2"},
    }
    cache.initiatives = {
        "N1": {"id": "N1", "teamIds": ["T1"], "ownerId": "U1"},
        "N2": {"id": "N2", "teamIds": ["T2"], "ownerId": "U3"},
    }
    cache.cycles = {
        "CY1": {"id": "CY1", "teamId": "T1"},
        "CY2": {"id": "CY2", "teamId": "T2"},
    }
    cache.documents = {
        "D1": {"id": "D1", "projectId": "P1", "creatorId": "U2"},
        "D2": {"id": "D2", "projectId": "P2", "creatorId": "U3"},
    }
    cache.milestones = {
        "M1": {"id": "M1", "projectId": "P1"},
        "M2": {"id": "M2", "projectId": "P2"},
    }
    cache.project_updates = {
        "UP1": {"id": "UP1", "projectId": "P1"},
        "UP2": {"id": "UP2", "projectId": "P2"},
    }
    cache.project_statuses = {
        "PS1": {"id": "PS1", "name": "On Track"},
        "PS2": {"id": "PS2", "name": "At Risk"},
    }
    return cache


def test_apply_account_scope_filters_by_email(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LINEAR_FAST_ACCOUNT_EMAILS", "target@example.com")
    monkeypatch.delenv("LINEAR_FAST_USER_ACCOUNT_IDS", raising=False)
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
    assert set(cache.labels.keys()) == {"L1"}
    assert set(cache.initiatives.keys()) == {"N1"}
    assert set(cache.cycles.keys()) == {"CY1"}
    assert set(cache.documents.keys()) == {"D1"}
    assert set(cache.milestones.keys()) == {"M1"}
    assert set(cache.project_updates.keys()) == {"UP1"}
    assert set(cache.project_statuses.keys()) == {"PS1"}


def test_apply_account_scope_raises_when_email_not_found(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LINEAR_FAST_ACCOUNT_EMAILS", "missing@example.com")
    monkeypatch.delenv("LINEAR_FAST_USER_ACCOUNT_IDS", raising=False)
    reader = LinearLocalReader()
    cache = _build_cache()

    with pytest.raises(ValueError):
        reader._apply_account_scope(cache)
