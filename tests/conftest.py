"""Pytest configuration and shared fixtures."""

import pytest


@pytest.fixture
def sample_user():
    """Sample user data."""
    return {
        "id": "user123",
        "username": "john.doe",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "nickname": "Johnny",
    }


@pytest.fixture
def sample_team():
    """Sample team data."""
    return {
        "id": "team123",
        "name": "engineering",
        "display_name": "Engineering Team",
        "description": "Engineering team",
    }


@pytest.fixture
def sample_channel():
    """Sample channel data."""
    return {
        "id": "channel123",
        "team_id": "team123",
        "name": "general",
        "display_name": "General",
        "type": "O",
    }


@pytest.fixture
def sample_post():
    """Sample post data."""
    return {
        "id": "post123",
        "user_id": "user123",
        "channel_id": "channel123",
        "message": "Hello, world!",
        "create_at": 1728057600000,
        "update_at": 1728057600000,
    }


@pytest.fixture
def sample_posts_response():
    """Sample posts API response."""
    return {
        "posts": {
            "post1": {
                "id": "post1",
                "user_id": "user1",
                "channel_id": "channel1",
                "message": "First post",
                "create_at": 1728057600000,
            },
            "post2": {
                "id": "post2",
                "user_id": "user2",
                "channel_id": "channel1",
                "message": "Second post",
                "create_at": 1728057660000,
            },
            "post3": {
                "id": "post3",
                "user_id": "user1",
                "channel_id": "channel1",
                "message": "Third post",
                "create_at": 1728057720000,
            },
        },
        "order": ["post1", "post2", "post3"],
    }


@pytest.fixture
def sample_users_map():
    """Sample users map for enrichment."""
    return {
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
