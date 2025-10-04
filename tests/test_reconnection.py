"""Tests for connection and reconnection behavior."""

import pytest
from unittest.mock import AsyncMock, Mock, patch

from mm_mcp.config import MattermostConfig
from mm_mcp.mattermost import MattermostClient
import mm_mcp.server as server_module


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    config = Mock(spec=MattermostConfig)
    config.get_parsed_config.return_value = {
        "url": "https://mattermost.example.com",
        "token": "test_token",
    }
    config.has_token_auth = True
    config.has_password_auth = False
    return config


class TestClientInitialization:
    """Tests for client initialization and connection."""

    @pytest.mark.asyncio
    async def test_get_client_creates_client_on_first_call(self, mock_config):
        """Test that get_client creates a client on first call."""
        # Reset global state
        server_module._client = None
        server_module._config = mock_config

        with patch("mm_mcp.server.MattermostClient") as mock_client_class:
            mock_instance = Mock(spec=MattermostClient)
            mock_instance.connect = AsyncMock()
            mock_client_class.return_value = mock_instance

            # First call should create client
            client = await server_module.get_client()

            assert client is not None
            mock_client_class.assert_called_once_with(mock_config)
            mock_instance.connect.assert_called_once()

        # Cleanup
        server_module._client = None

    @pytest.mark.asyncio
    async def test_get_client_reuses_existing_client(self, mock_config):
        """Test that get_client reuses existing client."""
        # Reset global state
        server_module._client = None
        server_module._config = mock_config

        with patch("mm_mcp.server.MattermostClient") as mock_client_class:
            mock_instance = Mock(spec=MattermostClient)
            mock_instance.connect = AsyncMock()
            mock_client_class.return_value = mock_instance

            # First call
            client1 = await server_module.get_client()
            # Second call
            client2 = await server_module.get_client()

            # Should be the same instance
            assert client1 is client2
            # Client should only be created once
            mock_client_class.assert_called_once()

        # Cleanup
        server_module._client = None

    @pytest.mark.asyncio
    async def test_get_client_raises_if_no_config(self):
        """Test that get_client raises error if config not initialized."""
        # Reset global state
        server_module._client = None
        server_module._config = None

        with pytest.raises(RuntimeError, match="Configuration not initialized"):
            await server_module.get_client()

        # Cleanup
        server_module._client = None

    @pytest.mark.asyncio
    async def test_get_client_resets_on_connection_failure(self, mock_config):
        """Test that client is reset if connection fails."""
        # Reset global state
        server_module._client = None
        server_module._config = mock_config

        with patch("mm_mcp.server.MattermostClient") as mock_client_class:
            mock_instance = Mock(spec=MattermostClient)
            # First call fails
            mock_instance.connect = AsyncMock(side_effect=Exception("Connection failed"))
            mock_client_class.return_value = mock_instance

            # First call should fail
            with pytest.raises(RuntimeError, match="Failed to connect"):
                await server_module.get_client()

            # Client should be reset to None
            assert server_module._client is None

            # Second call with working connection
            mock_instance.connect = AsyncMock()  # Works now
            client = await server_module.get_client()

            # Should successfully create client on retry
            assert client is not None
            assert mock_client_class.call_count == 2

        # Cleanup
        server_module._client = None


class TestClientCleanup:
    """Tests for client cleanup."""

    @pytest.mark.asyncio
    async def test_cleanup_client_disconnects_and_resets(self):
        """Test that cleanup properly disconnects and resets client."""
        mock_client = Mock(spec=MattermostClient)
        mock_client.disconnect = Mock()

        server_module._client = mock_client

        await server_module.cleanup_client()

        # Should call disconnect
        mock_client.disconnect.assert_called_once()
        # Should reset to None
        assert server_module._client is None

    @pytest.mark.asyncio
    async def test_cleanup_client_handles_disconnect_errors(self):
        """Test that cleanup handles disconnect errors gracefully."""
        mock_client = Mock(spec=MattermostClient)
        mock_client.disconnect = Mock(side_effect=Exception("Disconnect failed"))

        server_module._client = mock_client

        # Should not raise
        await server_module.cleanup_client()

        # Should still reset to None even if disconnect fails
        assert server_module._client is None

    @pytest.mark.asyncio
    async def test_cleanup_client_when_no_client(self):
        """Test that cleanup works when no client exists."""
        server_module._client = None

        # Should not raise
        await server_module.cleanup_client()

        assert server_module._client is None


class TestReconnectionBehavior:
    """Tests for reconnection on errors."""

    @pytest.mark.asyncio
    async def test_authentication_error_resets_client(self, mock_config):
        """Test that authentication errors reset the client for retry."""
        server_module._client = None
        server_module._config = mock_config

        with patch("mm_mcp.server.MattermostClient") as mock_client_class:
            mock_instance = Mock(spec=MattermostClient)
            mock_instance.connect = AsyncMock()
            mock_client_class.return_value = mock_instance

            # Create client
            await server_module.get_client()
            assert server_module._client is not None

            # Simulate authentication error in tool call
            mock_instance.get_teams = Mock(
                side_effect=Exception("Session is invalid or expired")
            )

            # Call tool (should catch error and reset client)
            result = await server_module.call_tool("get_teams", {})

            # Should return error message
            assert "Authentication error" in result[0].text
            # Client should be reset
            assert server_module._client is None

        # Cleanup
        server_module._client = None

    @pytest.mark.asyncio
    async def test_unauthorized_error_resets_client(self, mock_config):
        """Test that 401 errors reset the client."""
        server_module._client = None
        server_module._config = mock_config

        with patch("mm_mcp.server.MattermostClient") as mock_client_class:
            mock_instance = Mock(spec=MattermostClient)
            mock_instance.connect = AsyncMock()
            mock_client_class.return_value = mock_instance

            # Create client
            await server_module.get_client()

            # Simulate 401 error
            mock_instance.get_teams = Mock(side_effect=Exception("401 Unauthorized"))

            # Call tool
            result = await server_module.call_tool("get_teams", {})

            # Should return error and reset client
            assert "Authentication error" in result[0].text
            assert server_module._client is None

        # Cleanup
        server_module._client = None

    @pytest.mark.asyncio
    async def test_non_auth_error_keeps_client(self, mock_config):
        """Test that non-authentication errors don't reset client."""
        server_module._client = None
        server_module._config = mock_config

        with patch("mm_mcp.server.MattermostClient") as mock_client_class:
            mock_instance = Mock(spec=MattermostClient)
            mock_instance.connect = AsyncMock()
            mock_client_class.return_value = mock_instance

            # Create client
            client = await server_module.get_client()

            # Simulate non-auth error
            mock_instance.get_teams = Mock(side_effect=Exception("Network timeout"))

            # Call tool
            result = await server_module.call_tool("get_teams", {})

            # Should return error but NOT reset client
            assert "Error:" in result[0].text
            assert "Authentication error" not in result[0].text
            # Client should still exist
            assert server_module._client is client

        # Cleanup
        server_module._client = None

    @pytest.mark.asyncio
    async def test_reconnection_after_auth_error(self, mock_config):
        """Test that client can reconnect after auth error."""
        server_module._client = None
        server_module._config = mock_config

        with patch("mm_mcp.server.MattermostClient") as mock_client_class:
            # First client instance (will fail)
            mock_instance1 = Mock(spec=MattermostClient)
            mock_instance1.connect = AsyncMock()
            mock_instance1.get_teams = Mock(
                side_effect=Exception("Session expired")
            )

            # Second client instance (will succeed)
            mock_instance2 = Mock(spec=MattermostClient)
            mock_instance2.connect = AsyncMock()
            mock_instance2.get_teams = Mock(return_value=[
                {"id": "team1", "name": "engineering", "display_name": "Engineering"}
            ])

            mock_client_class.side_effect = [mock_instance1, mock_instance2]

            # First call - should fail and reset client
            result1 = await server_module.call_tool("get_teams", {})
            assert "Authentication error" in result1[0].text
            assert server_module._client is None

            # Second call - should reconnect and succeed
            result2 = await server_module.call_tool("get_teams", {})
            assert "Authentication error" not in result2[0].text
            assert server_module._client is not None
            # Should have created 2 clients
            assert mock_client_class.call_count == 2

        # Cleanup
        server_module._client = None


class TestConnectionErrorHandling:
    """Tests for handling connection errors."""

    @pytest.mark.asyncio
    async def test_connection_error_returns_friendly_message(self, mock_config):
        """Test that connection errors return user-friendly messages."""
        server_module._client = None
        server_module._config = mock_config

        with patch("mm_mcp.server.MattermostClient") as mock_client_class:
            mock_instance = Mock(spec=MattermostClient)
            mock_instance.connect = AsyncMock(
                side_effect=Exception("Cannot connect to server")
            )
            mock_client_class.return_value = mock_instance

            # Call should return friendly error
            result = await server_module.call_tool("get_teams", {})

            assert "Connection error" in result[0].text
            assert "Cannot connect to server" in result[0].text

        # Cleanup
        server_module._client = None

    @pytest.mark.asyncio
    async def test_multiple_connection_attempts(self, mock_config):
        """Test multiple connection attempts work correctly."""
        server_module._client = None
        server_module._config = mock_config

        with patch("mm_mcp.server.MattermostClient") as mock_client_class:
            # All attempts fail
            mock_instance = Mock(spec=MattermostClient)
            mock_instance.connect = AsyncMock(side_effect=Exception("Connection failed"))
            mock_client_class.return_value = mock_instance

            # First attempt
            result1 = await server_module.call_tool("get_teams", {})
            assert "Connection error" in result1[0].text

            # Second attempt (should also fail)
            result2 = await server_module.call_tool("get_teams", {})
            assert "Connection error" in result2[0].text

            # Should have tried to connect twice
            assert mock_client_class.call_count == 2

        # Cleanup
        server_module._client = None
