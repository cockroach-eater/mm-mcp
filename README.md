# mm-mcp

A Model Context Protocol (MCP) server that enables AI assistants to connect to and interact with Mattermost.

## Features

- 🔐 **Flexible Authentication**: Supports both personal access token and login/password authentication
- 🏢 **Self-Hosted Support**: Works with any Mattermost instance (cloud or self-hosted)
- 💬 **Message Management**: Read and send messages in channels
- 🔍 **Search**: Search for messages across teams
- 👥 **Team & Channel Management**: Access teams, channels, and user information
- 🤖 **AI-Ready**: Exposes Mattermost functionality as MCP tools for use with Claude and other AI assistants

## Installation

### Using uvx (Recommended)

Install directly from the latest GitHub release:

```bash
uvx --from git+https://github.com/cockroach-eater/mm-mcp.git mm-mcp
```

### Using pip

```bash
pip install git+https://github.com/cockroach-eater/mm-mcp.git
```

### From Source

```bash
git clone https://github.com/cockroach-eater/mm-mcp.git
cd mm-mcp
uv sync
```

## Configuration

### Command-Line Arguments

#### Required Arguments

You must provide a Mattermost server URL and authentication credentials.

**Mattermost Server URL:**

```bash
--url URL               # Mattermost server URL (e.g., https://mattermost.example.com)
```

**Authentication (choose one method):**

```bash
# Method 1: Personal Access Token (recommended)
--token TOKEN           # Personal access token

# Method 2: Login/Password
--login EMAIL           # Login email
--password PASSWORD     # Login password
```

#### Optional Arguments

```bash
--scheme SCHEME         # URL scheme: http or https (default: https)
--port PORT            # Server port (default: 443)
--basepath PATH        # Base path for API endpoints (default: /api/v4)
--no-verify            # Disable SSL certificate verification (for tests)
```

### Complete Examples

**With Personal Access Token (HTTPS):**

```bash
python -m mm_mcp.server \
  --url https://mattermost.example.com \
  --token xoxp-your-token-here
```

**With Login/Password:**

```bash
python -m mm_mcp.server \
  --url https://mattermost.example.com \
  --login user@example.com \
  --password your-password
```

**Self-Hosted with Custom Port:**

```bash
python -m mm_mcp.server \
  --url mattermost.internal.company.com \
  --port 8065 \
  --token xoxp-your-token-here
```

**HTTP without SSL Verification (development only):**

```bash
python -m mm_mcp.server \
  --url http://localhost \
  --port 8065 \
  --no-verify \
  --token xoxp-your-token-here
```

## Claude Desktop Configuration

Add to your Claude Desktop configuration file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`  
**Linux:** `~/.config/Claude/claude_desktop_config.json`

### Example 1: Using Token Authentication

```json
{
  "mcpServers": {
    "mattermost": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/cockroach-eater/mm-mcp.git",
        "mm-mcp",
        "--url",
        "https://mattermost.example.com",
        "--token",
        "your_personal_access_token"
      ]
    }
  }
}
```

### Example 2: Using Login/Password

```json
{
  "mcpServers": {
    "mattermost": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/cockroach-eater/mm-mcp.git",
        "mm-mcp",
        "--url",
        "https://mattermost.example.com",
        "--login",
        "user@example.com",
        "--password",
        "your-password"
      ]
    }
  }
}
```

### Example 3: Self-Hosted with Custom Port

```json
{
  "mcpServers": {
    "mattermost": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/cockroach-eater/mm-mcp.git",
        "mm-mcp",
        "--url",
        "mattermost.internal.company.com",
        "--port",
        "8065",
        "--token",
        "xoxp-your-token-here"
      ]
    }
  }
}
```

### Example 4: Development Setup (HTTP, no SSL)

```json
{
  "mcpServers": {
    "mattermost": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/cockroach-eater/mm-mcp.git",
        "mm-mcp",
        "--url",
        "http://localhost",
        "--port",
        "8065",
        "--scheme",
        "http",
        "--no-verify",
        "--token",
        "your_personal_access_token"
      ]
    }
  }
}
```

## Available Tools

The MCP server exposes the following tools that Claude can use:

### get_teams

Get all teams the authenticated user is a member of.

**Parameters:** None

**Returns:** List of teams with their IDs, names, and metadata.

### get_channels

Get all channels in a specific team.

**Parameters:**

- `team_id` (required): The ID of the team

**Returns:** List of channels in the team.

### get_channel_by_name

Get a specific channel by its name within a team.

**Parameters:**

- `team_id` (required): The ID of the team
- `channel_name` (required): The name of the channel (without #)

**Returns:** Channel information including ID and metadata.

### get_posts

Get recent posts/messages from a channel.

**Parameters:**

- `channel_id` (required): The ID of the channel
- `limit` (optional): Number of posts to retrieve (default: 20)

**Returns:** List of recent posts with content, authors, and timestamps.

### send_message

Send a message to a channel.

**Parameters:**

- `channel_id` (required): The ID of the channel
- `message` (required): The message text to send
- `reply_to` (optional): Post ID to reply to (for threaded conversations)

**Returns:** Created post information.

### search_messages

Search for messages in a team.

**Parameters:**

- `team_id` (required): The ID of the team to search in
- `query` (required): Search query string (supports `from:username` and `in:channel` syntax)

**Returns:** List of matching posts.

### get_user_info

Get information about a user.

**Parameters:**

- `user_id` (optional): The user ID (leave empty for current user)

**Returns:** User information including username, email, and roles.

## Example Interactions with Claude

Once configured, you can interact with Mattermost naturally through Claude:

**Example 1: Reading Messages**

```
You: "Show me the recent messages in the #general channel"
Claude: [Uses get_teams, get_channel_by_name, and get_posts to fetch and display messages]
```

**Example 2: Sending Messages**

```
You: "Send a message to #engineering saying 'Deployment complete'"
Claude: [Uses get_channel_by_name and send_message to post the message]
```

**Example 3: Searching**

```
You: "Search for messages about 'bug fix' in the development team"
Claude: [Uses search_messages to find relevant messages]
```

**Example 4: Team Overview**

```
You: "What teams am I part of?"
Claude: [Uses get_teams to list your teams]
```

**Example 5: Threaded Reply**

```
You: "Reply to the message about database migration saying 'I'll handle this'"
Claude: [Uses get_posts to find the message, then send_message with reply_to parameter]
```

## Obtaining a Personal Access Token

1. Log in to your Mattermost instance
2. Go to **Profile → Security → Personal Access Tokens**
3. Click **Create Token**
4. Give it a description (e.g., "Claude MCP Access")
5. Click **Save**
6. Copy the token immediately (it won't be shown again)
7. Use this token with the `--token` argument

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/cockroach-eater/mm-mcp.git
cd mm-mcp

# Install dependencies
uv sync

# Install pre-commit hooks (optional)
pre-commit install
```

### Running with MCP Inspector

The MCP Inspector allows you to test the server interactively:

```bash
# Using uv
uv run mcp dev src/mm_mcp/server.py

# Or using npx
npx @modelcontextprotocol/inspector uv run python -m mm_mcp.server \
  --url https://mattermost.example.com \
  --token your-token
```

### Running Tests

```bash
uv run pytest
```

### Code Quality Checks

```bash
# Format code
uv run ruff format

# Lint code
uv run ruff check

# Type check
uv run mypy src/mm_mcp
```

### Building

```bash
uv build
```

This creates distribution files in the `dist/` directory.

## Troubleshooting

### Authentication Errors

**Issue:** "Failed to authenticate with Mattermost"

**Solutions:**

- Verify your Mattermost URL is correct and accessible
- Check that your personal access token is valid and not expired
- Ensure your login credentials are correct
- Verify you have network access to the Mattermost server

### SSL Certificate Errors

**Issue:** SSL certificate verification fails

**Solutions:**

- For production: Ensure your server has a valid SSL certificate
- For development/testing: Use `--no-verify` flag (not recommended for production)
- For self-signed certificates: Import the certificate into your system's trust store

### Connection Issues

**Issue:** Cannot connect to Mattermost server

**Solutions:**

- Verify the URL is correct (including protocol: http/https)
- Check if the port is correct (default: 443 for HTTPS, 80 for HTTP)
- Ensure your firewall allows connections to the Mattermost server
- Test connectivity: `curl https://your-mattermost-instance.com`

### Permission Errors

**Issue:** "Not enough permissions" errors when using tools

**Solutions:**

- Verify your user account has the necessary permissions in Mattermost
- Check that your personal access token has the required scopes
- Ensure you're a member of the team/channel you're trying to access

### Session Expiry (Login/Password Mode)

**Issue:** "Session expired" errors

**Solutions:**

- The server automatically re-authenticates when sessions expire
- If re-authentication fails, check your credentials
- Consider using personal access token authentication instead

## Security Considerations

- **Never commit credentials** to version control
- **Use personal access tokens** when possible (more secure than passwords)
- **Enable SSL verification** in production (`--no-verify` should only be used for development)
- **Rotate tokens regularly** and revoke unused tokens
- **Limit token permissions** to only what's needed
- **Use environment variables** or secure secret management for credentials

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting: `uv run pytest && uv run ruff check`
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

Please ensure your PR:

- Includes tests for new functionality
- Updates documentation as needed
- Follows the existing code style
- Passes all CI checks

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with the [Model Context Protocol](https://modelcontextprotocol.io/)
- Uses the [mattermostdriver](https://github.com/Vaelor/python-mattermost-driver) Python library
- Inspired by the Mattermost and AI communities

## Support

- **Issues:** [GitHub Issues](https://github.com/cockroach-eater/mm-mcp/issues)
- **Mattermost API Docs:** [api.mattermost.com](https://api.mattermost.com/)
- **MCP Documentation:** [modelcontextprotocol.io](https://modelcontextprotocol.io/)

## Roadmap

- [ ] Support for file uploads and attachments
- [ ] Direct message support
- [ ] Emoji reactions
- [ ] Channel creation and management
- [ ] User presence/status information
- [ ] Webhooks and integrations
- [ ] Read-only mode for enhanced security
