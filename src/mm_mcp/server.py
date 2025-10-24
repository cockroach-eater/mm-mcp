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



async def cleanup_client() -> None:
    """Cleanup and disconnect the Mattermost client."""
    global _client
    if _client is not None:
        try:
            _client.disconnect()
        except Exception:
            pass  # Ignore cleanup errors
        finally:
            _client = None

async def get_client() -> MattermostClient:
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
        try:
            _client = MattermostClient(_config)
            # Ensure connection is established
            await _client.connect()
        except Exception as e:
            # Reset client on connection failure so retry can work
            _client = None
            raise RuntimeError(f"Failed to connect to Mattermost: {e}") from e
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
            description="Get recent posts from a channel with enriched user information (includes usernames and formatted timestamps). Use this instead of fetching user info separately.",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "The ID of the channel",
                    },
                    "page": {
                        "type": "number",
                        "description": "Page number for pagination (default: 0)",
                        "default": 0,
                    },
                    "per_page": {
                        "type": "number",
                        "description": "Number of posts per page (default: 20, max: 200)",
                        "default": 20,
                    },
                },
                "required": ["channel_id"],
            },
        ),
        Tool(
            name="get_posts_by_name",
            description="Get recent posts from a channel using team and channel names (simpler than using IDs). Returns enriched posts with user information.",
            inputSchema={
                "type": "object",
                "properties": {
                    "team_name": {
                        "type": "string",
                        "description": "The team name (not display name)",
                    },
                    "channel_name": {
                        "type": "string",
                        "description": "The channel name (not display name, without # prefix)",
                    },
                    "page": {
                        "type": "number",
                        "description": "Page number for pagination (default: 0)",
                        "default": 0,
                    },
                    "per_page": {
                        "type": "number",
                        "description": "Number of posts per page (default: 20, max: 200)",
                        "default": 20,
                    },
                },
                "required": ["team_name", "channel_name"],
            },
        ),
        Tool(
            name="send_message",
            description="Send a message to a channel by channel ID",
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
            name="send_message_by_name",
            description="Send a message to a channel using team and channel names (simpler than using IDs)",
            inputSchema={
                "type": "object",
                "properties": {
                    "team_name": {
                        "type": "string",
                        "description": "The team name (not display name)",
                    },
                    "channel_name": {
                        "type": "string",
                        "description": "The channel name (not display name, without # prefix)",
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
                "required": ["team_name", "channel_name", "message"],
            },
        ),
        Tool(
            name="search_messages",
            description="Search for messages in a team with enriched user and channel information. Returns results with usernames and channel names included.",
            inputSchema={
                "type": "object",
                "properties": {
                    "team_id": {
                        "type": "string",
                        "description": "The ID of the team to search in",
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query string (supports from:username and in:channel syntax)",
                    },
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of results to return (default: 50)",
                        "default": 50,
                    },
                },
                "required": ["team_id", "query"],
            },
        ),
        Tool(
            name="search_messages_by_team_name",
            description="Search for messages using team name (simpler than using team ID). Returns enriched results with user and channel information.",
            inputSchema={
                "type": "object",
                "properties": {
                    "team_name": {
                        "type": "string",
                        "description": "The team name (not display name)",
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query string (supports from:username and in:channel syntax)",
                    },
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of results to return (default: 50)",
                        "default": 50,
                    },
                },
                "required": ["team_name", "query"],
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
    global _client
    
    try:
        client = await get_client()
    except RuntimeError as e:
        return [TextContent(type="text", text=f"Connection error: {str(e)}")]

    try:
        if name == "get_teams":
            teams = client.get_teams()
            # Return only essential fields to reduce token usage
            formatted_teams = [
                {
                    "id": team.get("id"),
                    "name": team.get("name"),
                    "display_name": team.get("display_name"),
                }
                for team in teams
            ]
            return [TextContent(type="text", text=json.dumps(formatted_teams, indent=2))]

        elif name == "get_channels":
            team_id = arguments["team_id"]
            channels = client.get_channels(team_id)
            # Return only essential fields to reduce token usage
            formatted_channels = [
                {
                    "id": channel.get("id"),
                    "name": channel.get("name"),
                    "display_name": channel.get("display_name"),
                    "type": channel.get("type"),
                }
                for channel in channels
            ]
            return [TextContent(type="text", text=json.dumps(formatted_channels, indent=2))]

        elif name == "get_posts":
            channel_id = arguments["channel_id"]
            page = arguments.get("page", 0)
            per_page = arguments.get("per_page", 20)
            enriched_posts = client.get_posts_enriched(channel_id, page=page, per_page=per_page)
            return [TextContent(type="text", text=json.dumps(enriched_posts, indent=2))]

        elif name == "get_posts_by_name":
            team_name = arguments["team_name"]
            channel_name = arguments["channel_name"]
            page = arguments.get("page", 0)
            per_page = arguments.get("per_page", 20)
            try:
                enriched_posts = client.get_posts_by_channel_name(team_name, channel_name, page, per_page)
                return [TextContent(type="text", text=json.dumps(enriched_posts, indent=2))]
            except ValueError as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]

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

        elif name == "send_message_by_name":
            team_name = arguments["team_name"]
            channel_name = arguments["channel_name"]
            message = arguments["message"]
            reply_to = arguments.get("reply_to")

            try:
                post = client.send_message_by_channel_name(team_name, channel_name, message, reply_to)
                return [
                    TextContent(
                        type="text",
                        text=f"Message sent successfully to #{channel_name}. Post ID: {post.get('id')}",
                    )
                ]
            except ValueError as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]

        elif name == "search_messages":
            team_id = arguments["team_id"]
            query = arguments["query"]
            limit = arguments.get("limit", 50)

            enriched_results = client.search_posts_enriched(team_id, query)
            # Limit results to prevent token overflow
            limited_results = enriched_results[:limit]
            return [TextContent(type="text", text=json.dumps(limited_results, indent=2))]

        elif name == "search_messages_by_team_name":
            team_name = arguments["team_name"]
            query = arguments["query"]
            limit = arguments.get("limit", 50)

            try:
                enriched_results = client.search_messages_by_team_name(team_name, query)
                # Limit results to prevent token overflow
                limited_results = enriched_results[:limit]
                return [TextContent(type="text", text=json.dumps(limited_results, indent=2))]
            except ValueError as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]

        elif name == "get_channel_by_name":
            team_id = arguments["team_id"]
            channel_name = arguments["channel_name"]

            channel = client.get_channel_by_name(team_id, channel_name)
            # Return only essential fields to reduce token usage
            formatted_channel = {
                "id": channel.get("id"),
                "name": channel.get("name"),
                "display_name": channel.get("display_name"),
                "type": channel.get("type"),
            }
            return [TextContent(type="text", text=json.dumps(formatted_channel, indent=2))]

        elif name == "get_user_info":
            user_id = arguments.get("user_id", "me")
            user = client.get_user(user_id)
            # Return only essential fields to reduce token usage
            formatted_user = {
                "id": user.get("id"),
                "username": user.get("username"),
                "email": user.get("email"),
                "first_name": user.get("first_name"),
                "last_name": user.get("last_name"),
                "nickname": user.get("nickname"),
            }
            return [TextContent(type="text", text=json.dumps(formatted_user, indent=2))]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        # Log the error type for debugging
        import sys
        error_msg = str(e).lower()
        error_type = type(e).__name__
        
        # Be more specific about when to reset client
        # Only reset on actual authentication/session errors, not general API errors
        auth_error_indicators = [
            "session is invalid",
            "session expired", 
            "invalid or expired session",
            "unauthorized",
            "authentication required",
            "authentication failed",
            "token expired",
            "please login again",
        ]
        
        is_auth_error = any(indicator in error_msg for indicator in auth_error_indicators)
        
        # Also check for 401 status in error message
        if "401" in error_msg and ("status" in error_msg or "error" in error_msg):
            is_auth_error = True
        
        if is_auth_error:
            print(f"[mm-mcp] Authentication error detected: {error_type}: {str(e)}", file=sys.stderr)
            _client = None
            return [TextContent(type="text", text=f"Authentication error (will retry on next request): {str(e)}")]
        
        # For non-auth errors, just return the error without resetting client
        print(f"[mm-mcp] Tool error: {error_type}: {str(e)}", file=sys.stderr)
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
    try:
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())
    finally:
        # Cleanup client on shutdown
        await cleanup_client()


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
