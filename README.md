# mm-mcp

A Model Context Protocol (MCP) server that enables AI assistants to connect to and interact with Mattermost.

## Features

- 🔐 **Flexible Authentication**: Supports both personal access token and login/password authentication
- 🏢 **Self-Hosted Support**: Configurable Mattermost server URL for self-hosted instances
- 💬 **Message Management**: Read and send messages in channels
- 🔍 **Search**: Search for messages across teams
- 👥 **Team & Channel Management**: Access teams, channels, and user information
- 🤖 **AI-Ready**: Exposes Mattermost functionality as MCP tools for use with Claude and other AI assistants

## Installation

### From GitHub Release (Recommended)

Download the latest `.whl` file from [Releases](https://github.com/cockroach-eater/mm-mcp/releases) and install:

```bash
uvx --from /path/to/mm_mcp-0.1.0-py3-none-any.whl mm-mcp
```

Or install directly from the latest release:

```bash
uvx --from https://github.com/cockroach-eater/mm-mcp/releases/latest/download/mm_mcp-0.1.0-py3-none-any.whl mm-mcp
```

### From GitHub Repository

Install directly from the main branch:

```bash
uvx --from git+https://github.com/cockroach-eater/mm-mcp.git mm-mcp
```

Or with pip:

```bash
pip install git+https://github.com/cockroach-eater/mm-mcp.git
```

### From Source

```bash
git clone https://github.com/cockroach-eater/mm-mcp.git
cd mm-mcp
uv sync
uv run python -m mm_mcp.server --url https://your-mattermost.com --token your_token
```

## Configuration

The server is configured using command-line arguments when running the MCP server.

### Required Arguments

**Mattermost Server URL:**
```bash
--url https://your-mattermost-instance.com
```

**Authentication (choose one):**

Option 1 - Personal Access Token (recommended):
```bash
--token your_personal_access_token
```

Option 2 - Login/Password:
```bash
--login your_email@example.com --password your_password
```

### Optional Arguments

```bash
--scheme https          # URL scheme (default: https)
--port 443              # Server port (default: 443)
--no-verify             # Disable SSL certificate verification (not recommended)
```

## Usage

### With Claude Desktop

Add to your Claude Desktop configuration file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

**Using GitHub Repository:**

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
        "https://your-mattermost-instance.com",
        "--token",
        "your_personal_access_token"
      ]
    }
  }
}
```

**Using Login/Password Authentication:**

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
        "https://your-mattermost-instance.com",
        "--login",
        "your.email@example.com",
        "--password",
        "your_password"
      ]
    }
  }
}
```

**Using GitHub Release (after v0.1.0 is released):**

```json
{
  "mcpServers": {
    "mattermost": {
      "command": "uvx",
      "args": [
        "--from",
        "https://github.com/cockroach-eater/mm-mcp/releases/latest/download/mm_mcp-0.1.0-py3-none-any.whl",
        "mm-mcp",
        "--url",
        "https://your-mattermost-instance.com",
        "--token",
        "your_personal_access_token"
      ]
    }
  }
}
```

### Development Mode

```bash
# Install dependencies
uv sync

# Run in development mode with MCP Inspector
uv run mcp dev src/mm_mcp/server.py

# Or use the MCP Inspector
npx @modelcontextprotocol/inspector uv run src/mm_mcp/server.py
```

## Available Tools

The MCP server exposes the following tools:

- **get_teams**: Get all teams the authenticated user is a member of
- **get_channels**: Get all channels in a specific team
- **get_posts**: Get recent posts from a channel
- **send_message**: Send a message to a channel
- **search_messages**: Search for messages in a team
- **get_channel_by_name**: Get a channel by its name in a team
- **get_user_info**: Get information about a user

## Example Interactions

Once configured with Claude, you can interact with Mattermost naturally:

```
You: "Show me the recent messages in the #general channel"
Claude: [Uses get_teams, get_channel_by_name, and get_posts to fetch and display messages]

You: "Send a message to #engineering saying 'Deployment complete'"
Claude: [Uses get_channel_by_name and send_message to post the message]

You: "Search for messages about 'bug fix' in the development team"
Claude: [Uses search_messages to find relevant messages]
```

## Obtaining a Personal Access Token

1. Log in to your Mattermost instance
2. Go to **Profile → Security → Personal Access Tokens**
3. Click **Create Token**
4. Give it a description and click **Save**
5. Copy the token immediately (it won't be shown again)
6. Use this token in your `MATTERMOST_TOKEN` environment variable

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/cockroach-eater/mm-mcp.git
cd mm-mcp

# Install dependencies
uv sync

# Install pre-commit hooks (optional)
pre-commit install
```

### Running Tests

```bash
uv run pytest
```

### Code Quality

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

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes
4. Run tests and linting
5. Commit your changes (`git commit -m 'Add some feature'`)
6. Push to the branch (`git push origin feature/your-feature`)
7. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) file for details

## Troubleshooting

### Authentication Errors

- Verify your Mattermost URL is correct and accessible
- Check that your token or credentials are valid
- For self-signed certificates, set `MATTERMOST_VERIFY=false` (not recommended for production)

### Connection Issues

- Ensure your Mattermost instance is accessible from your network
- Check firewall settings if using a self-hosted instance
- Verify the port number matches your Mattermost configuration

### Tool Errors

- Make sure you have the necessary permissions in Mattermost
- Check that team IDs and channel IDs are correct
- Review the error messages for specific issues

## Support

For issues and questions:
- Open an issue on [GitHub](https://github.com/cockroach-eater/mm-mcp/issues)
- Check existing issues for solutions
- Review the [Mattermost API documentation](https://api.mattermost.com/)

## Acknowledgments

- Built with the [Model Context Protocol](https://modelcontextprotocol.io/)
- Uses the [mattermostdriver](https://github.com/Vaelor/python-mattermost-driver) Python library
- Inspired by the Mattermost and AI communities
