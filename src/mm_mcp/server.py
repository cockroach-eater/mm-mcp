"""Main MCP server implementation for Mattermost integration."""

import argparse
import asyncio
import json
import sys
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    TextContent,
    Tool,
)

from .config import MattermostConfig
from .mattermost import MattermostClient

# Initialize server
app = Server("mm-mcp")

# Global client instance
_client: MattermostClient | None = None
_config: MattermostConfig | None = None


def get_client() -> MattermostClient:
    """Get or create the Mattermost client.

    Returns:
        The Mattermost client instance.

    Raises:
        RuntimeError: If the client is not initialized.
    """
    global _client, _config
    if _client is None:
        if _config is None:
            raise RuntimeError("Configuration not initialized")
        _client = MattermostClient(_config)
        # Run connection in event loop
        asyncio.create_task(_client.connect())
    return _client


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools.

    Returns:
        List of available tools.
    """
    return [
        Tool(
            name="get_teams",
            description="Get all teams the authenticated user is a member of",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_channels",
            description="Get all channels in a specific team",
            inputSchema={
                "type": "object",
                "properties": {
                    "team_id": {
                        "type": "string",
                        "description": "The ID of the team",
                    },
                },
                "required": ["team_id"],
            },
        ),
        Tool(
            name="get_posts",
            description="Get recent posts from a channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "The ID of the channel",
                    },
                    "limit": {
                        "type": "number",
                        "description": "Number of posts to retrieve (default: 20)",
                        "default": 20,
                    },
                },
                "required": ["channel_id"],
            },
        ),
        Tool(
            name="send_message",
            description="Send a message to a channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "The ID of the channel",
                    },
                    "message": {
                        "type": "string",
                        "description": "The message text to send",
                    },
                    "reply_to": {
                        "type": "string",
                        "description": "Optional post ID to reply to",
                    },
                },
                "required": ["channel_id", "message"],
            },
        ),
        Tool(
            name="search_messages",
            description="Search for messages in a team",
            inputSchema={
                "type": "object",
                "properties": {
                    "team_id": {
                        "type": "string",
                        "description": "The ID of the team to search in",
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query string",
                    },
                },
                "required": ["team_id", "query"],
            },
        ),
        Tool(
            name="get_channel_by_name",
            description="Get a channel by its name in a team",
            inputSchema={
                "type": "object",
                "properties": {
                    "team_id": {
                        "type": "string",
                        "description": "The ID of the team",
                    },
                    "channel_name": {
                        "type": "string",
                        "description": "The name of the channel",
                    },
                },
                "required": ["team_id", "channel_name"],
            },
        ),
        Tool(
            name="get_user_info",
            description="Get information about a user",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "The user ID (leave empty for current user)",
                        "default": "me",
                    },
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls.

    Args:
        name: The name of the tool to call.
        arguments: The arguments for the tool.

    Returns:
        List of text content with the tool results.

    Raises:
        ValueError: If the tool name is unknown.
    """
    client = get_client()

    try:
        if name == "get_teams":
            teams = client.get_teams()
            return [TextContent(type="text", text=json.dumps(teams, indent=2))]

        elif name == "get_channels":
            team_id = arguments["team_id"]
            channels = client.get_channels(team_id)
            return [TextContent(type="text", text=json.dumps(channels, indent=2))]

        elif name == "get_posts":
            channel_id = arguments["channel_id"]
            limit = arguments.get("limit", 20)
            posts_data = client.get_posts(channel_id, per_page=limit)

            # Format posts for readability
            posts = posts_data.get("posts", {})
            order = posts_data.get("order", [])

            formatted_posts = []
            for post_id in order[:limit]:
                post = posts.get(post_id, {})
                formatted_posts.append({
                    "id": post.get("id"),
                    "user_id": post.get("user_id"),
                    "message": post.get("message"),
                    "create_at": post.get("create_at"),
                })

            return [TextContent(type="text", text=json.dumps(formatted_posts, indent=2))]

        elif name == "send_message":
            channel_id = arguments["channel_id"]
            message = arguments["message"]
            reply_to = arguments.get("reply_to")

            post = client.create_post(channel_id, message, reply_to)
            return [
                TextContent(
                    type="text",
                    text=f"Message sent successfully. Post ID: {post.get('id')}",
                )
            ]

        elif name == "search_messages":
            team_id = arguments["team_id"]
            query = arguments["query"]

            results = client.search_posts(team_id, query)
            posts = results.get("posts", [])

            formatted_results = [
                {
                    "id": post.get("id"),
                    "user_id": post.get("user_id"),
                    "message": post.get("message"),
                    "channel_id": post.get("channel_id"),
                    "create_at": post.get("create_at"),
                }
                for post in posts
            ]

            return [TextContent(type="text", text=json.dumps(formatted_results, indent=2))]

        elif name == "get_channel_by_name":
            team_id = arguments["team_id"]
            channel_name = arguments["channel_name"]

            channel = client.get_channel_by_name(team_id, channel_name)
            return [TextContent(type="text", text=json.dumps(channel, indent=2))]

        elif name == "get_user_info":
            user_id = arguments.get("user_id", "me")
            user = client.get_user(user_id)
            return [TextContent(type="text", text=json.dumps(user, indent=2))]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


@app.list_resources()
async def list_resources() -> list[Resource]:
    """List available resources.

    Returns:
        List of available resources.
    """
    return []


async def main() -> None:
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


def run() -> None:
    """Entry point for the MCP server."""
    global _config
    
    parser = argparse.ArgumentParser(
        description="MCP server for Mattermost integration"
    )
    parser.add_argument(
        "--url",
        required=True,
        help="Mattermost server URL (e.g., https://mattermost.example.com)",
    )
    
    # Authentication options
    auth_group = parser.add_mutually_exclusive_group(required=True)
    auth_group.add_argument(
        "--token",
        help="Personal access token for authentication",
    )
    auth_group.add_argument(
        "--login",
        help="Login email for password authentication (requires --password)",
    )
    
    parser.add_argument(
        "--password",
        help="Password for password authentication (requires --login)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=443,
        help="Mattermost server port (default: 443)",
    )
    parser.add_argument(
        "--scheme",
        default="https",
        choices=["http", "https"],
        help="URL scheme (default: https)",
    )
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Disable SSL certificate verification (not recommended)",
    )

    args = parser.parse_args()

    # Validate password auth requirements
    if args.login and not args.password:
        parser.error("--password is required when using --login")
    if args.password and not args.login:
        parser.error("--login is required when using --password")

    # Create configuration from arguments
    _config = MattermostConfig(
        url=args.url,
        token=args.token,
        login=args.login,
        password=args.password,
        scheme=args.scheme,
        port=args.port,
        verify=not args.no_verify,
    )
    
    try:
        _config.validate_auth()
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)

    asyncio.run(main())


if __name__ == "__main__":
    run()
