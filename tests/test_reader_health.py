from __future__ import annotations

import time

from linear_mcp_fast.reader import LinearLocalReader


def test_initial_health_is_not_degraded():
    """New reader starts healthy."""
    reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")

    assert reader.is_degraded() is False
    assert reader._health.degraded is False
    assert reader._health.reason is None
    assert reader._health.failure_count == 0
    assert reader._health.last_error is None
    assert reader._health.last_error_at is None
    assert reader._health.last_success_at is None


def test_set_degraded_updates_health():
    """Sets degraded=True, increments failure_count, records reason."""
    reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
    reason = "Database connection failed"

    reader._set_degraded(reason)

    assert reader._health.degraded is True
    assert reader._health.reason == reason
    assert reader._health.failure_count == 1
    assert reader._health.last_error == reason
    assert reader._health.last_error_at is not None


def test_set_degraded_increments_failure_count():
    """Calling _set_degraded multiple times increments failure_count."""
    reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")

    reader._set_degraded("Error 1")
    assert reader._health.failure_count == 1

    reader._set_degraded("Error 2")
    assert reader._health.failure_count == 2

    reader._set_degraded("Error 3")
    assert reader._health.failure_count == 3


def test_set_healthy_resets_state():
    """Resets degraded, reason, failure_count."""
    reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")

    # First, set degraded state
    reader._set_degraded("Some error")
    assert reader._health.degraded is True
    assert reader._health.reason == "Some error"
    assert reader._health.failure_count == 1

    # Now restore health
    reader._set_healthy()

    assert reader._health.degraded is False
    assert reader._health.reason is None
    assert reader._health.failure_count == 0
    assert reader._health.last_success_at is not None


def test_set_healthy_resets_failure_count_after_multiple_failures():
    """After 5 failures, _set_healthy resets failure_count to 0."""
    reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")

    # Simulate multiple failures
    for i in range(5):
        reader._set_degraded(f"Error {i+1}")
    assert reader._health.failure_count == 5

    # Restore health
    reader._set_healthy()

    assert reader._health.failure_count == 0
    assert reader._health.degraded is False


def test_get_health_returns_dict():
    """Returns dict with expected keys."""
    reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")

    health = reader.get_health()

    assert isinstance(health, dict)
    assert "degraded" in health
    assert "reason" in health
    assert "failureCount" in health
    assert "lastError" in health
    assert "lastErrorAt" in health
    assert "lastSuccessAt" in health
    assert "loadedAt" in health
    assert "ttlSeconds" in health
    assert "scopeAccountEmails" in health
    assert "scopeUserAccountIds" in health


def test_get_health_returns_correct_values():
    """get_health returns dict with current health state values."""
    reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")

    # Initial state
    health = reader.get_health()
    assert health["degraded"] is False
    assert health["reason"] is None
    assert health["failureCount"] == 0
    assert health["lastError"] is None

    # After degradation
    reader._set_degraded("Connection timeout")
    health = reader.get_health()
    assert health["degraded"] is True
    assert health["reason"] == "Connection timeout"
    assert health["failureCount"] == 1
    assert health["lastError"] == "Connection timeout"
    assert health["lastErrorAt"] is not None


def test_is_degraded_reflects_state():
    """is_degraded returns True when _health.degraded is True."""
    reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")

    # Initial state
    assert reader.is_degraded() is False

    # After degradation
    reader._set_degraded("Cache expired")
    assert reader.is_degraded() is True

    # After recovery
    reader._set_healthy()
    assert reader.is_degraded() is False


def test_set_degraded_updates_last_error_at_timestamp():
    """_set_degraded updates last_error_at with current timestamp."""
    reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")

    before = time.time()
    reader._set_degraded("Error message")
    after = time.time()

    assert reader._health.last_error_at is not None
    assert before <= reader._health.last_error_at <= after


def test_set_healthy_updates_last_success_at_timestamp():
    """_set_healthy updates last_success_at with current timestamp."""
    reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")

    # First degrade
    reader._set_degraded("Error")

    before = time.time()
    reader._set_healthy()
    after = time.time()

    assert reader._health.last_success_at is not None
    assert before <= reader._health.last_success_at <= after


def test_multiple_degradation_cycles():
    """Health state correctly reflects multiple degradation and recovery cycles."""
    reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")

    # Cycle 1: degrade and recover
    reader._set_degraded("Error 1")
    assert reader.is_degraded() is True
    assert reader._health.failure_count == 1

    reader._set_healthy()
    assert reader.is_degraded() is False
    assert reader._health.failure_count == 0

    # Cycle 2: multiple failures then recover
    reader._set_degraded("Error 2a")
    reader._set_degraded("Error 2b")
    reader._set_degraded("Error 2c")
    assert reader._health.failure_count == 3
    assert reader._health.reason == "Error 2c"
    assert reader._health.last_error == "Error 2c"

    reader._set_healthy()
    assert reader.is_degraded() is False
    assert reader._health.failure_count == 0
    assert reader._health.reason is None


def test_set_degraded_preserves_last_error_history():
    """_set_degraded always updates last_error to most recent error."""
    reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")

    reader._set_degraded("Error A")
    assert reader._health.last_error == "Error A"

    reader._set_degraded("Error B")
    assert reader._health.last_error == "Error B"
    assert reader._health.reason == "Error B"


def test_get_health_with_cache_loaded_at():
    """get_health includes cache loaded_at timestamp from CachedData."""
    reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")

    # Set a custom loaded_at time
    test_time = time.time()
    reader._cache.loaded_at = test_time

    health = reader.get_health()
    assert health["loadedAt"] == test_time


def test_get_health_ttl_seconds():
    """get_health includes correct TTL value."""
    reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")

    health = reader.get_health()
    assert health["ttlSeconds"] == 300  # CACHE_TTL_SECONDS


def test_get_health_scope_emails_empty():
    """get_health returns empty scope account emails when none configured."""
    reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")

    health = reader.get_health()
    assert health["scopeAccountEmails"] == []
    assert isinstance(health["scopeAccountEmails"], list)


def test_get_health_scope_user_account_ids_empty():
    """get_health returns empty scope user account IDs when none configured."""
    reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")

    health = reader.get_health()
    assert health["scopeUserAccountIds"] == []
    assert isinstance(health["scopeUserAccountIds"], list)
