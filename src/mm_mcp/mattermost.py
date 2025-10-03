"""Mattermost API wrapper for the MCP server."""

from typing import Any

from mattermostdriver import Driver

from .config import MattermostConfig


class MattermostClient:
    """Wrapper around the Mattermost API driver."""

    def __init__(self, config: MattermostConfig) -> None:
        """Initialize the Mattermost client.

        Args:
            config: Mattermost configuration.
        """
        self.config = config
        self.driver = Driver(config.get_parsed_config())
        self._authenticated = False

    async def connect(self) -> None:
        """Connect and authenticate with Mattermost.

        Raises:
            Exception: If authentication fails.
        """
        try:
            if self.config.has_token_auth:
                # Token authentication - driver handles this automatically
                self._authenticated = True
            elif self.config.has_password_auth:
                # Login with username/password
                self.driver.login()
                self._authenticated = True
            else:
                raise ValueError("No valid authentication method configured")
        except Exception as e:
            raise Exception(f"Failed to authenticate with Mattermost: {e}") from e

    def get_teams(self) -> list[dict[str, Any]]:
        """Get all teams the user is a member of.

        Returns:
            List of team dictionaries.
        """
        return self.driver.teams.get_user_teams(user_id="me")

    def get_channels(self, team_id: str) -> list[dict[str, Any]]:
        """Get all channels in a team.

        Args:
            team_id: The team ID.

        Returns:
            List of channel dictionaries.
        """
        return self.driver.channels.get_channels_for_user(user_id="me", team_id=team_id)

    def get_channel_by_name(self, team_id: str, channel_name: str) -> dict[str, Any]:
        """Get a channel by name.

        Args:
            team_id: The team ID.
            channel_name: The channel name.

        Returns:
            Channel dictionary.
        """
        return self.driver.channels.get_channel_by_name(team_id=team_id, channel_name=channel_name)

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
        return self.driver.posts.get_posts_for_channel(
            channel_id=channel_id, params={"page": page, "per_page": per_page}
        )

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
        return self.driver.posts.create_post(options=post_data)

    def search_posts(self, team_id: str, terms: str) -> dict[str, Any]:
        """Search for posts in a team.

        Args:
            team_id: The team ID.
            terms: Search terms.

        Returns:
            Dictionary containing search results.
        """
        return self.driver.posts.search_posts(team_id=team_id, terms=terms)

    def get_user(self, user_id: str = "me") -> dict[str, Any]:
        """Get user information.

        Args:
            user_id: The user ID (default: "me" for current user).

        Returns:
            User dictionary.
        """
        return self.driver.users.get_user(user_id=user_id)

    def get_channel_members(self, channel_id: str) -> list[dict[str, Any]]:
        """Get all members of a channel.

        Args:
            channel_id: The channel ID.

        Returns:
            List of channel member dictionaries.
        """
        return self.driver.channels.get_channel_members(channel_id=channel_id)

    def disconnect(self) -> None:
        """Disconnect from Mattermost."""
        if self._authenticated and self.config.has_password_auth:
            try:
                self.driver.logout()
            except Exception:
                pass  # Ignore logout errors
        self._authenticated = False
