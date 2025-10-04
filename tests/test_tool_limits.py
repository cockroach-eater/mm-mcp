"""Tests for tool limit parameters to prevent token overflow."""

import json
from unittest.mock import AsyncMock, Mock, patch

import pytest

from mm_mcp.config import MattermostConfig
from mm_mcp.mattermost import MattermostClient
from mm_mcp.server import call_tool


@pytest.fixture
def mock_client_for_server():
    """Create a mock client for server tests."""
    config = Mock(spec=MattermostConfig)
    config.get_parsed_config.return_value = {
        "url": "https://mattermost.example.com",
        "token": "test_token",
    }
    config.has_token_auth = True
    config.has_password_auth = False

    with patch("mm_mcp.mattermost.Driver") as mock_driver_class:
        client = MattermostClient(config, cache_ttl=300.0)
        client.driver = mock_driver_class.return_value
        client._authenticated = True
        yield client


@pytest.fixture
def mock_get_client(mock_client_for_server):
    """Mock the get_client function to return our test client."""
    async def _get_client():
        return mock_client_for_server

    with patch("mm_mcp.server.get_client", new=_get_client):
        yield mock_client_for_server


class TestGetPostsLimit:
    """Tests for get_posts limit parameter."""

    @pytest.mark.asyncio
    async def test_get_posts_respects_default_limit(self, mock_get_client):
        """Test get_posts uses default limit of 20."""
        # Create 30 posts
        posts_data = {
            "posts": {f"post{i}": {
                "id": f"post{i}",
                "user_id": "user1",
                "message": f"Message {i}",
                "create_at": 1728057600000 + i * 1000,
                "channel_id": "channel1",
            } for i in range(30)},
            "order": [f"post{i}" for i in range(30)],
        }

        mock_get_client.driver.posts.get_posts_for_channel.return_value = posts_data
        mock_get_client.driver.users.get_user.return_value = {
            "id": "user1",
            "username": "alice",
            "first_name": "Alice",
            "last_name": "",
        }

        # Call without explicit limit (should use default of 20)
        result = await call_tool("get_posts", {"channel_id": "channel1"})

        # Parse the JSON response
        response_text = result[0].text
        posts = json.loads(response_text)

        # Should return only 20 posts (default limit)
        assert len(posts) == 20

    @pytest.mark.asyncio
    async def test_get_posts_respects_custom_limit(self, mock_get_client):
        """Test get_posts respects custom limit parameter."""
        # Create 30 posts
        posts_data = {
            "posts": {f"post{i}": {
                "id": f"post{i}",
                "user_id": "user1",
                "message": f"Message {i}",
                "create_at": 1728057600000 + i * 1000,
                "channel_id": "channel1",
            } for i in range(30)},
            "order": [f"post{i}" for i in range(30)],
        }

        mock_get_client.driver.posts.get_posts_for_channel.return_value = posts_data
        mock_get_client.driver.users.get_user.return_value = {
            "id": "user1",
            "username": "alice",
            "first_name": "",
            "last_name": "",
        }

        # Call with custom limit of 10
        result = await call_tool("get_posts", {"channel_id": "channel1", "limit": 10})

        # Parse the JSON response
        response_text = result[0].text
        posts = json.loads(response_text)

        # Should return only 10 posts
        assert len(posts) == 10

    @pytest.mark.asyncio
    async def test_get_posts_limit_larger_than_results(self, mock_get_client):
        """Test get_posts when limit is larger than available posts."""
        # Create only 5 posts
        posts_data = {
            "posts": {f"post{i}": {
                "id": f"post{i}",
                "user_id": "user1",
                "message": f"Message {i}",
                "create_at": 1728057600000 + i * 1000,
                "channel_id": "channel1",
            } for i in range(5)},
            "order": [f"post{i}" for i in range(5)],
        }

        mock_get_client.driver.posts.get_posts_for_channel.return_value = posts_data
        mock_get_client.driver.users.get_user.return_value = {
            "id": "user1",
            "username": "alice",
            "first_name": "",
            "last_name": "",
        }

        # Call with limit of 20 (more than available)
        result = await call_tool("get_posts", {"channel_id": "channel1", "limit": 20})

        # Parse the JSON response
        response_text = result[0].text
        posts = json.loads(response_text)

        # Should return all 5 posts
        assert len(posts) == 5


class TestGetPostsByNameLimit:
    """Tests for get_posts_by_name limit parameter."""

    @pytest.mark.asyncio
    async def test_get_posts_by_name_respects_default_limit(self, mock_get_client):
        """Test get_posts_by_name uses default limit of 20."""
        # Mock team lookup
        teams = [{"id": "team1", "name": "engineering", "display_name": "Engineering"}]
        mock_get_client.driver.teams.get_user_teams.return_value = teams

        # Mock channel lookup
        mock_get_client.driver.channels.get_channel_by_name.return_value = {
            "id": "channel1",
            "name": "general",
            "team_id": "team1",
        }

        # Create 30 posts
        posts_data = {
            "posts": {f"post{i}": {
                "id": f"post{i}",
                "user_id": "user1",
                "message": f"Message {i}",
                "create_at": 1728057600000 + i * 1000,
                "channel_id": "channel1",
            } for i in range(30)},
            "order": [f"post{i}" for i in range(30)],
        }

        mock_get_client.driver.posts.get_posts_for_channel.return_value = posts_data
        mock_get_client.driver.users.get_user.return_value = {
            "id": "user1",
            "username": "alice",
            "first_name": "",
            "last_name": "",
        }

        # Call without explicit limit
        result = await call_tool(
            "get_posts_by_name",
            {"team_name": "engineering", "channel_name": "general"}
        )

        # Parse the JSON response
        response_text = result[0].text
        posts = json.loads(response_text)

        # Should return only 20 posts (default)
        assert len(posts) == 20

    @pytest.mark.asyncio
    async def test_get_posts_by_name_respects_custom_limit(self, mock_get_client):
        """Test get_posts_by_name respects custom limit."""
        # Mock team lookup
        teams = [{"id": "team1", "name": "engineering", "display_name": "Engineering"}]
        mock_get_client.driver.teams.get_user_teams.return_value = teams

        # Mock channel lookup
        mock_get_client.driver.channels.get_channel_by_name.return_value = {
            "id": "channel1",
            "name": "general",
            "team_id": "team1",
        }

        # Create 30 posts
        posts_data = {
            "posts": {f"post{i}": {
                "id": f"post{i}",
                "user_id": "user1",
                "message": f"Message {i}",
                "create_at": 1728057600000 + i * 1000,
                "channel_id": "channel1",
            } for i in range(30)},
            "order": [f"post{i}" for i in range(30)],
        }

        mock_get_client.driver.posts.get_posts_for_channel.return_value = posts_data
        mock_get_client.driver.users.get_user.return_value = {
            "id": "user1",
            "username": "alice",
            "first_name": "",
            "last_name": "",
        }

        # Call with custom limit of 5
        result = await call_tool(
            "get_posts_by_name",
            {"team_name": "engineering", "channel_name": "general", "limit": 5}
        )

        # Parse the JSON response
        response_text = result[0].text
        posts = json.loads(response_text)

        # Should return only 5 posts
        assert len(posts) == 5


class TestSearchMessagesLimit:
    """Tests for search_messages limit parameter."""

    @pytest.mark.asyncio
    async def test_search_messages_respects_default_limit(self, mock_get_client):
        """Test search_messages uses default limit of 50."""
        # Create 100 search results
        search_results = {
            "posts": {f"post{i}": {
                "id": f"post{i}",
                "user_id": "user1",
                "channel_id": "channel1",
                "message": f"Search result {i}",
                "create_at": 1728057600000 + i * 1000,
            } for i in range(100)}
        }

        mock_get_client.driver.posts.search_for_team_posts.return_value = search_results
        mock_get_client.driver.users.get_user.return_value = {
            "id": "user1",
            "username": "alice",
            "first_name": "",
            "last_name": "",
        }
        mock_get_client.driver.channels.get_channel.return_value = {
            "id": "channel1",
            "name": "general",
            "display_name": "General",
        }

        # Call without explicit limit (should use default of 50)
        result = await call_tool(
            "search_messages",
            {"team_id": "team1", "query": "test"}
        )

        # Parse the JSON response
        response_text = result[0].text
        results = json.loads(response_text)

        # Should return only 50 results (default limit)
        assert len(results) == 50

    @pytest.mark.asyncio
    async def test_search_messages_respects_custom_limit(self, mock_get_client):
        """Test search_messages respects custom limit parameter."""
        # Create 100 search results
        search_results = {
            "posts": {f"post{i}": {
                "id": f"post{i}",
                "user_id": "user1",
                "channel_id": "channel1",
                "message": f"Search result {i}",
                "create_at": 1728057600000 + i * 1000,
            } for i in range(100)}
        }

        mock_get_client.driver.posts.search_for_team_posts.return_value = search_results
        mock_get_client.driver.users.get_user.return_value = {
            "id": "user1",
            "username": "alice",
            "first_name": "",
            "last_name": "",
        }
        mock_get_client.driver.channels.get_channel.return_value = {
            "id": "channel1",
            "name": "general",
            "display_name": "General",
        }

        # Call with custom limit of 10
        result = await call_tool(
            "search_messages",
            {"team_id": "team1", "query": "test", "limit": 10}
        )

        # Parse the JSON response
        response_text = result[0].text
        results = json.loads(response_text)

        # Should return only 10 results
        assert len(results) == 10

    @pytest.mark.asyncio
    async def test_search_messages_limit_prevents_token_overflow(self, mock_get_client):
        """Test search limit prevents returning too many results."""
        # Create 1000 search results (would be huge token usage)
        search_results = {
            "posts": {f"post{i}": {
                "id": f"post{i}",
                "user_id": f"user{i % 10}",  # 10 unique users
                "channel_id": f"channel{i % 5}",  # 5 unique channels
                "message": f"Very long message with lots of text that would consume many tokens {i}",
                "create_at": 1728057600000 + i * 1000,
            } for i in range(1000)}
        }

        mock_get_client.driver.posts.search_for_team_posts.return_value = search_results

        # Mock user responses
        def mock_get_user(user_id):
            return {
                "id": user_id,
                "username": f"user_{user_id}",
                "first_name": "User",
                "last_name": user_id,
            }

        mock_get_client.driver.users.get_user.side_effect = mock_get_user

        # Mock channel responses
        def mock_get_channel(channel_id):
            return {
                "id": channel_id,
                "name": f"channel_{channel_id}",
                "display_name": f"Channel {channel_id}",
            }

        mock_get_client.driver.channels.get_channel.side_effect = mock_get_channel

        # Call with reasonable limit
        result = await call_tool(
            "search_messages",
            {"team_id": "team1", "query": "test", "limit": 50}
        )

        # Parse the JSON response
        response_text = result[0].text
        results = json.loads(response_text)

        # Should return only 50 results, not all 1000
        assert len(results) == 50


class TestSearchMessagesByTeamNameLimit:
    """Tests for search_messages_by_team_name limit parameter."""

    @pytest.mark.asyncio
    async def test_search_by_team_name_respects_default_limit(self, mock_get_client):
        """Test search_messages_by_team_name uses default limit of 50."""
        # Mock team lookup
        teams = [{"id": "team1", "name": "engineering", "display_name": "Engineering"}]
        mock_get_client.driver.teams.get_user_teams.return_value = teams

        # Create 100 search results
        search_results = {
            "posts": {f"post{i}": {
                "id": f"post{i}",
                "user_id": "user1",
                "channel_id": "channel1",
                "message": f"Search result {i}",
                "create_at": 1728057600000 + i * 1000,
            } for i in range(100)}
        }

        mock_get_client.driver.posts.search_for_team_posts.return_value = search_results
        mock_get_client.driver.users.get_user.return_value = {
            "id": "user1",
            "username": "alice",
            "first_name": "",
            "last_name": "",
        }
        mock_get_client.driver.channels.get_channel.return_value = {
            "id": "channel1",
            "name": "general",
            "display_name": "General",
        }

        # Call without explicit limit
        result = await call_tool(
            "search_messages_by_team_name",
            {"team_name": "engineering", "query": "test"}
        )

        # Parse the JSON response
        response_text = result[0].text
        results = json.loads(response_text)

        # Should return only 50 results (default)
        assert len(results) == 50

    @pytest.mark.asyncio
    async def test_search_by_team_name_respects_custom_limit(self, mock_get_client):
        """Test search_messages_by_team_name respects custom limit."""
        # Mock team lookup
        teams = [{"id": "team1", "name": "engineering", "display_name": "Engineering"}]
        mock_get_client.driver.teams.get_user_teams.return_value = teams

        # Create 100 search results
        search_results = {
            "posts": {f"post{i}": {
                "id": f"post{i}",
                "user_id": "user1",
                "channel_id": "channel1",
                "message": f"Search result {i}",
                "create_at": 1728057600000 + i * 1000,
            } for i in range(100)}
        }

        mock_get_client.driver.posts.search_for_team_posts.return_value = search_results
        mock_get_client.driver.users.get_user.return_value = {
            "id": "user1",
            "username": "alice",
            "first_name": "",
            "last_name": "",
        }
        mock_get_client.driver.channels.get_channel.return_value = {
            "id": "channel1",
            "name": "general",
            "display_name": "General",
        }

        # Call with custom limit of 15
        result = await call_tool(
            "search_messages_by_team_name",
            {"team_name": "engineering", "query": "test", "limit": 15}
        )

        # Parse the JSON response
        response_text = result[0].text
        results = json.loads(response_text)

        # Should return only 15 results
        assert len(results) == 15


class TestLimitWithEnrichment:
    """Tests that limits work correctly with data enrichment."""

    @pytest.mark.asyncio
    async def test_limit_applies_after_enrichment(self, mock_get_client):
        """Test that limit is applied after enrichment, not before."""
        # Create 100 posts from multiple users
        posts_data = {
            "posts": {f"post{i}": {
                "id": f"post{i}",
                "user_id": f"user{i % 5}",  # 5 unique users
                "message": f"Message {i}",
                "create_at": 1728057600000 + i * 1000,
                "channel_id": "channel1",
            } for i in range(100)},
            "order": [f"post{i}" for i in range(100)],
        }

        mock_get_client.driver.posts.get_posts_for_channel.return_value = posts_data

        # Mock user responses
        def mock_get_user(user_id):
            return {
                "id": user_id,
                "username": f"user_{user_id}",
                "first_name": f"User",
                "last_name": user_id,
            }

        mock_get_client.driver.users.get_user.side_effect = mock_get_user

        # Call with limit of 10
        result = await call_tool("get_posts", {"channel_id": "channel1", "limit": 10})

        # Parse the JSON response
        response_text = result[0].text
        posts = json.loads(response_text)

        # Should return exactly 10 posts
        assert len(posts) == 10

        # All posts should be enriched (have username field)
        for post in posts:
            assert "username" in post
            assert post["username"].startswith("user_")

    @pytest.mark.asyncio
    async def test_enrichment_fetches_only_needed_users(self, mock_get_client):
        """Test that enrichment only fetches users for limited results."""
        # Create 100 posts but with limited unique users
        posts_data = {
            "posts": {f"post{i}": {
                "id": f"post{i}",
                "user_id": f"user{i % 3}",  # Only 3 unique users in first 10 posts
                "message": f"Message {i}",
                "create_at": 1728057600000 + i * 1000,
                "channel_id": "channel1",
            } for i in range(100)},
            "order": [f"post{i}" for i in range(100)],
        }

        mock_get_client.driver.posts.get_posts_for_channel.return_value = posts_data

        # Mock user responses
        def mock_get_user(user_id):
            return {
                "id": user_id,
                "username": f"user_{user_id}",
                "first_name": "",
                "last_name": "",
            }

        mock_get_client.driver.users.get_user.side_effect = mock_get_user

        # Call with limit of 10
        result = await call_tool("get_posts", {"channel_id": "channel1", "limit": 10})

        # Parse the JSON response
        response_text = result[0].text
        posts = json.loads(response_text)

        assert len(posts) == 10

        # Should only fetch 3 unique users (user0, user1, user2) for first 10 posts
        # Not all users from all 100 posts
        user_api_calls = mock_get_client.driver.users.get_user.call_count
        assert user_api_calls == 3  # Only fetched users for limited results


class TestLimitEdgeCases:
    """Tests for edge cases with limit parameters."""

    @pytest.mark.asyncio
    async def test_limit_zero(self, mock_get_client):
        """Test behavior when limit is zero."""
        posts_data = {
            "posts": {"post1": {
                "id": "post1",
                "user_id": "user1",
                "message": "Message",
                "create_at": 1728057600000,
                "channel_id": "channel1",
            }},
            "order": ["post1"],
        }

        mock_get_client.driver.posts.get_posts_for_channel.return_value = posts_data
        mock_get_client.driver.users.get_user.return_value = {
            "id": "user1",
            "username": "alice",
            "first_name": "",
            "last_name": "",
        }

        # Call with limit of 0
        result = await call_tool("get_posts", {"channel_id": "channel1", "limit": 0})

        # Parse the JSON response
        response_text = result[0].text
        posts = json.loads(response_text)

        # Should return empty list
        assert len(posts) == 0

    @pytest.mark.asyncio
    async def test_limit_one(self, mock_get_client):
        """Test limit of exactly one result."""
        posts_data = {
            "posts": {
                "post1": {
                    "id": "post1",
                    "user_id": "user1",
                    "message": "Message 1",
                    "create_at": 1728057600000,
                    "channel_id": "channel1",
                },
                "post2": {
                    "id": "post2",
                    "user_id": "user1",
                    "message": "Message 2",
                    "create_at": 1728057660000,
                    "channel_id": "channel1",
                },
            },
            "order": ["post1", "post2"],
        }

        mock_get_client.driver.posts.get_posts_for_channel.return_value = posts_data
        mock_get_client.driver.users.get_user.return_value = {
            "id": "user1",
            "username": "alice",
            "first_name": "",
            "last_name": "",
        }

        # Call with limit of 1
        result = await call_tool("get_posts", {"channel_id": "channel1", "limit": 1})

        # Parse the JSON response
        response_text = result[0].text
        posts = json.loads(response_text)

        # Should return exactly 1 post
        assert len(posts) == 1
        assert posts[0]["id"] == "post1"
