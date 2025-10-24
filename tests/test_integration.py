"""Integration tests for caching behavior across multiple operations."""

from unittest.mock import Mock, patch

import pytest

from mm_mcp.config import MattermostConfig
from mm_mcp.mattermost import MattermostClient


@pytest.fixture
def integrated_client():
    """Create a client with mocked driver for integration tests."""
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


class TestCachingWorkflow:
    """Test caching behavior across typical workflows."""

    def test_workflow_view_multiple_channels(self, integrated_client):
        """Test viewing posts from multiple channels uses cache efficiently."""
        # Setup team data
        teams = [{"id": "team1", "name": "engineering", "display_name": "Engineering"}]
        integrated_client.driver.teams.get_user_teams.return_value = teams

        # Setup channel data
        def mock_get_channel_by_name(team_id, channel_name):
            channels = {
                "general": {"id": "channel1", "name": "general", "team_id": team_id},
                "random": {"id": "channel2", "name": "random", "team_id": team_id},
            }
            return channels[channel_name]

        integrated_client.driver.channels.get_channel_by_name.side_effect = (
            mock_get_channel_by_name
        )

        # Setup posts data - same users across channels
        def mock_get_posts(channel_id, params):
            return {
                "posts": {
                    f"post_{channel_id}_1": {
                        "id": f"post_{channel_id}_1",
                        "user_id": "user1",  # Same user
                        "message": f"Message in {channel_id}",
                        "create_at": 1728057600000,
                        "channel_id": channel_id,
                    }
                },
                "order": [f"post_{channel_id}_1"],
            }

        integrated_client.driver.posts.get_posts_for_channel.side_effect = mock_get_posts

        # Setup user data
        integrated_client.driver.users.get_user.return_value = {
            "id": "user1",
            "username": "alice",
            "first_name": "Alice",
            "last_name": "Smith",
        }

        # View posts from first channel
        posts1 = integrated_client.get_posts_by_channel_name("engineering", "general", 20)
        assert len(posts1) == 1
        assert posts1[0]["username"] == "alice"

        # User API should be called once
        assert integrated_client.driver.users.get_user.call_count == 1

        # View posts from second channel (same user)
        posts2 = integrated_client.get_posts_by_channel_name("engineering", "random", 20)
        assert len(posts2) == 1
        assert posts2[0]["username"] == "alice"

        # User API should still only be called once (cached!)
        assert integrated_client.driver.users.get_user.call_count == 1

        # Verify cache stats
        stats = integrated_client.cache.get_stats()
        assert stats["users"] >= 1
        assert stats["teams"] >= 1
        assert stats["channels"] >= 2

    def test_workflow_search_then_view_channel(self, integrated_client):
        """Test search followed by viewing channel reuses cached data."""
        # Setup team
        teams = [{"id": "team1", "name": "engineering", "display_name": "Engineering"}]
        integrated_client.driver.teams.get_user_teams.return_value = teams

        # Setup search results
        search_results = {
            "posts": {
                "post1": {
                    "id": "post1",
                    "user_id": "user1",
                    "channel_id": "channel1",
                    "message": "Search result",
                    "create_at": 1728057600000,
                }
            }
        }
        integrated_client.driver.posts.search_for_team_posts.return_value = search_results

        # Setup user and channel mocks
        integrated_client.driver.users.get_user.return_value = {
            "id": "user1",
            "username": "alice",
            "first_name": "Alice",
            "last_name": "",
        }
        integrated_client.driver.channels.get_channel.return_value = {
            "id": "channel1",
            "name": "general",
            "display_name": "General",
            "team_id": "team1",
        }

        # Perform search (caches user and channel)
        search_result = integrated_client.search_messages_by_team_name("engineering", "query")
        assert len(search_result) == 1
        assert search_result[0]["username"] == "alice"

        user_calls_after_search = integrated_client.driver.users.get_user.call_count
        channel_calls_after_search = integrated_client.driver.channels.get_channel.call_count

        # Now view the same channel
        integrated_client.driver.posts.get_posts_for_channel.return_value = {
            "posts": {
                "post2": {
                    "id": "post2",
                    "user_id": "user1",  # Same user as search
                    "message": "New post",
                    "create_at": 1728057700000,
                    "channel_id": "channel1",
                }
            },
            "order": ["post2"],
        }

        posts = integrated_client.get_posts_enriched("channel1", per_page=20)
        assert len(posts) == 1
        assert posts[0]["username"] == "alice"

        # Should not make additional user calls (cached)
        assert (
            integrated_client.driver.users.get_user.call_count == user_calls_after_search
        )

    def test_workflow_multiple_searches_same_team(self, integrated_client):
        """Test multiple searches in same team cache team lookup."""
        # Setup team
        teams = [{"id": "team1", "name": "engineering", "display_name": "Engineering"}]
        integrated_client.driver.teams.get_user_teams.return_value = teams

        # Setup search results
        def mock_search(team_id, options):
            return {
                "posts": {
                    "post1": {
                        "id": "post1",
                        "user_id": "user1",
                        "channel_id": "channel1",
                        "message": options["terms"],
                        "create_at": 1728057600000,
                    }
                }
            }

        integrated_client.driver.posts.search_for_team_posts.side_effect = mock_search

        # Mock user and channel
        integrated_client.driver.users.get_user.return_value = {
            "id": "user1",
            "username": "alice",
            "first_name": "",
            "last_name": "",
        }
        integrated_client.driver.channels.get_channel.return_value = {
            "id": "channel1",
            "name": "general",
            "display_name": "General",
        }

        # First search
        result1 = integrated_client.search_messages_by_team_name("engineering", "query1")
        assert len(result1) == 1

        team_calls_after_first = integrated_client.driver.teams.get_user_teams.call_count

        # Second search (same team)
        result2 = integrated_client.search_messages_by_team_name("engineering", "query2")
        assert len(result2) == 1

        # Team lookup should be cached, no additional calls
        assert (
            integrated_client.driver.teams.get_user_teams.call_count
            == team_calls_after_first
        )

    def test_cache_prevents_repeated_api_calls(self, integrated_client):
        """Test cache prevents unnecessary repeated API calls."""
        # Pre-populate cache
        user_data = {
            "id": "user1",
            "username": "alice",
            "first_name": "Alice",
            "last_name": "Smith",
        }
        integrated_client.cache.set_user("user1", user_data)

        team_data = {"id": "team1", "name": "engineering", "display_name": "Engineering"}
        integrated_client.cache.set_team("team1", team_data)

        channel_data = {
            "id": "channel1",
            "name": "general",
            "display_name": "General",
            "team_id": "team1",
        }
        integrated_client.cache.set_channel("channel1", channel_data)

        # Mock posts response
        integrated_client.driver.posts.get_posts_for_channel.return_value = {
            "posts": {
                "post1": {
                    "id": "post1",
                    "user_id": "user1",
                    "message": "Test",
                    "create_at": 1728057600000,
                    "channel_id": "channel1",
                }
            },
            "order": ["post1"],
        }

        # Get enriched posts (everything cached except posts themselves)
        result = integrated_client.get_posts_enriched("channel1")

        assert len(result) == 1
        assert result[0]["username"] == "alice"

        # Should not call user/team/channel APIs
        integrated_client.driver.users.get_user.assert_not_called()
        integrated_client.driver.teams.get_user_teams.assert_not_called()
        integrated_client.driver.channels.get_channel.assert_not_called()

    def test_batch_operations_minimize_api_calls(self, integrated_client):
        """Test batch operations minimize API calls."""
        # Setup posts with multiple unique users
        posts_data = {
            "posts": {
                "post1": {
                    "id": "post1",
                    "user_id": "user1",
                    "message": "Post 1",
                    "create_at": 1728057600000,
                    "channel_id": "channel1",
                },
                "post2": {
                    "id": "post2",
                    "user_id": "user2",
                    "message": "Post 2",
                    "create_at": 1728057660000,
                    "channel_id": "channel1",
                },
                "post3": {
                    "id": "post3",
                    "user_id": "user1",  # Duplicate user
                    "message": "Post 3",
                    "create_at": 1728057720000,
                    "channel_id": "channel1",
                },
                "post4": {
                    "id": "post4",
                    "user_id": "user3",
                    "message": "Post 4",
                    "create_at": 1728057780000,
                    "channel_id": "channel1",
                },
            },
            "order": ["post1", "post2", "post3", "post4"],
        }

        integrated_client.driver.posts.get_posts_for_channel.return_value = posts_data

        # Mock user responses
        def mock_get_user(user_id):
            users = {
                "user1": {"id": "user1", "username": "alice", "first_name": "", "last_name": ""},
                "user2": {"id": "user2", "username": "bob", "first_name": "", "last_name": ""},
                "user3": {"id": "user3", "username": "charlie", "first_name": "", "last_name": ""},
            }
            return users[user_id]

        integrated_client.driver.users.get_user.side_effect = mock_get_user

        # Get enriched posts
        result = integrated_client.get_posts_enriched("channel1", per_page=4)

        assert len(result) == 4

        # Should only call API for 3 unique users, not 4 posts
        assert integrated_client.driver.users.get_user.call_count == 3

        # Verify enrichment
        assert result[0]["username"] == "alice"
        assert result[1]["username"] == "bob"
        assert result[2]["username"] == "alice"  # Duplicate user
        assert result[3]["username"] == "charlie"


class TestErrorRecovery:
    """Test error recovery and fallback behavior."""

    def test_user_fetch_failure_provides_fallback(self, integrated_client):
        """Test user fetch failure provides fallback data."""
        # Mock posts
        posts_data = {
            "posts": {
                "post1": {
                    "id": "post1",
                    "user_id": "user1",
                    "message": "Test",
                    "create_at": 1728057600000,
                    "channel_id": "channel1",
                }
            },
            "order": ["post1"],
        }

        integrated_client.driver.posts.get_posts_for_channel.return_value = posts_data

        # Mock user API to fail
        integrated_client.driver.users.get_user.side_effect = Exception("API error")

        # Should not raise, should provide fallback
        result = integrated_client.get_posts_enriched("channel1")

        assert len(result) == 1
        # Should have fallback username
        assert "username" in result[0]
        assert "user_" in result[0]["username"]

    def test_channel_fetch_failure_provides_fallback(self, integrated_client):
        """Test channel fetch failure provides fallback data."""
        # Mock search results
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

        integrated_client.driver.posts.search_for_team_posts.return_value = search_results

        # Mock user (success)
        integrated_client.driver.users.get_user.return_value = {
            "id": "user1",
            "username": "alice",
            "first_name": "",
            "last_name": "",
        }

        # Mock channel to fail
        integrated_client.driver.channels.get_channel.side_effect = Exception("API error")

        # Should not raise, should provide fallback
        result = integrated_client.search_posts_enriched("team1", "query")

        assert len(result) == 1
        # Should have username (success) and fallback channel
        assert result[0]["username"] == "alice"
        assert "channel_name" in result[0]
        assert "channel_" in result[0]["channel_name"]


class TestCacheStatistics:
    """Test cache statistics tracking."""

    def test_cache_stats_track_entries(self, integrated_client):
        """Test cache statistics track entries correctly."""
        initial_stats = integrated_client.cache.get_stats()
        assert initial_stats["users"] == 0
        assert initial_stats["teams"] == 0
        assert initial_stats["channels"] == 0
        assert initial_stats["posts"] == 0

        # Add entries
        integrated_client.cache.set_user("user1", {"id": "user1"})
        integrated_client.cache.set_team("team1", {"id": "team1", "name": "team"})
        integrated_client.cache.set_channel("channel1", {"id": "channel1"})
        integrated_client.cache.set_post("post1", {"id": "post1"})

        stats = integrated_client.cache.get_stats()
        assert stats["users"] == 1
        assert stats["teams"] == 1
        assert stats["channels"] == 1
        assert stats["posts"] == 1

    def test_cache_clear_resets_stats(self, integrated_client):
        """Test cache clear resets statistics."""
        # Add entries
        integrated_client.cache.set_user("user1", {"id": "user1"})
        integrated_client.cache.set_team("team1", {"id": "team1", "name": "team"})

        stats_before = integrated_client.cache.get_stats()
        assert stats_before["users"] > 0
        assert stats_before["teams"] > 0

        # Clear cache
        integrated_client.cache.clear()

        stats_after = integrated_client.cache.get_stats()
        assert stats_after["users"] == 0
        assert stats_after["teams"] == 0
        assert stats_after["channels"] == 0
        assert stats_after["posts"] == 0
