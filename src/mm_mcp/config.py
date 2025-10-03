"""Configuration management for the Mattermost MCP server."""

from typing import Optional
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator


class MattermostConfig(BaseModel):
    """Configuration for Mattermost connection."""

    url: str = Field(
        description="Mattermost server URL (can include scheme and port)",
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

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format.
        
        The URL can be provided in various formats:
        - https://mm.example.com
        - http://mm.example.com:8065
        - mm.example.com
        
        This validator just checks the URL is valid and returns it unchanged.
        """
        if not v:
            raise ValueError("URL cannot be empty")
        
        # Store original for parsing later
        return v
    
    def get_parsed_config(self) -> dict[str, str | int | bool | None]:
        """Get configuration with URL properly parsed.
        
        Returns:
            Dictionary with parsed URL components for mattermostdriver.
        """
        # Parse the original URL to extract scheme and port if provided
        url_to_parse = self.url
        if not url_to_parse.startswith(("http://", "https://")):
            url_to_parse = f"{self.scheme}://{url_to_parse}"
        
        parsed = urlparse(url_to_parse)
        
        # Extract scheme if provided in URL
        scheme = parsed.scheme if parsed.scheme else self.scheme
        
        # Extract port if provided in URL
        if parsed.port:
            port = parsed.port
        else:
            # Use provided port, or default based on scheme
            if self.port != 443:  # User specified a custom port
                port = self.port
            else:
                port = 443 if scheme == "https" else 80
        
        # Extract hostname from parsed URL
        hostname = parsed.hostname or parsed.netloc.split(":")[0]
        
        return {
            "url": hostname,
            "token": self.token,
            "login_id": self.login,
            "password": self.password,
            "scheme": scheme,
            "port": port,
            "verify": self.verify,
        }

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
