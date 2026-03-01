from __future__ import annotations

from linear_mcp_fast.store_detector import (
    _is_comment_record,
    _is_cycle_record,
    _is_document_content_record,
    _is_document_record,
    _is_initiative_record,
    _is_issue_content_record,
    _is_issue_record,
    _is_label_record,
    _is_milestone_record,
    _is_project_record,
    _is_project_status_record,
    _is_project_update_record,
    _is_team_record,
    _is_user_record,
    _is_workflow_state_record,
)


class TestIsIssueRecord:
    """Tests for _is_issue_record function."""

    def test_valid_issue_record(self) -> None:
        """Test that a record with all required fields is recognized as issue."""
        record = {
            "number": 42,
            "teamId": "team123",
            "stateId": "state456",
            "title": "Fix bug",
            "extra_field": "ignored",
        }
        assert _is_issue_record(record)

    def test_missing_number(self) -> None:
        """Test that missing number field returns False."""
        record = {
            "teamId": "team123",
            "stateId": "state456",
            "title": "Fix bug",
        }
        assert not _is_issue_record(record)

    def test_missing_teamId(self) -> None:
        """Test that missing teamId field returns False."""
        record = {
            "number": 42,
            "stateId": "state456",
            "title": "Fix bug",
        }
        assert not _is_issue_record(record)

    def test_missing_stateId(self) -> None:
        """Test that missing stateId field returns False."""
        record = {
            "number": 42,
            "teamId": "team123",
            "title": "Fix bug",
        }
        assert not _is_issue_record(record)

    def test_missing_title(self) -> None:
        """Test that missing title field returns False."""
        record = {
            "number": 42,
            "teamId": "team123",
            "stateId": "state456",
        }
        assert not _is_issue_record(record)

    def test_empty_record(self) -> None:
        """Test that empty record returns False."""
        assert not _is_issue_record({})


class TestIsUserRecord:
    """Tests for _is_user_record function."""

    def test_valid_user_record(self) -> None:
        """Test that a record with all required fields is recognized as user."""
        record = {
            "name": "John",
            "displayName": "John Doe",
            "email": "john@example.com",
            "id": "user123",
        }
        assert _is_user_record(record)

    def test_missing_name(self) -> None:
        """Test that missing name field returns False."""
        record = {
            "displayName": "John Doe",
            "email": "john@example.com",
        }
        assert not _is_user_record(record)

    def test_missing_displayName(self) -> None:
        """Test that missing displayName field returns False."""
        record = {
            "name": "John",
            "email": "john@example.com",
        }
        assert not _is_user_record(record)

    def test_missing_email(self) -> None:
        """Test that missing email field returns False."""
        record = {
            "name": "John",
            "displayName": "John Doe",
        }
        assert not _is_user_record(record)

    def test_empty_record(self) -> None:
        """Test that empty record returns False."""
        assert not _is_user_record({})


class TestIsTeamRecord:
    """Tests for _is_team_record function."""

    def test_valid_team_record(self) -> None:
        """Test that a record with valid key and name is recognized as team."""
        record = {
            "key": "TEAM",
            "name": "Engineering",
        }
        assert _is_team_record(record)

    def test_valid_team_record_with_extra_fields(self) -> None:
        """Test that extra fields don't affect team detection."""
        record = {
            "key": "ENG",
            "name": "Engineering",
            "color": "blue",
            "id": "team123",
        }
        assert _is_team_record(record)

    def test_missing_key(self) -> None:
        """Test that missing key field returns False."""
        record = {"name": "Engineering"}
        assert not _is_team_record(record)

    def test_missing_name(self) -> None:
        """Test that missing name field returns False."""
        record = {"key": "ENG"}
        assert not _is_team_record(record)

    def test_key_lowercase(self) -> None:
        """Test that lowercase key returns False."""
        record = {
            "key": "eng",
            "name": "Engineering",
        }
        assert not _is_team_record(record)

    def test_key_mixed_case(self) -> None:
        """Test that mixed case key returns False."""
        record = {
            "key": "Eng",
            "name": "Engineering",
        }
        assert not _is_team_record(record)

    def test_key_with_numbers(self) -> None:
        """Test that key with numbers returns False."""
        record = {
            "key": "ENG1",
            "name": "Engineering",
        }
        assert not _is_team_record(record)

    def test_key_with_special_chars(self) -> None:
        """Test that key with special characters returns False."""
        record = {
            "key": "ENG-",
            "name": "Engineering",
        }
        assert not _is_team_record(record)

    def test_key_too_long(self) -> None:
        """Test that key longer than 10 characters returns False."""
        record = {
            "key": "ENGINEERING",  # 11 characters
            "name": "Engineering",
        }
        assert not _is_team_record(record)

    def test_key_exactly_10_chars(self) -> None:
        """Test that key with exactly 10 characters is accepted."""
        record = {
            "key": "ENGINEERING",  # wait, this is 11
            "name": "Engineering",
        }
        # Let me fix this - ENGINEERI is 9, ENGINEERIN is 10
        record = {
            "key": "ENGINEERIN",  # exactly 10
            "name": "Engineering",
        }
        assert _is_team_record(record)

    def test_key_not_string(self) -> None:
        """Test that non-string key returns False."""
        record = {
            "key": 123,
            "name": "Engineering",
        }
        assert not _is_team_record(record)

    def test_key_single_char(self) -> None:
        """Test that single uppercase letter key is valid."""
        record = {
            "key": "A",
            "name": "Team A",
        }
        assert _is_team_record(record)

    def test_empty_record(self) -> None:
        """Test that empty record returns False."""
        assert not _is_team_record({})


class TestIsWorkflowStateRecord:
    """Tests for _is_workflow_state_record function."""

    def test_valid_workflow_state_started(self) -> None:
        """Test that record with type 'started' is recognized."""
        record = {
            "name": "In Progress",
            "type": "started",
            "color": "blue",
            "teamId": "team123",
        }
        assert _is_workflow_state_record(record)

    def test_valid_workflow_state_unstarted(self) -> None:
        """Test that record with type 'unstarted' is recognized."""
        record = {
            "name": "Todo",
            "type": "unstarted",
            "color": "gray",
            "teamId": "team123",
        }
        assert _is_workflow_state_record(record)

    def test_valid_workflow_state_completed(self) -> None:
        """Test that record with type 'completed' is recognized."""
        record = {
            "name": "Done",
            "type": "completed",
            "color": "green",
            "teamId": "team123",
        }
        assert _is_workflow_state_record(record)

    def test_valid_workflow_state_canceled(self) -> None:
        """Test that record with type 'canceled' is recognized."""
        record = {
            "name": "Canceled",
            "type": "canceled",
            "color": "red",
            "teamId": "team123",
        }
        assert _is_workflow_state_record(record)

    def test_valid_workflow_state_backlog(self) -> None:
        """Test that record with type 'backlog' is recognized."""
        record = {
            "name": "Backlog",
            "type": "backlog",
            "color": "yellow",
            "teamId": "team123",
        }
        assert _is_workflow_state_record(record)

    def test_missing_name(self) -> None:
        """Test that missing name field returns False."""
        record = {
            "type": "started",
            "color": "blue",
            "teamId": "team123",
        }
        assert not _is_workflow_state_record(record)

    def test_missing_type(self) -> None:
        """Test that missing type field returns False."""
        record = {
            "name": "In Progress",
            "color": "blue",
            "teamId": "team123",
        }
        assert not _is_workflow_state_record(record)

    def test_missing_color(self) -> None:
        """Test that missing color field returns False."""
        record = {
            "name": "In Progress",
            "type": "started",
            "teamId": "team123",
        }
        assert not _is_workflow_state_record(record)

    def test_missing_teamId(self) -> None:
        """Test that missing teamId field returns False."""
        record = {
            "name": "In Progress",
            "type": "started",
            "color": "blue",
        }
        assert not _is_workflow_state_record(record)

    def test_invalid_type(self) -> None:
        """Test that invalid type value returns False."""
        record = {
            "name": "In Progress",
            "type": "invalid",
            "color": "blue",
            "teamId": "team123",
        }
        assert not _is_workflow_state_record(record)

    def test_empty_record(self) -> None:
        """Test that empty record returns False."""
        assert not _is_workflow_state_record({})


class TestIsCommentRecord:
    """Tests for _is_comment_record function."""

    def test_valid_comment_record(self) -> None:
        """Test that a record with all required fields is recognized as comment."""
        record = {
            "issueId": "issue123",
            "userId": "user456",
            "bodyData": "Some comment text",
            "createdAt": "2025-01-01T00:00:00Z",
            "id": "comment789",
        }
        assert _is_comment_record(record)

    def test_missing_issueId(self) -> None:
        """Test that missing issueId field returns False."""
        record = {
            "userId": "user456",
            "bodyData": "Some comment text",
            "createdAt": "2025-01-01T00:00:00Z",
        }
        assert not _is_comment_record(record)

    def test_missing_userId(self) -> None:
        """Test that missing userId field returns False."""
        record = {
            "issueId": "issue123",
            "bodyData": "Some comment text",
            "createdAt": "2025-01-01T00:00:00Z",
        }
        assert not _is_comment_record(record)

    def test_missing_bodyData(self) -> None:
        """Test that missing bodyData field returns False."""
        record = {
            "issueId": "issue123",
            "userId": "user456",
            "createdAt": "2025-01-01T00:00:00Z",
        }
        assert not _is_comment_record(record)

    def test_missing_createdAt(self) -> None:
        """Test that missing createdAt field returns False."""
        record = {
            "issueId": "issue123",
            "userId": "user456",
            "bodyData": "Some comment text",
        }
        assert not _is_comment_record(record)

    def test_empty_record(self) -> None:
        """Test that empty record returns False."""
        assert not _is_comment_record({})


class TestIsProjectRecord:
    """Tests for _is_project_record function."""

    def test_valid_project_record(self) -> None:
        """Test that a record with all required fields is recognized as project."""
        record = {
            "name": "Q1 Planning",
            "teamIds": ["team1", "team2"],
            "slugId": "slug123",
            "statusId": "status456",
            "memberIds": ["user1", "user2"],
            "description": "Planning for Q1",
        }
        assert _is_project_record(record)

    def test_missing_name(self) -> None:
        """Test that missing name field returns False."""
        record = {
            "teamIds": ["team1"],
            "slugId": "slug123",
            "statusId": "status456",
            "memberIds": ["user1"],
        }
        assert not _is_project_record(record)

    def test_missing_teamIds(self) -> None:
        """Test that missing teamIds field returns False."""
        record = {
            "name": "Q1 Planning",
            "slugId": "slug123",
            "statusId": "status456",
            "memberIds": ["user1"],
        }
        assert not _is_project_record(record)

    def test_missing_slugId(self) -> None:
        """Test that missing slugId field returns False."""
        record = {
            "name": "Q1 Planning",
            "teamIds": ["team1"],
            "statusId": "status456",
            "memberIds": ["user1"],
        }
        assert not _is_project_record(record)

    def test_missing_statusId(self) -> None:
        """Test that missing statusId field returns False."""
        record = {
            "name": "Q1 Planning",
            "teamIds": ["team1"],
            "slugId": "slug123",
            "memberIds": ["user1"],
        }
        assert not _is_project_record(record)

    def test_missing_memberIds(self) -> None:
        """Test that missing memberIds field returns False."""
        record = {
            "name": "Q1 Planning",
            "teamIds": ["team1"],
            "slugId": "slug123",
            "statusId": "status456",
        }
        assert not _is_project_record(record)

    def test_empty_record(self) -> None:
        """Test that empty record returns False."""
        assert not _is_project_record({})


class TestIsIssueContentRecord:
    """Tests for _is_issue_content_record function."""

    def test_valid_issue_content_record(self) -> None:
        """Test that a record with all required fields is recognized as issue content."""
        record = {
            "issueId": "issue123",
            "contentState": b"encoded_yjs_data",
            "createdAt": "2025-01-01T00:00:00Z",
        }
        assert _is_issue_content_record(record)

    def test_missing_issueId(self) -> None:
        """Test that missing issueId field returns False."""
        record = {
            "contentState": b"encoded_yjs_data",
        }
        assert not _is_issue_content_record(record)

    def test_missing_contentState(self) -> None:
        """Test that missing contentState field returns False."""
        record = {
            "issueId": "issue123",
        }
        assert not _is_issue_content_record(record)

    def test_empty_record(self) -> None:
        """Test that empty record returns False."""
        assert not _is_issue_content_record({})


class TestIsLabelRecord:
    """Tests for _is_label_record function."""

    def test_valid_label_record(self) -> None:
        """Test that a record with all required fields is recognized as label."""
        record = {
            "name": "bug",
            "color": "red",
            "isGroup": False,
            "id": "label123",
        }
        assert _is_label_record(record)

    def test_valid_label_record_group(self) -> None:
        """Test that a group label is recognized."""
        record = {
            "name": "Category",
            "color": "blue",
            "isGroup": True,
        }
        assert _is_label_record(record)

    def test_missing_name(self) -> None:
        """Test that missing name field returns False."""
        record = {
            "color": "red",
            "isGroup": False,
        }
        assert not _is_label_record(record)

    def test_missing_color(self) -> None:
        """Test that missing color field returns False."""
        record = {
            "name": "bug",
            "isGroup": False,
        }
        assert not _is_label_record(record)

    def test_missing_isGroup(self) -> None:
        """Test that missing isGroup field returns False."""
        record = {
            "name": "bug",
            "color": "red",
        }
        assert not _is_label_record(record)

    def test_empty_record(self) -> None:
        """Test that empty record returns False."""
        assert not _is_label_record({})


class TestIsInitiativeRecord:
    """Tests for _is_initiative_record function."""

    def test_valid_initiative_record(self) -> None:
        """Test that a record with all required fields is recognized as initiative."""
        record = {
            "name": "Q1 Goals",
            "ownerId": "user123",
            "slugId": "slug456",
            "frequencyResolution": "quarter",
            "id": "init789",
        }
        assert _is_initiative_record(record)

    def test_missing_name(self) -> None:
        """Test that missing name field returns False."""
        record = {
            "ownerId": "user123",
            "slugId": "slug456",
            "frequencyResolution": "quarter",
        }
        assert not _is_initiative_record(record)

    def test_missing_ownerId(self) -> None:
        """Test that missing ownerId field returns False."""
        record = {
            "name": "Q1 Goals",
            "slugId": "slug456",
            "frequencyResolution": "quarter",
        }
        assert not _is_initiative_record(record)

    def test_missing_slugId(self) -> None:
        """Test that missing slugId field returns False."""
        record = {
            "name": "Q1 Goals",
            "ownerId": "user123",
            "frequencyResolution": "quarter",
        }
        assert not _is_initiative_record(record)

    def test_missing_frequencyResolution(self) -> None:
        """Test that missing frequencyResolution field returns False."""
        record = {
            "name": "Q1 Goals",
            "ownerId": "user123",
            "slugId": "slug456",
        }
        assert not _is_initiative_record(record)

    def test_empty_record(self) -> None:
        """Test that empty record returns False."""
        assert not _is_initiative_record({})


class TestIsProjectStatusRecord:
    """Tests for _is_project_status_record function."""

    def test_valid_project_status_record(self) -> None:
        """Test that a record with all required fields is recognized as project status."""
        record = {
            "name": "On Track",
            "color": "green",
            "position": 0,
            "type": "active",
            "indefinite": False,
            "id": "status123",
        }
        assert _is_project_status_record(record)

    def test_missing_name(self) -> None:
        """Test that missing name field returns False."""
        record = {
            "color": "green",
            "position": 0,
            "type": "active",
            "indefinite": False,
        }
        assert not _is_project_status_record(record)

    def test_missing_color(self) -> None:
        """Test that missing color field returns False."""
        record = {
            "name": "On Track",
            "position": 0,
            "type": "active",
            "indefinite": False,
        }
        assert not _is_project_status_record(record)

    def test_missing_position(self) -> None:
        """Test that missing position field returns False."""
        record = {
            "name": "On Track",
            "color": "green",
            "type": "active",
            "indefinite": False,
        }
        assert not _is_project_status_record(record)

    def test_missing_type(self) -> None:
        """Test that missing type field returns False."""
        record = {
            "name": "On Track",
            "color": "green",
            "position": 0,
            "indefinite": False,
        }
        assert not _is_project_status_record(record)

    def test_missing_indefinite(self) -> None:
        """Test that missing indefinite field returns False."""
        record = {
            "name": "On Track",
            "color": "green",
            "position": 0,
            "type": "active",
        }
        assert not _is_project_status_record(record)

    def test_with_teamId_returns_false(self) -> None:
        """Test that presence of teamId field returns False (differentiates from workflow state)."""
        record = {
            "name": "On Track",
            "color": "green",
            "position": 0,
            "type": "active",
            "indefinite": False,
            "teamId": "team123",  # This should make it fail
        }
        assert not _is_project_status_record(record)

    def test_empty_record(self) -> None:
        """Test that empty record returns False."""
        assert not _is_project_status_record({})


class TestIsCycleRecord:
    """Tests for _is_cycle_record function."""

    def test_valid_cycle_record(self) -> None:
        """Test that a record with all required fields is recognized as cycle."""
        record = {
            "number": 1,
            "teamId": "team123",
            "startsAt": "2025-01-01T00:00:00Z",
            "endsAt": "2025-03-31T23:59:59Z",
            "name": "Q1 2025",
        }
        assert _is_cycle_record(record)

    def test_missing_number(self) -> None:
        """Test that missing number field returns False."""
        record = {
            "teamId": "team123",
            "startsAt": "2025-01-01T00:00:00Z",
            "endsAt": "2025-03-31T23:59:59Z",
        }
        assert not _is_cycle_record(record)

    def test_missing_teamId(self) -> None:
        """Test that missing teamId field returns False."""
        record = {
            "number": 1,
            "startsAt": "2025-01-01T00:00:00Z",
            "endsAt": "2025-03-31T23:59:59Z",
        }
        assert not _is_cycle_record(record)

    def test_missing_startsAt(self) -> None:
        """Test that missing startsAt field returns False."""
        record = {
            "number": 1,
            "teamId": "team123",
            "endsAt": "2025-03-31T23:59:59Z",
        }
        assert not _is_cycle_record(record)

    def test_missing_endsAt(self) -> None:
        """Test that missing endsAt field returns False."""
        record = {
            "number": 1,
            "teamId": "team123",
            "startsAt": "2025-01-01T00:00:00Z",
        }
        assert not _is_cycle_record(record)

    def test_empty_record(self) -> None:
        """Test that empty record returns False."""
        assert not _is_cycle_record({})


class TestIsDocumentRecord:
    """Tests for _is_document_record function."""

    def test_valid_document_record(self) -> None:
        """Test that a record with all required fields is recognized as document."""
        record = {
            "title": "Q1 Planning",
            "slugId": "slug123",
            "projectId": "project456",
            "sortOrder": 1.0,
            "createdAt": "2025-01-01T00:00:00Z",
        }
        assert _is_document_record(record)

    def test_missing_title(self) -> None:
        """Test that missing title field returns False."""
        record = {
            "slugId": "slug123",
            "projectId": "project456",
            "sortOrder": 1.0,
        }
        assert not _is_document_record(record)

    def test_missing_slugId(self) -> None:
        """Test that missing slugId field returns False."""
        record = {
            "title": "Q1 Planning",
            "projectId": "project456",
            "sortOrder": 1.0,
        }
        assert not _is_document_record(record)

    def test_missing_projectId(self) -> None:
        """Test that missing projectId field returns False."""
        record = {
            "title": "Q1 Planning",
            "slugId": "slug123",
            "sortOrder": 1.0,
        }
        assert not _is_document_record(record)

    def test_missing_sortOrder(self) -> None:
        """Test that missing sortOrder field returns False."""
        record = {
            "title": "Q1 Planning",
            "slugId": "slug123",
            "projectId": "project456",
        }
        assert not _is_document_record(record)

    def test_with_number_returns_false(self) -> None:
        """Test that presence of number field (issue field) returns False."""
        record = {
            "title": "Q1 Planning",
            "slugId": "slug123",
            "projectId": "project456",
            "sortOrder": 1.0,
            "number": 42,  # This makes it look like an issue
        }
        assert not _is_document_record(record)

    def test_with_stateId_returns_false(self) -> None:
        """Test that presence of stateId field (issue field) returns False."""
        record = {
            "title": "Q1 Planning",
            "slugId": "slug123",
            "projectId": "project456",
            "sortOrder": 1.0,
            "stateId": "state789",  # This makes it look like an issue
        }
        assert not _is_document_record(record)

    def test_with_both_number_and_stateId_returns_false(self) -> None:
        """Test that presence of both number and stateId returns False."""
        record = {
            "title": "Q1 Planning",
            "slugId": "slug123",
            "projectId": "project456",
            "sortOrder": 1.0,
            "number": 42,
            "stateId": "state789",
        }
        assert not _is_document_record(record)

    def test_empty_record(self) -> None:
        """Test that empty record returns False."""
        assert not _is_document_record({})


class TestIsDocumentContentRecord:
    """Tests for _is_document_content_record function."""

    def test_valid_document_content_record(self) -> None:
        """Test that a record with all required fields is recognized as document content."""
        record = {
            "documentContentId": "doccontent123",
            "contentData": b"encoded_yjs_data",
            "createdAt": "2025-01-01T00:00:00Z",
        }
        assert _is_document_content_record(record)

    def test_missing_documentContentId(self) -> None:
        """Test that missing documentContentId field returns False."""
        record = {
            "contentData": b"encoded_yjs_data",
        }
        assert not _is_document_content_record(record)

    def test_missing_contentData(self) -> None:
        """Test that missing contentData field returns False."""
        record = {
            "documentContentId": "doccontent123",
        }
        assert not _is_document_content_record(record)

    def test_empty_record(self) -> None:
        """Test that empty record returns False."""
        assert not _is_document_content_record({})


class TestIsMilestoneRecord:
    """Tests for _is_milestone_record function."""

    def test_valid_milestone_with_current_progress(self) -> None:
        """Test that milestone with currentProgress is recognized."""
        record = {
            "name": "Alpha Release",
            "projectId": "project123",
            "sortOrder": 1.0,
            "currentProgress": 50,
        }
        assert _is_milestone_record(record)

    def test_valid_milestone_with_target_date(self) -> None:
        """Test that milestone with targetDate is recognized."""
        record = {
            "name": "Beta Release",
            "projectId": "project123",
            "sortOrder": 2.0,
            "targetDate": "2025-06-30T23:59:59Z",
        }
        assert _is_milestone_record(record)

    def test_valid_milestone_with_both_progress_and_date(self) -> None:
        """Test that milestone with both currentProgress and targetDate is recognized."""
        record = {
            "name": "Gamma Release",
            "projectId": "project123",
            "sortOrder": 3.0,
            "currentProgress": 75,
            "targetDate": "2025-12-31T23:59:59Z",
        }
        assert _is_milestone_record(record)

    def test_missing_name(self) -> None:
        """Test that missing name field returns False."""
        record = {
            "projectId": "project123",
            "sortOrder": 1.0,
            "currentProgress": 50,
        }
        assert not _is_milestone_record(record)

    def test_missing_projectId(self) -> None:
        """Test that missing projectId field returns False."""
        record = {
            "name": "Alpha Release",
            "sortOrder": 1.0,
            "currentProgress": 50,
        }
        assert not _is_milestone_record(record)

    def test_missing_sortOrder(self) -> None:
        """Test that missing sortOrder field returns False."""
        record = {
            "name": "Alpha Release",
            "projectId": "project123",
            "currentProgress": 50,
        }
        assert not _is_milestone_record(record)

    def test_missing_progress_and_date(self) -> None:
        """Test that missing both currentProgress and targetDate returns False."""
        record = {
            "name": "Alpha Release",
            "projectId": "project123",
            "sortOrder": 1.0,
        }
        assert not _is_milestone_record(record)

    def test_empty_record(self) -> None:
        """Test that empty record returns False."""
        assert not _is_milestone_record({})


class TestIsProjectUpdateRecord:
    """Tests for _is_project_update_record function."""

    def test_valid_project_update_with_projectId(self) -> None:
        """Test that project update with body and projectId is recognized."""
        record = {
            "body": "Updated Q1 status",
            "projectId": "project123",
            "createdAt": "2025-01-01T00:00:00Z",
        }
        assert _is_project_update_record(record)

    def test_valid_project_update_with_health(self) -> None:
        """Test that project update with body and health is recognized."""
        record = {
            "body": "All systems healthy",
            "health": "green",
            "createdAt": "2025-01-01T00:00:00Z",
        }
        assert _is_project_update_record(record)

    def test_valid_project_update_with_both_projectId_and_health(self) -> None:
        """Test that project update with body, projectId, and health is recognized."""
        record = {
            "body": "Q1 status update",
            "projectId": "project123",
            "health": "yellow",
        }
        assert _is_project_update_record(record)

    def test_missing_body(self) -> None:
        """Test that missing body field returns False."""
        record = {
            "projectId": "project123",
        }
        assert not _is_project_update_record(record)

    def test_missing_projectId_and_health(self) -> None:
        """Test that missing both projectId and health returns False."""
        record = {
            "body": "Some update",
        }
        assert not _is_project_update_record(record)

    def test_with_issueId_returns_false(self) -> None:
        """Test that presence of issueId field (comment field) returns False."""
        record = {
            "body": "Some update",
            "projectId": "project123",
            "issueId": "issue456",  # This makes it look like a comment
        }
        assert not _is_project_update_record(record)

    def test_empty_record(self) -> None:
        """Test that empty record returns False."""
        assert not _is_project_update_record({})
