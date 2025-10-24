"""Tests for Mattermost client enrichment functionality."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from mm_mcp.cache import CacheManager
from mm_mcp.config import MattermostConfig
from mm_mcp.mattermost import MattermostClient


@pytest.fixture
def mock_config():
    """Create a mock Mattermost configuration."""
    config = Mock(spec=MattermostConfig)
    config.get_parsed_config.return_value = {
        "url": "https://mattermost.example.com",
        "token": "test_token",
    }
    config.has_token_auth = True
    config.has_password_auth = False
    return config


@pytest.fixture
def mock_client(mock_config):
    """Create a Mattermost client with mocked driver."""
    with patch("mm_mcp.mattermost.Driver") as mock_driver_class:
        client = MattermostClient(mock_config, cache_ttl=300.0)
        client.driver = mock_driver_class.return_value
        client._authenticated = True
        return client


class TestFormatTimestamp:
    """Tests for timestamp formatting."""

    def test_format_timestamp(self, mock_client):
        """Test formatting Mattermost timestamp."""
        # Mattermost timestamp: 1728057600000 = 2024-10-04 10:00:00 UTC
        timestamp_ms = 1728057600000
        formatted = mock_client._format_timestamp(timestamp_ms)

        assert isinstance(formatted, str)
        assert "2024" in formatted
        assert "10" in formatted
        assert "04" in formatted

    def test_format_timestamp_zero(self, mock_client):
        """Test formatting zero timestamp."""
        formatted = mock_client._format_timestamp(0)
        assert isinstance(formatted, str)
        assert "1970" in formatted  # Unix epoch


class TestBatchGetUsers:
    """Tests for batch user fetching."""

    def test_batch_get_users_all_cached(self, mock_client):
        """Test batch getting users when all are cached."""
        # Pre-populate cache
        users = {
            "user1": {"id": "user1", "username": "alice"},
            "user2": {"id": "user2", "username": "bob"},
        }
        for user_id, user_data in users.items():
            mock_client.cache.set_user(user_id, user_data)

        # Fetch users
        result = mock_client._batch_get_users(["user1", "user2"])

        assert result == users
        # Driver should not be called since all cached
        mock_client.driver.users.get_user.assert_not_called()

    def test_batch_get_users_none_cached(self, mock_client):
        """Test batch getting users when none are cached."""
        # Mock API responses
        def mock_get_user(user_id):
            return {"id": user_id, "username": f"user_{user_id}"}

        mock_client.driver.users.get_user.side_effect = mock_get_user

        # Fetch users
        result = mock_client._batch_get_users(["user1", "user2"])

        assert len(result) == 2
        assert result["user1"]["username"] == "user_user1"
        assert result["user2"]["username"] == "user_user2"

        # Users should now be cached
        assert mock_client.cache.get_user("user1") is not None
        assert mock_client.cache.get_user("user2") is not None

    def test_batch_get_users_partial_cached(self, mock_client):
        """Test batch getting users with some cached, some not."""
        # Pre-cache one user
        mock_client.cache.set_user("user1", {"id": "user1", "username": "alice"})

        # Mock API response for uncached user
        mock_client.driver.users.get_user.return_value = {
            "id": "user2",
            "username": "bob",
        }

        # Fetch users
        result = mock_client._batch_get_users(["user1", "user2"])

        assert len(result) == 2
        assert result["user1"]["username"] == "alice"
        assert result["user2"]["username"] == "bob"

        # Only uncached user should trigger API call
        mock_client.driver.users.get_user.assert_called_once_with(user_id="user2")

    def test_batch_get_users_handles_fetch_failure(self, mock_client):
        """Test batch getting users handles fetch failures gracefully."""
        # Mock API to raise exception
        mock_client.driver.users.get_user.side_effect = Exception("API error")

        # Fetch users
        result = mock_client._batch_get_users(["user1"])

        assert len(result) == 1
        # Should provide fallback data
        assert "user1" in result
        assert "username" in result["user1"]
        assert "user_" in result["user1"]["username"]


class TestBatchGetChannels:
    """Tests for batch channel fetching."""

    def test_batch_get_channels_all_cached(self, mock_client):
        """Test batch getting channels when all are cached."""
        # Pre-populate cache
        channels = {
            "channel1": {"id": "channel1", "name": "general"},
            "channel2": {"id": "channel2", "name": "random"},
        }
        for channel_id, channel_data in channels.items():
            mock_client.cache.set_channel(channel_id, channel_data)

        # Fetch channels
        result = mock_client._batch_get_channels(["channel1", "channel2"])

        assert result == channels
        # Driver should not be called since all cached
        mock_client.driver.channels.get_channel.assert_not_called()

    def test_batch_get_channels_none_cached(self, mock_client):
        """Test batch getting channels when none are cached."""
        # Mock API responses
        def mock_get_channel(channel_id):
            return {"id": channel_id, "name": f"channel_{channel_id}"}

        mock_client.driver.channels.get_channel.side_effect = mock_get_channel

        # Fetch channels
        result = mock_client._batch_get_channels(["channel1", "channel2"])

        assert len(result) == 2
        assert result["channel1"]["name"] == "channel_channel1"
        assert result["channel2"]["name"] == "channel_channel2"

        # Channels should now be cached
        assert mock_client.cache.get_channel("channel1") is not None
        assert mock_client.cache.get_channel("channel2") is not None


class TestGetPostsEnriched:
    """Tests for enriched get_posts functionality."""

    def test_get_posts_enriched_with_users(self, mock_client):
        """Test getting enriched posts includes user information."""
        # Mock get_posts response
        posts_data = {
            "posts": {
                "post1": {
                    "id": "post1",
                    "user_id": "user1",
                    "message": "Hello",
                    "create_at": 1728057600000,
                    "channel_id": "channel1",
                },
                "post2": {
                    "id": "post2",
                    "user_id": "user2",
                    "message": "World",
                    "create_at": 1728057660000,
                    "channel_id": "channel1",
                },
            },
            "order": ["post1", "post2"],
        }

        mock_client.driver.posts.get_posts_for_channel.return_value = posts_data

        # Mock user responses
        def mock_get_user(user_id):
            users = {
                "user1": {
                    "id": "user1",
                    "username": "alice",
                    "first_name": "Alice",
                    "last_name": "Smith",
                },
                "user2": {
                    "id": "user2",
                    "username": "bob",
                    "first_name": "Bob",
                    "last_name": "Jones",
                },
            }
            return users[user_id]

        mock_client.driver.users.get_user.side_effect = mock_get_user

        # Get enriched posts
        result = mock_client.get_posts_enriched("channel1", per_page=20)

        assert len(result) == 2

        # Check first post
        assert result[0]["id"] == "post1"
        assert result[0]["username"] == "alice"
        assert result[0]["user_display_name"] == "Alice Smith"
        assert result[0]["message"] == "Hello"
        assert "create_at_formatted" in result[0]

        # Check second post
        assert result[1]["id"] == "post2"
        assert result[1]["username"] == "bob"
        assert result[1]["user_display_name"] == "Bob Jones"

    def test_get_posts_enriched_uses_cache(self, mock_client):
        """Test enriched posts uses cached user data."""
        # Pre-cache users
        mock_client.cache.set_user(
            "user1", {"id": "user1", "username": "alice", "first_name": "Alice", "last_name": ""}
        )

        # Mock posts response
        posts_data = {
            "posts": {
                "post1": {
                    "id": "post1",
                    "user_id": "user1",
                    "message": "Hello",
                    "create_at": 1728057600000,
                    "channel_id": "channel1",
                }
            },
            "order": ["post1"],
        }

        mock_client.driver.posts.get_posts_for_channel.return_value = posts_data

        # Get enriched posts
        result = mock_client.get_posts_enriched("channel1", per_page=20)

        assert len(result) == 1
        assert result[0]["username"] == "alice"

        # Should not call API for users since cached
        mock_client.driver.users.get_user.assert_not_called()

    def test_get_posts_enriched_empty_response(self, mock_client):
        """Test enriched posts handles empty response."""
        mock_client.driver.posts.get_posts_for_channel.return_value = {
            "posts": {},
            "order": [],
        }

        result = mock_client.get_posts_enriched("channel1")

        assert result == []


class TestSearchPostsEnriched:
    """Tests for enriched search_posts functionality."""

    def test_search_posts_enriched_with_users_and_channels(self, mock_client):
        """Test search returns enriched results with user and channel info."""
        # Mock search response (posts as dict)
        search_results = {
            "posts": {
                "post1": {
                    "id": "post1",
                    "user_id": "user1",
                    "channel_id": "channel1",
                    "message": "Found this",
                    "create_at": 1728057600000,
                }
            }
        }

        mock_client.driver.posts.search_for_team_posts.return_value = search_results

        # Mock user response
        mock_client.driver.users.get_user.return_value = {
            "id": "user1",
            "username": "alice",
            "first_name": "Alice",
            "last_name": "Smith",
        }

        # Mock channel response
        mock_client.driver.channels.get_channel.return_value = {
            "id": "channel1",
            "name": "general",
            "display_name": "General",
        }

        # Search with enrichment
        result = mock_client.search_posts_enriched("team1", "search term")

        assert len(result) == 1
        assert result[0]["username"] == "alice"
        assert result[0]["user_display_name"] == "Alice Smith"
        assert result[0]["channel_name"] == "general"
        assert result[0]["channel_display_name"] == "General"
        assert "create_at_formatted" in result[0]

    def test_search_posts_enriched_caches_results(self, mock_client):
        """Test search enrichment caches users and channels."""
        # Mock search response
        search_results = {
            "posts": {
                "post1": {
                    "id": "post1",
                    "user_id": "user1",
                    "channel_id": "channel1",
                    "message": "Test",
                    "create_at": 1728057600000,
                }
            }
        }

        mock_client.driver.posts.search_for_team_posts.return_value = search_results

        # Mock responses
        mock_client.driver.users.get_user.return_value = {
            "id": "user1",
            "username": "alice",
            "first_name": "",
            "last_name": "",
        }
        mock_client.driver.channels.get_channel.return_value = {
            "id": "channel1",
            "name": "general",
            "display_name": "General",
        }

        # First search
        result1 = mock_client.search_posts_enriched("team1", "term1")

        # Verify data cached
        assert mock_client.cache.get_user("user1") is not None
        assert mock_client.cache.get_channel("channel1") is not None

        # Reset mocks
        mock_client.driver.users.get_user.reset_mock()
        mock_client.driver.channels.get_channel.reset_mock()

        # Second search with same user/channel
        search_results2 = {
            "posts": {
                "post2": {
                    "id": "post2",
                    "user_id": "user1",  # Same user
                    "channel_id": "channel1",  # Same channel
                    "message": "Test2",
                    "create_at": 1728057700000,
                }
            }
        }
        mock_client.driver.posts.search_for_team_posts.return_value = search_results2

        result2 = mock_client.search_posts_enriched("team1", "term2")

        # Should use cache, not call API again
        mock_client.driver.users.get_user.assert_not_called()
        mock_client.driver.channels.get_channel.assert_not_called()

        assert result2[0]["username"] == "alice"
        assert result2[0]["channel_name"] == "general"


class TestGetTeamByName:
    """Tests for get_team_by_name functionality."""

    def test_get_team_by_name_found(self, mock_client):
        """Test getting team by name when it exists."""
        teams = [
            {"id": "team1", "name": "engineering", "display_name": "Engineering"},
            {"id": "team2", "name": "sales", "display_name": "Sales"},
        ]

        mock_client.driver.teams.get_user_teams.return_value = teams

        result = mock_client.get_team_by_name("engineering")

        assert result["id"] == "team1"
        assert result["name"] == "engineering"

        # Should be cached
        assert mock_client.cache.get_team_by_name("engineering") is not None

    def test_get_team_by_name_uses_cache(self, mock_client):
        """Test get_team_by_name uses cache."""
        # Pre-cache team
        team_data = {"id": "team1", "name": "engineering", "display_name": "Engineering"}
        mock_client.cache.set_team("team1", team_data)

        result = mock_client.get_team_by_name("engineering")

        assert result == team_data
        # Should not call API
        mock_client.driver.teams.get_user_teams.assert_not_called()

    def test_get_team_by_name_not_found(self, mock_client):
        """Test getting team by name when it doesn't exist."""
        teams = [{"id": "team1", "name": "engineering", "display_name": "Engineering"}]

        mock_client.driver.teams.get_user_teams.return_value = teams

        with pytest.raises(ValueError, match="Team 'nonexistent' not found"):
            mock_client.get_team_by_name("nonexistent")


class TestGetPostsByChannelName:
    """Tests for get_posts_by_channel_name functionality."""

    def test_get_posts_by_channel_name(self, mock_client):
        """Test getting posts by team and channel names."""
        # Mock team lookup
        teams = [{"id": "team1", "name": "engineering", "display_name": "Engineering"}]
        mock_client.driver.teams.get_user_teams.return_value = teams

        # Mock channel lookup
        mock_client.driver.channels.get_channel_by_name.return_value = {
            "id": "channel1",
            "name": "general",
            "team_id": "team1",
        }

        # Mock posts
        posts_data = {
            "posts": {
                "post1": {
                    "id": "post1",
                    "user_id": "user1",
                    "message": "Hello",
                    "create_at": 1728057600000,
                    "channel_id": "channel1",
                }
            },
            "order": ["post1"],
        }
        mock_client.driver.posts.get_posts_for_channel.return_value = posts_data

        # Mock user
        mock_client.driver.users.get_user.return_value = {
            "id": "user1",
            "username": "alice",
            "first_name": "Alice",
            "last_name": "",
        }

        # Get posts by name
        result = mock_client.get_posts_by_channel_name("engineering", "general", limit=20)

        assert len(result) == 1
        assert result[0]["username"] == "alice"
        assert result[0]["message"] == "Hello"


class TestSendMessageByChannelName:
    """Tests for send_message_by_channel_name functionality."""

    def test_send_message_by_channel_name(self, mock_client):
        """Test sending message by team and channel names."""
        # Mock team lookup
        teams = [{"id": "team1", "name": "engineering", "display_name": "Engineering"}]
        mock_client.driver.teams.get_user_teams.return_value = teams

        # Mock channel lookup
        mock_client.driver.channels.get_channel_by_name.return_value = {
            "id": "channel1",
            "name": "general",
            "team_id": "team1",
        }

        # Mock post creation
        mock_client.driver.posts.create_post.return_value = {
            "id": "post123",
            "message": "Test message",
        }

        # Send message
        result = mock_client.send_message_by_channel_name(
            "engineering", "general", "Test message"
        )

        assert result["id"] == "post123"
        mock_client.driver.posts.create_post.assert_called_once()


class TestSearchMessagesByTeamName:
    """Tests for search_messages_by_team_name functionality."""

    def test_search_messages_by_team_name(self, mock_client):
        """Test searching messages by team name."""
        # Mock team lookup
        teams = [{"id": "team1", "name": "engineering", "display_name": "Engineering"}]
        mock_client.driver.teams.get_user_teams.return_value = teams

        # Mock search results
        search_results = {
            "posts": {
                "post1": {
                    "id": "post1",
                    "user_id": "user1",
                    "channel_id": "channel1",
                    "message": "Found it",
                    "create_at": 1728057600000,
                }
            }
        }
        mock_client.driver.posts.search_for_team_posts.return_value = search_results

        # Mock user and channel
        mock_client.driver.users.get_user.return_value = {
            "id": "user1",
            "username": "alice",
            "first_name": "",
            "last_name": "",
        }
        mock_client.driver.channels.get_channel.return_value = {
            "id": "channel1",
            "name": "general",
            "display_name": "General",
        }

        # Search by team name
        result = mock_client.search_messages_by_team_name("engineering", "search query")

        assert len(result) == 1
        assert result[0]["username"] == "alice"
        assert result[0]["channel_name"] == "general"
