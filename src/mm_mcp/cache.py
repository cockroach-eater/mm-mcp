"""In-memory caching with TTL for Mattermost data."""

import time
from typing import Any, TypeVar

T = TypeVar("T")


class CacheEntry:
    """A cache entry with timestamp for TTL management."""

    def __init__(self, value: Any, ttl: float) -> None:
        """Initialize a cache entry.

        Args:
            value: The value to cache.
            ttl: Time-to-live in seconds.
        """
        self.value = value
        self.expires_at = time.time() + ttl

    def is_expired(self) -> bool:
        """Check if the cache entry has expired.

        Returns:
            True if expired, False otherwise.
        """
        return time.time() > self.expires_at


class CacheManager:
    """Manages in-memory caching with TTL for Mattermost data."""

    def __init__(self, ttl: float = 300.0) -> None:
        """Initialize the cache manager.

        Args:
            ttl: Default time-to-live for cache entries in seconds (default: 5 minutes).
        """
        self.ttl = ttl
        self._users: dict[str, CacheEntry] = {}
        self._teams: dict[str, CacheEntry] = {}
        self._team_names: dict[str, CacheEntry] = {}  # name -> team data
        self._channels: dict[str, CacheEntry] = {}
        self._channel_names: dict[tuple[str, str], CacheEntry] = {}  # (team_id, name) -> channel data
        self._posts: dict[str, CacheEntry] = {}

    def _cleanup_expired(self, cache: dict[Any, CacheEntry]) -> None:
        """Remove expired entries from a cache dictionary.

        Args:
            cache: The cache dictionary to clean.
        """
        expired_keys = [key for key, entry in cache.items() if entry.is_expired()]
        for key in expired_keys:
            del cache[key]

    def get_user(self, user_id: str) -> dict[str, Any] | None:
        """Get a user from cache if available and not expired.

        Args:
            user_id: The user ID.

        Returns:
            User data or None if not cached or expired.
        """
        self._cleanup_expired(self._users)
        entry = self._users.get(user_id)
        return entry.value if entry and not entry.is_expired() else None

    def set_user(self, user_id: str, user_data: dict[str, Any]) -> None:
        """Cache user data.

        Args:
            user_id: The user ID.
            user_data: The user data to cache.
        """
        self._users[user_id] = CacheEntry(user_data, self.ttl)

    def get_team(self, team_id: str) -> dict[str, Any] | None:
        """Get a team from cache if available and not expired.

        Args:
            team_id: The team ID.

        Returns:
            Team data or None if not cached or expired.
        """
        self._cleanup_expired(self._teams)
        entry = self._teams.get(team_id)
        return entry.value if entry and not entry.is_expired() else None

    def set_team(self, team_id: str, team_data: dict[str, Any]) -> None:
        """Cache team data.

        Args:
            team_id: The team ID.
            team_data: The team data to cache.
        """
        self._teams[team_id] = CacheEntry(team_data, self.ttl)
        # Also cache by name for name-based lookups
        if "name" in team_data:
            self._team_names[team_data["name"]] = CacheEntry(team_data, self.ttl)

    def get_team_by_name(self, team_name: str) -> dict[str, Any] | None:
        """Get a team by name from cache.

        Args:
            team_name: The team name.

        Returns:
            Team data or None if not cached or expired.
        """
        self._cleanup_expired(self._team_names)
        entry = self._team_names.get(team_name)
        return entry.value if entry and not entry.is_expired() else None

    def get_channel(self, channel_id: str) -> dict[str, Any] | None:
        """Get a channel from cache if available and not expired.

        Args:
            channel_id: The channel ID.

        Returns:
            Channel data or None if not cached or expired.
        """
        self._cleanup_expired(self._channels)
        entry = self._channels.get(channel_id)
        return entry.value if entry and not entry.is_expired() else None

    def set_channel(self, channel_id: str, channel_data: dict[str, Any]) -> None:
        """Cache channel data.

        Args:
            channel_id: The channel ID.
            channel_data: The channel data to cache.
        """
        self._channels[channel_id] = CacheEntry(channel_data, self.ttl)
        # Also cache by (team_id, name) for name-based lookups
        if "team_id" in channel_data and "name" in channel_data:
            key = (channel_data["team_id"], channel_data["name"])
            self._channel_names[key] = CacheEntry(channel_data, self.ttl)

    def get_channel_by_name(
        self, team_id: str, channel_name: str
    ) -> dict[str, Any] | None:
        """Get a channel by team ID and name from cache.

        Args:
            team_id: The team ID.
            channel_name: The channel name.

        Returns:
            Channel data or None if not cached or expired.
        """
        self._cleanup_expired(self._channel_names)
        key = (team_id, channel_name)
        entry = self._channel_names.get(key)
        return entry.value if entry and not entry.is_expired() else None

    def get_post(self, post_id: str) -> dict[str, Any] | None:
        """Get a post from cache if available and not expired.

        Args:
            post_id: The post ID.

        Returns:
            Post data or None if not cached or expired.
        """
        self._cleanup_expired(self._posts)
        entry = self._posts.get(post_id)
        return entry.value if entry and not entry.is_expired() else None

    def set_post(self, post_id: str, post_data: dict[str, Any]) -> None:
        """Cache post data.

        Args:
            post_id: The post ID.
            post_data: The post data to cache.
        """
        self._posts[post_id] = CacheEntry(post_data, self.ttl)

    def clear(self) -> None:
        """Clear all caches."""
        self._users.clear()
        self._teams.clear()
        self._team_names.clear()
        self._channels.clear()
        self._channel_names.clear()
        self._posts.clear()

    def get_stats(self) -> dict[str, int]:
        """Get cache statistics.

        Returns:
            Dictionary with cache size statistics.
        """
        return {
            "users": len(self._users),
            "teams": len(self._teams),
            "channels": len(self._channels),
            "posts": len(self._posts),
        }
