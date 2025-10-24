"""Tests for cache manager."""

import time
from unittest.mock import Mock

import pytest

from mm_mcp.cache import CacheEntry, CacheManager


class TestCacheEntry:
    """Tests for CacheEntry class."""

    def test_cache_entry_creation(self):
        """Test creating a cache entry."""
        value = {"id": "123", "name": "test"}
        ttl = 300.0
        entry = CacheEntry(value, ttl)

        assert entry.value == value
        assert entry.expires_at > time.time()

    def test_cache_entry_not_expired(self):
        """Test cache entry is not expired immediately."""
        entry = CacheEntry("test", 300.0)
        assert not entry.is_expired()

    def test_cache_entry_expires(self):
        """Test cache entry expires after TTL."""
        entry = CacheEntry("test", 0.1)  # 100ms TTL
        time.sleep(0.2)  # Wait 200ms
        assert entry.is_expired()


class TestCacheManager:
    """Tests for CacheManager class."""

    def test_cache_manager_initialization(self):
        """Test cache manager initializes correctly."""
        cache = CacheManager(ttl=300.0)
        assert cache.ttl == 300.0
        stats = cache.get_stats()
        assert stats["users"] == 0
        assert stats["teams"] == 0
        assert stats["channels"] == 0
        assert stats["posts"] == 0

    def test_user_caching(self):
        """Test user caching and retrieval."""
        cache = CacheManager()
        user_data = {
            "id": "user123",
            "username": "john.doe",
            "email": "john@example.com",
        }

        # Cache user
        cache.set_user("user123", user_data)
        assert cache.get_stats()["users"] == 1

        # Retrieve user
        cached_user = cache.get_user("user123")
        assert cached_user == user_data

        # Non-existent user
        assert cache.get_user("nonexistent") is None

    def test_user_cache_expiration(self):
        """Test user cache expires after TTL."""
        cache = CacheManager(ttl=0.1)  # 100ms TTL
        user_data = {"id": "user123", "username": "john.doe"}

        cache.set_user("user123", user_data)
        assert cache.get_user("user123") == user_data

        time.sleep(0.2)  # Wait for expiration
        assert cache.get_user("user123") is None

    def test_team_caching(self):
        """Test team caching and retrieval."""
        cache = CacheManager()
        team_data = {
            "id": "team123",
            "name": "engineering",
            "display_name": "Engineering Team",
        }

        # Cache team
        cache.set_team("team123", team_data)
        assert cache.get_stats()["teams"] == 1

        # Retrieve by ID
        cached_team = cache.get_team("team123")
        assert cached_team == team_data

        # Retrieve by name
        cached_by_name = cache.get_team_by_name("engineering")
        assert cached_by_name == team_data

    def test_team_cache_by_name_only(self):
        """Test team cache can be retrieved by name."""
        cache = CacheManager()
        team_data = {
            "id": "team123",
            "name": "engineering",
            "display_name": "Engineering Team",
        }

        cache.set_team("team123", team_data)

        # Should be retrievable by name
        assert cache.get_team_by_name("engineering") is not None
        assert cache.get_team_by_name("nonexistent") is None

    def test_channel_caching(self):
        """Test channel caching and retrieval."""
        cache = CacheManager()
        channel_data = {
            "id": "channel123",
            "team_id": "team123",
            "name": "general",
            "display_name": "General",
        }

        # Cache channel
        cache.set_channel("channel123", channel_data)
        assert cache.get_stats()["channels"] == 1

        # Retrieve by ID
        cached_channel = cache.get_channel("channel123")
        assert cached_channel == channel_data

        # Retrieve by name
        cached_by_name = cache.get_channel_by_name("team123", "general")
        assert cached_by_name == channel_data

    def test_channel_cache_requires_team_and_name(self):
        """Test channel cache by name requires both team_id and channel name."""
        cache = CacheManager()
        channel_data = {
            "id": "channel123",
            "team_id": "team123",
            "name": "general",
            "display_name": "General",
        }

        cache.set_channel("channel123", channel_data)

        # Correct team and channel
        assert cache.get_channel_by_name("team123", "general") is not None

        # Wrong team
        assert cache.get_channel_by_name("team999", "general") is None

        # Wrong channel
        assert cache.get_channel_by_name("team123", "random") is None

    def test_post_caching(self):
        """Test post caching and retrieval."""
        cache = CacheManager()
        post_data = {
            "id": "post123",
            "user_id": "user123",
            "message": "Hello world",
            "create_at": 1234567890,
        }

        # Cache post
        cache.set_post("post123", post_data)
        assert cache.get_stats()["posts"] == 1

        # Retrieve post
        cached_post = cache.get_post("post123")
        assert cached_post == post_data

    def test_cache_clear(self):
        """Test clearing all caches."""
        cache = CacheManager()

        # Add data to all caches
        cache.set_user("user123", {"id": "user123"})
        cache.set_team("team123", {"id": "team123", "name": "team"})
        cache.set_channel("channel123", {"id": "channel123"})
        cache.set_post("post123", {"id": "post123"})

        stats = cache.get_stats()
        assert stats["users"] == 1
        assert stats["teams"] == 1
        assert stats["channels"] == 1
        assert stats["posts"] == 1

        # Clear all
        cache.clear()

        stats = cache.get_stats()
        assert stats["users"] == 0
        assert stats["teams"] == 0
        assert stats["channels"] == 0
        assert stats["posts"] == 0

    def test_cache_cleanup_expired_entries(self):
        """Test that expired entries are cleaned up."""
        cache = CacheManager(ttl=0.1)  # 100ms TTL

        # Add multiple users
        cache.set_user("user1", {"id": "user1"})
        cache.set_user("user2", {"id": "user2"})
        assert cache.get_stats()["users"] == 2

        time.sleep(0.2)  # Wait for expiration

        # Add new user (triggers cleanup)
        cache.set_user("user3", {"id": "user3"})

        # Try to get expired users (triggers cleanup)
        cache.get_user("user1")

        # Stats should show cleanup happened
        stats = cache.get_stats()
        # Only user3 should remain after cleanup
        assert stats["users"] == 1

    def test_multiple_teams_caching(self):
        """Test caching multiple teams."""
        cache = CacheManager()

        teams = [
            {"id": "team1", "name": "engineering", "display_name": "Engineering"},
            {"id": "team2", "name": "sales", "display_name": "Sales"},
            {"id": "team3", "name": "marketing", "display_name": "Marketing"},
        ]

        for team in teams:
            cache.set_team(team["id"], team)

        assert cache.get_stats()["teams"] == 3

        # All should be retrievable
        for team in teams:
            assert cache.get_team(team["id"]) == team
            assert cache.get_team_by_name(team["name"]) == team

    def test_multiple_channels_same_name_different_teams(self):
        """Test caching channels with same name in different teams."""
        cache = CacheManager()

        channel1 = {
            "id": "channel1",
            "team_id": "team1",
            "name": "general",
            "display_name": "General",
        }
        channel2 = {
            "id": "channel2",
            "team_id": "team2",
            "name": "general",
            "display_name": "General",
        }

        cache.set_channel("channel1", channel1)
        cache.set_channel("channel2", channel2)

        # Both should be retrievable by their team+name combination
        assert cache.get_channel_by_name("team1", "general") == channel1
        assert cache.get_channel_by_name("team2", "general") == channel2
        assert cache.get_channel_by_name("team1", "general") != channel2
