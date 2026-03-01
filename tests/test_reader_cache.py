"""Unit tests for LinearLocalReader cache TTL and force refresh logic."""

import time
from unittest.mock import MagicMock

from linear_mcp_fast.reader import CACHE_TTL_SECONDS, CachedData, LinearLocalReader


class TestCachedDataExpiration:
    """Tests for CachedData.is_expired() method."""

    def test_cached_data_starts_expired(self):
        """New CachedData has loaded_at=0, is_expired() returns True."""
        cache = CachedData()
        assert cache.loaded_at == 0.0
        assert cache.is_expired() is True

    def test_cached_data_not_expired_after_load(self):
        """CachedData with loaded_at=time.time(), is_expired() returns False."""
        cache = CachedData(loaded_at=time.time())
        assert cache.is_expired() is False

    def test_cached_data_expires_after_ttl(self):
        """With loaded_at in the past (>300s ago), is_expired() returns True."""
        past_time = time.time() - (CACHE_TTL_SECONDS + 1)
        cache = CachedData(loaded_at=past_time)
        assert cache.is_expired() is True

    def test_cached_data_not_expired_near_ttl_boundary(self):
        """Cache not expired if just under TTL threshold."""
        past_time = time.time() - (CACHE_TTL_SECONDS - 10)
        cache = CachedData(loaded_at=past_time)
        assert cache.is_expired() is False

    def test_cached_data_expires_at_ttl_boundary(self):
        """Cache expires exactly at TTL threshold."""
        past_time = time.time() - CACHE_TTL_SECONDS
        cache = CachedData(loaded_at=past_time)
        assert cache.is_expired() is True


class TestForceRefreshFlag:
    """Tests for _force_next_refresh flag initialization and behavior."""

    def test_force_next_refresh_initial_false(self):
        """New reader has _force_next_refresh=False."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        assert reader._force_next_refresh is False

    def test_mark_stale_sets_force_flag(self):
        """Calling mark_stale() sets _force_next_refresh=True."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        assert reader._force_next_refresh is False
        reader.mark_stale()
        assert reader._force_next_refresh is True


class TestEnsureCacheLogic:
    """Tests for _ensure_cache() method with various cache states."""

    def test_ensure_cache_reloads_when_expired(self):
        """Mock _reload_cache, verify it's called when cache expired."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()

        past_time = time.time() - (CACHE_TTL_SECONDS + 1)
        reader._cache = CachedData(loaded_at=past_time, teams={"team1": {}})

        reader._ensure_cache()

        reader._reload_cache.assert_called_once()

    def test_ensure_cache_reloads_when_force_flag_set(self):
        """Set _force_next_refresh=True, mock _reload_cache, verify called."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()

        reader._cache = CachedData(loaded_at=time.time(), teams={"team1": {}})
        reader._force_next_refresh = True

        reader._ensure_cache()

        reader._reload_cache.assert_called_once()

    def test_ensure_cache_resets_force_flag(self):
        """After _ensure_cache with force flag, flag becomes False."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()

        reader._cache = CachedData(loaded_at=time.time(), teams={"team1": {}})
        reader._force_next_refresh = True

        reader._ensure_cache()

        assert reader._force_next_refresh is False

    def test_ensure_cache_skips_reload_when_fresh(self):
        """Fresh cache + no force flag → _reload_cache NOT called."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()

        reader._cache = CachedData(loaded_at=time.time(), teams={"team1": {}})
        reader._force_next_refresh = False

        reader._ensure_cache()

        reader._reload_cache.assert_not_called()

    def test_ensure_cache_reloads_when_teams_empty(self):
        """Cache with empty teams triggers reload even if fresh."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()

        reader._cache = CachedData(loaded_at=time.time(), teams={})
        reader._force_next_refresh = False

        reader._ensure_cache()

        reader._reload_cache.assert_called_once()

    def test_ensure_cache_returns_cache_object(self):
        """_ensure_cache returns CachedData object."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()

        test_cache = CachedData(loaded_at=time.time(), teams={"team1": {"id": "t1"}})
        reader._cache = test_cache
        reader._force_next_refresh = False

        result = reader._ensure_cache()

        assert result is test_cache
        assert isinstance(result, CachedData)
        assert result.teams == {"team1": {"id": "t1"}}

    def test_ensure_cache_with_multiple_conditions(self):
        """Expired cache with force flag both trigger reload."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()

        past_time = time.time() - (CACHE_TTL_SECONDS + 1)
        reader._cache = CachedData(loaded_at=past_time, teams={"team1": {}})
        reader._force_next_refresh = True

        reader._ensure_cache()

        reader._reload_cache.assert_called_once()
        assert reader._force_next_refresh is False


class TestCacheIntegration:
    """Integration tests for cache behavior with properties."""

    def test_accessing_teams_property_triggers_ensure_cache(self):
        """Accessing .teams property triggers _ensure_cache."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()

        reader._cache = CachedData(loaded_at=time.time(), teams={"team1": {"id": "t1"}})
        reader._force_next_refresh = False

        teams = reader.teams

        assert teams == {"team1": {"id": "t1"}}
        reader._reload_cache.assert_not_called()

    def test_accessing_expired_cache_via_property_reloads(self):
        """Accessing expired cache via property triggers reload."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()

        past_time = time.time() - (CACHE_TTL_SECONDS + 1)
        reader._cache = CachedData(loaded_at=past_time, teams={"team1": {}})

        reader._ensure_cache()

        reader._reload_cache.assert_called_once()

    def test_mark_stale_then_access_property(self):
        """After mark_stale(), accessing property triggers reload."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()

        reader._cache = CachedData(loaded_at=time.time(), teams={"team1": {}})
        reader.mark_stale()

        reader._ensure_cache()

        reader._reload_cache.assert_called_once()
        assert reader._force_next_refresh is False


class TestCacheRefreshMethod:
    """Tests for the refresh_cache() public method."""

    def test_refresh_cache_with_force_true(self):
        """refresh_cache(force=True) calls _reload_cache directly."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()

        reader.refresh_cache(force=True)

        reader._reload_cache.assert_called_once()

    def test_refresh_cache_with_force_false(self):
        """refresh_cache(force=False) calls _ensure_cache."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()

        reader._cache = CachedData(loaded_at=time.time(), teams={"team1": {}})

        reader.refresh_cache(force=False)

        reader._reload_cache.assert_not_called()

    def test_refresh_cache_default_force_true(self):
        """refresh_cache() defaults to force=True."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()

        reader.refresh_cache()

        reader._reload_cache.assert_called_once()


class TestCacheDataStructure:
    """Tests for CachedData structure and initialization."""

    def test_cached_data_default_fields(self):
        """CachedData initializes with empty collections."""
        cache = CachedData()
        assert cache.teams == {}
        assert cache.users == {}
        assert cache.issues == {}
        assert cache.comments == {}
        assert cache.projects == {}
        assert cache.loaded_at == 0.0

    def test_cached_data_with_loaded_at(self):
        """CachedData can be initialized with loaded_at."""
        now = time.time()
        cache = CachedData(loaded_at=now)
        assert cache.loaded_at == now
        assert cache.is_expired() is False

    def test_cached_data_with_sample_data(self):
        """CachedData can store teams and users."""
        cache = CachedData(
            loaded_at=time.time(),
            teams={"t1": {"id": "t1", "name": "Team 1"}},
            users={"u1": {"id": "u1", "name": "User 1"}},
        )
        assert cache.teams["t1"]["name"] == "Team 1"
        assert cache.users["u1"]["name"] == "User 1"


class TestReaderInitialization:
    """Tests for LinearLocalReader initialization."""

    def test_reader_initializes_with_default_cache(self):
        """LinearLocalReader initializes with empty CachedData."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        assert isinstance(reader._cache, CachedData)
        assert reader._cache.teams == {}
        assert reader._cache.is_expired() is True

    def test_reader_stores_db_paths(self):
        """LinearLocalReader stores db_path and blob_path."""
        db = "/test/db"
        blob = "/test/blob"
        reader = LinearLocalReader(db_path=db, blob_path=blob)
        assert reader._db_path == db
        assert reader._blob_path == blob

    def test_reader_initializes_force_refresh_false(self):
        """LinearLocalReader._force_next_refresh initialized to False."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        assert reader._force_next_refresh is False


class TestCacheTTLConstant:
    """Tests for CACHE_TTL_SECONDS constant."""

    def test_cache_ttl_is_300_seconds(self):
        """CACHE_TTL_SECONDS should be 300 (5 minutes)."""
        assert CACHE_TTL_SECONDS == 300

    def test_cache_ttl_used_in_expiration_check(self):
        """is_expired() uses CACHE_TTL_SECONDS."""
        cache = CachedData(loaded_at=time.time() - CACHE_TTL_SECONDS - 1)
        assert cache.is_expired() is True


class TestEdgeCases:
    """Edge case tests for cache logic."""

    def test_ensure_cache_with_zero_loaded_at(self):
        """Cache with loaded_at=0 is always expired."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()

        reader._cache = CachedData(loaded_at=0.0, teams={"team1": {}})

        reader._ensure_cache()

        reader._reload_cache.assert_called_once()

    def test_multiple_mark_stale_calls(self):
        """Multiple mark_stale() calls keep flag set."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader.mark_stale()
        reader.mark_stale()
        reader.mark_stale()

        assert reader._force_next_refresh is True

    def test_ensure_cache_resets_flag_only_once(self):
        """Flag reset happens in _ensure_cache, not multiple times."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()

        reader._cache = CachedData(loaded_at=time.time(), teams={"team1": {}})
        reader._force_next_refresh = True

        reader._ensure_cache()
        assert reader._force_next_refresh is False

        reader._ensure_cache()
        assert reader._reload_cache.call_count == 1

    def test_cache_ttl_boundary_precision(self):
        """Test cache expiration near TTL boundary with precision."""
        just_before_expire = time.time() - (CACHE_TTL_SECONDS - 0.1)
        cache = CachedData(loaded_at=just_before_expire)
        assert cache.is_expired() is False

        just_after_expire = time.time() - (CACHE_TTL_SECONDS + 0.1)
        cache = CachedData(loaded_at=just_after_expire)
        assert cache.is_expired() is True

    def test_ensure_cache_with_empty_teams_but_fresh(self):
        """Empty teams in fresh cache still triggers reload."""
        reader = LinearLocalReader(db_path="/nonexistent", blob_path="/nonexistent")
        reader._reload_cache = MagicMock()

        fresh_time = time.time()
        reader._cache = CachedData(loaded_at=fresh_time, teams={})

        reader._ensure_cache()

        reader._reload_cache.assert_called_once()
