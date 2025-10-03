"""Configuration management for the Mattermost MCP server."""

from typing import Optional

from pydantic import BaseModel, Field


class MattermostConfig(BaseModel):
    """Configuration for Mattermost connection."""

    url: str = Field(
        description="Mattermost server URL",
    )
    token: Optional[str] = Field(
        default=None,
        description="Personal access token for authentication",
    )
    login: Optional[str] = Field(
        default=None,
        description="Login email for password authentication",
    )
    password: Optional[str] = Field(
        default=None,
        description="Password for password authentication",
    )
    scheme: str = Field(
        default="https",
        description="URL scheme (http or https)",
    )
    port: int = Field(
        default=443,
        description="Mattermost server port",
    )
    verify: bool = Field(
        default=True,
        description="Verify SSL certificates",
    )

    def validate_auth(self) -> None:
        """Validate that at least one authentication method is configured.

        Raises:
            ValueError: If neither token nor login/password is provided.
        """
        if not self.token and not (self.login and self.password):
            raise ValueError(
                "Either MATTERMOST_TOKEN or both MATTERMOST_LOGIN and "
                "MATTERMOST_PASSWORD must be provided"
            )

    @property
    def has_token_auth(self) -> bool:
        """Check if token authentication is configured."""
        return bool(self.token)

    @property
    def has_password_auth(self) -> bool:
        """Check if password authentication is configured."""
        return bool(self.login and self.password)
