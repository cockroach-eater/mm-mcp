"""Mattermost API wrapper for the MCP server."""

from datetime import datetime
from functools import wraps
from typing import Any, Callable, TypeVar

from mattermostdriver import Driver
from mattermostdriver.exceptions import (
    InvalidOrMissingParameters,
    NoAccessTokenProvided,
    NotEnoughPermissions,
    ResourceNotFound,
)

from .cache import CacheManager
from .config import MattermostConfig

T = TypeVar("T")


class MattermostClient:
    """Wrapper around the Mattermost API driver."""

    def __init__(self, config: MattermostConfig, cache_ttl: float = 300.0) -> None:
        """Initialize the Mattermost client.

        Args:
            config: Mattermost configuration.
            cache_ttl: Cache time-to-live in seconds (default: 5 minutes).
        """
        self.config = config
        self.driver = Driver(config.get_parsed_config())
        self._authenticated = False
        self.cache = CacheManager(ttl=cache_ttl)

    async def connect(self) -> None:
        """Connect and authenticate with Mattermost.

        Raises:
            Exception: If authentication fails.
        """
        self._authenticate()

    def _authenticate(self) -> None:
        """Perform authentication with Mattermost.

        Raises:
            Exception: If authentication fails.
        """
        try:
            if self.config.has_token_auth:
                # Token authentication - test with a simple API call
                # This will raise an exception if token is invalid
                try:
                    self.driver.users.get_user(user_id="me")
                    self._authenticated = True
                except Exception as e:
                    raise Exception(f"Token authentication failed: {e}") from e
            elif self.config.has_password_auth:
                # Login with username/password
                self.driver.login()
                self._authenticated = True
            else:
                raise ValueError("No valid authentication method configured")
        except Exception as e:
            self._authenticated = False
            raise Exception(f"Failed to authenticate with Mattermost: {e}") from e

    def _is_auth_error(self, error: Exception) -> bool:
        """Check if an error is related to authentication/session expiry.

        Args:
            error: The exception to check.

        Returns:
            True if the error is authentication-related.
        """
        error_msg = str(error).lower()
        
        # Check for common session/auth error patterns
        auth_patterns = [
            "session is invalid",
            "invalid or expired session",
            "session expired",
            "expired session",
            "invalid session",
            "unauthorized",
            "401",
            "authentication required",
            "token expired",
            "please login again",
        ]
        
        return any(phrase in error_msg for phrase in auth_patterns)

    def _with_retry(self, func: Callable[..., T]) -> Callable[..., T]:
        """Decorator to retry API calls with re-authentication on session expiry.

        Args:
            func: The function to wrap.

        Returns:
            Wrapped function with retry logic.
        """

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_msg = str(e)
                # Check if it's an authentication error
                if self._is_auth_error(e) and self.config.has_password_auth:
                    # Re-authenticate and retry once
                    try:
                        # Log the retry attempt (visible in error messages if it fails)
                        self._authenticate()
                        # Retry the original function
                        return func(*args, **kwargs)
                    except Exception as retry_error:
                        # If retry also fails, provide helpful error message
                        raise Exception(
                            f"Session expired and re-authentication failed. "
                            f"Original error: {error_msg}. "
                            f"Retry error: {retry_error}"
                        ) from e
                # If not an auth error or already using token auth, raise original error
                raise

        return wrapper

    def get_teams(self) -> list[dict[str, Any]]:
        """Get all teams the user is a member of.

        Returns:
            List of team dictionaries.
        """
        teams = self._with_retry(lambda: self.driver.teams.get_user_teams(user_id="me"))()
        # Cache all teams
        for team in teams:
            if "id" in team:
                self.cache.set_team(team["id"], team)
        return teams

    def get_channels(self, team_id: str) -> list[dict[str, Any]]:
        """Get all channels in a team.

        Args:
            team_id: The team ID.

        Returns:
            List of channel dictionaries.
        """
        channels = self._with_retry(
            lambda: self.driver.channels.get_channels_for_user(user_id="me", team_id=team_id)
        )()
        # Cache all channels
        for channel in channels:
            if "id" in channel:
                self.cache.set_channel(channel["id"], channel)
        return channels

    def get_channel_by_name(self, team_id: str, channel_name: str) -> dict[str, Any]:
        """Get a channel by name.

        Args:
            team_id: The team ID.
            channel_name: The channel name.

        Returns:
            Channel dictionary.
        """
        # Check cache first
        cached = self.cache.get_channel_by_name(team_id, channel_name)
        if cached:
            return cached
        
        # Fetch from API
        channel = self._with_retry(
            lambda: self.driver.channels.get_channel_by_name(
                team_id=team_id, channel_name=channel_name
            )
        )()
        
        # Cache the result
        if "id" in channel:
            self.cache.set_channel(channel["id"], channel)
        
        return channel

    def _format_timestamp(self, timestamp_ms: int) -> str:
        """Format a Mattermost timestamp (milliseconds) to readable string.

        Args:
            timestamp_ms: Timestamp in milliseconds.

        Returns:
            Formatted timestamp string.
        """
        dt = datetime.fromtimestamp(timestamp_ms / 1000.0)
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    def _batch_get_users(self, user_ids: list[str]) -> dict[str, dict[str, Any]]:
        """Batch fetch user information with caching.

        Args:
            user_ids: List of user IDs to fetch.

        Returns:
            Dictionary mapping user_id to user data.
        """
        users = {}
        ids_to_fetch = []
        
        # Check cache first
        for user_id in user_ids:
            cached = self.cache.get_user(user_id)
            if cached:
                users[user_id] = cached
            else:
                ids_to_fetch.append(user_id)
        
        # Fetch missing users
        for user_id in ids_to_fetch:
            try:
                user = self.get_user(user_id)
                users[user_id] = user
            except Exception:
                # If user fetch fails, provide a fallback
                users[user_id] = {
                    "id": user_id,
                    "username": f"user_{user_id[:8]}",
                    "first_name": "",
                    "last_name": "",
                }
        
        return users

    def _batch_get_channels(self, channel_ids: list[str]) -> dict[str, dict[str, Any]]:
        """Batch fetch channel information with caching.

        Args:
            channel_ids: List of channel IDs to fetch.

        Returns:
            Dictionary mapping channel_id to channel data.
        """
        channels = {}
        ids_to_fetch = []
        
        # Check cache first
        for channel_id in channel_ids:
            cached = self.cache.get_channel(channel_id)
            if cached:
                channels[channel_id] = cached
            else:
                ids_to_fetch.append(channel_id)
        
        # Fetch missing channels
        for channel_id in ids_to_fetch:
            try:
                channel = self._with_retry(
                    lambda: self.driver.channels.get_channel(channel_id=channel_id)
                )()
                self.cache.set_channel(channel_id, channel)
                channels[channel_id] = channel
            except Exception:
                # If channel fetch fails, provide a fallback
                channels[channel_id] = {
                    "id": channel_id,
                    "name": f"channel_{channel_id[:8]}",
                    "display_name": "Unknown Channel",
                }
        
        return channels

    def get_posts(
        self, channel_id: str, page: int = 0, per_page: int = 60
    ) -> dict[str, Any]:
        """Get posts from a channel.

        Args:
            channel_id: The channel ID.
            page: Page number for pagination (default: 0).
            per_page: Number of posts per page (default: 60).

        Returns:
            Dictionary containing posts and order information.
        """
        posts_data = self._with_retry(
            lambda: self.driver.posts.get_posts_for_channel(
                channel_id=channel_id, params={"page": page, "per_page": per_page}
            )
        )()
        
        # Cache all posts
        posts = posts_data.get("posts", {})
        for post_id, post in posts.items():
            self.cache.set_post(post_id, post)
        
        return posts_data

    def get_posts_enriched(
        self, channel_id: str, page: int = 0, per_page: int = 60
    ) -> list[dict[str, Any]]:
        """Get posts from a channel with enriched user information.

        Args:
            channel_id: The channel ID.
            page: Page number for pagination (default: 0).
            per_page: Number of posts per page (default: 60).

        Returns:
            List of enriched post dictionaries with user information.
        """
        posts_data = self.get_posts(channel_id, page, per_page)
        posts = posts_data.get("posts", {})
        order = posts_data.get("order", [])
        
        # Collect unique user IDs
        user_ids = list(set(post.get("user_id") for post in posts.values() if post.get("user_id")))
        
        # Batch fetch users
        users = self._batch_get_users(user_ids)
        
        # Enrich posts
        enriched_posts = []
        for post_id in order[:per_page]:
            post = posts.get(post_id, {})
            user_id = post.get("user_id")
            user = users.get(user_id, {})
            
            enriched_post = {
                "id": post.get("id"),
                "user_id": user_id,
                "username": user.get("username", "unknown"),
                "user_display_name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() 
                                     or user.get("username", "Unknown User"),
                "message": post.get("message"),
                "create_at": post.get("create_at"),
                "create_at_formatted": self._format_timestamp(post.get("create_at", 0)),
                "channel_id": post.get("channel_id"),
                "root_id": post.get("root_id"),
            }
            enriched_posts.append(enriched_post)
        
        return enriched_posts

    def create_post(
        self, channel_id: str, message: str, root_id: str | None = None
    ) -> dict[str, Any]:
        """Create a new post in a channel.

        Args:
            channel_id: The channel ID.
            message: The message text.
            root_id: Optional root post ID for replies.

        Returns:
            Created post dictionary.
        """
        post_data = {"channel_id": channel_id, "message": message}
        if root_id:
            post_data["root_id"] = root_id
        return self._with_retry(lambda: self.driver.posts.create_post(options=post_data))()

    def search_posts(self, team_id: str, terms: str) -> dict[str, Any]:
        """Search for posts in a team.

        Args:
            team_id: The team ID.
            terms: Search terms (supports from:user and in:channel syntax).

        Returns:
            Dictionary containing search results.
        """
        results = self._with_retry(
            lambda: self.driver.posts.search_for_team_posts(
                team_id=team_id,
                options={
                    "terms": terms,
                    "is_or_search": False,
                },
            )
        )()

        # Cache all posts from search results (posts is a dict with post_id as keys)
        posts = results.get("posts", {})
        if isinstance(posts, dict):
            for post_id, post in posts.items():
                self.cache.set_post(post_id, post)
        
        return results

    def search_posts_enriched(self, team_id: str, terms: str) -> list[dict[str, Any]]:
        """Search for posts with enriched user and channel information.

        Args:
            team_id: The team ID.
            terms: Search terms (supports from:user and in:channel syntax).

        Returns:
            List of enriched post dictionaries with user and channel information.
        """
        results = self.search_posts(team_id, terms)
        posts_data = results.get("posts", {})
        # Handle both dict (from search) and list formats
        posts = list(posts_data.values()) if isinstance(posts_data, dict) else posts_data
        
        # Collect unique user and channel IDs
        user_ids = list(set(post.get("user_id") for post in posts if post.get("user_id")))
        channel_ids = list(set(post.get("channel_id") for post in posts if post.get("channel_id")))
        
        # Batch fetch users and channels
        users = self._batch_get_users(user_ids)
        channels = self._batch_get_channels(channel_ids)
        
        # Enrich posts
        enriched_posts = []
        for post in posts:
            user_id = post.get("user_id")
            channel_id = post.get("channel_id")
            user = users.get(user_id, {})
            channel = channels.get(channel_id, {})
            
            enriched_post = {
                "id": post.get("id"),
                "user_id": user_id,
                "username": user.get("username", "unknown"),
                "user_display_name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() 
                                     or user.get("username", "Unknown User"),
                "channel_id": channel_id,
                "channel_name": channel.get("name", "unknown"),
                "channel_display_name": channel.get("display_name", "Unknown Channel"),
                "message": post.get("message"),
                "create_at": post.get("create_at"),
                "create_at_formatted": self._format_timestamp(post.get("create_at", 0)),
            }
            enriched_posts.append(enriched_post)
        
        return enriched_posts

    def get_team_by_name(self, team_name: str) -> dict[str, Any]:
        """Get a team by its name.

        Args:
            team_name: The team name.

        Returns:
            Team dictionary.

        Raises:
            ValueError: If team is not found.
        """
        # Check cache first
        cached = self.cache.get_team_by_name(team_name)
        if cached:
            return cached
        
        # Fetch all teams and find by name
        teams = self.get_teams()
        for team in teams:
            if team.get("name") == team_name:
                return team
        
        raise ValueError(f"Team '{team_name}' not found")

    def get_posts_by_channel_name(
        self, team_name: str, channel_name: str, page: int = 0, per_page: int = 20
    ) -> list[dict[str, Any]]:
        """Get enriched posts from a channel by team and channel name.

        Args:
            team_name: The team name.
            channel_name: The channel name.
            page: Page number for pagination (default: 0).
            per_page: Number of posts per page (default: 20).

        Returns:
            List of enriched post dictionaries.
        """
        # Resolve team name to ID
        team = self.get_team_by_name(team_name)
        team_id = team["id"]
        
        # Resolve channel name to ID
        channel = self.get_channel_by_name(team_id, channel_name)
        channel_id = channel["id"]
        
        # Get enriched posts
        return self.get_posts_enriched(channel_id, page=page, per_page=per_page)

    def send_message_by_channel_name(
        self, team_name: str, channel_name: str, message: str, reply_to: str | None = None
    ) -> dict[str, Any]:
        """Send a message to a channel by team and channel name.

        Args:
            team_name: The team name.
            channel_name: The channel name.
            message: The message text.
            reply_to: Optional root post ID for replies.

        Returns:
            Created post dictionary.
        """
        # Resolve team name to ID
        team = self.get_team_by_name(team_name)
        team_id = team["id"]
        
        # Resolve channel name to ID
        channel = self.get_channel_by_name(team_id, channel_name)
        channel_id = channel["id"]
        
        # Send message
        return self.create_post(channel_id, message, reply_to)

    def search_messages_by_team_name(
        self, team_name: str, query: str
    ) -> list[dict[str, Any]]:
        """Search for messages by team name with enriched information.

        Args:
            team_name: The team name.
            query: Search query string.

        Returns:
            List of enriched search result dictionaries.
        """
        # Resolve team name to ID
        team = self.get_team_by_name(team_name)
        team_id = team["id"]
        
        # Search with enrichment
        return self.search_posts_enriched(team_id, query)

    def get_user(self, user_id: str = "me") -> dict[str, Any]:
        """Get user information.

        Args:
            user_id: The user ID (default: "me" for current user).

        Returns:
            User dictionary.
        """
        # Don't cache "me" - always fetch current user fresh
        if user_id == "me":
            return self._with_retry(lambda: self.driver.users.get_user(user_id=user_id))()
        
        # Check cache first
        cached = self.cache.get_user(user_id)
        if cached:
            return cached
        
        # Fetch from API
        user = self._with_retry(lambda: self.driver.users.get_user(user_id=user_id))()
        
        # Cache the result
        if "id" in user:
            self.cache.set_user(user["id"], user)
        
        return user

    def get_channel_members(self, channel_id: str) -> list[dict[str, Any]]:
        """Get all members of a channel.

        Args:
            channel_id: The channel ID.

        Returns:
            List of channel member dictionaries.
        """
        return self._with_retry(
            lambda: self.driver.channels.get_channel_members(channel_id=channel_id)
        )()

    def disconnect(self) -> None:
        """Disconnect from Mattermost."""
        if self._authenticated and self.config.has_password_auth:
            try:
                self.driver.logout()
            except Exception:
                pass  # Ignore logout errors
        self._authenticated = False
