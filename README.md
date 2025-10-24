# Mattermost MCP Server

<div align="center">

**Connect AI assistants to Mattermost**

An MCP server that brings Mattermost messaging capabilities to Claude, Cursor, and other AI-powered development environments.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Model Context Protocol](https://img.shields.io/badge/MCP-Server-green.svg)](https://modelcontextprotocol.io/)

</div>

---

## What is this?

**Without mm-mcp:** Manually switching between your IDE and Mattermost, losing context, breaking your flow.

**With mm-mcp:** Your AI assistant reads messages, sends updates, searches conversations—all without leaving your development environment.

## Installation

<details>
<summary><b>Claude Desktop</b></summary>

Add to your config file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**Linux:** `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "mattermost": {
      "command": "uvx",
      "args": [
        "--from", "git+https://github.com/cockroach-eater/mm-mcp.git",
        "mm-mcp",
        "--url", "https://your-mattermost.com",
        "--token", "YOUR_TOKEN"
      ]
    }
  }
}
```

**Getting a token:** Mattermost → Profile → Security → Personal Access Tokens → Create Token

Restart Claude Desktop after saving.

</details>

<details>
<summary><b>Cursor</b></summary>

**macOS/Linux:** `~/.cursor/mcp.json`
**Windows:** `%USERPROFILE%\.cursor\mcp.json`

```json
{
  "mcpServers": {
    "mattermost": {
      "command": "uvx",
      "args": [
        "--from", "git+https://github.com/cockroach-eater/mm-mcp.git",
        "mm-mcp",
        "--url", "https://your-mattermost.com",
        "--token", "YOUR_TOKEN"
      ]
    }
  }
}
```

Restart Cursor after saving.

</details>

<details>
<summary><b>Cline (VS Code)</b></summary>

1. Open Cline settings in VS Code
2. Find MCP Servers configuration
3. Add:

```json
{
  "mcpServers": {
    "mattermost": {
      "command": "uvx",
      "args": [
        "--from", "git+https://github.com/cockroach-eater/mm-mcp.git",
        "mm-mcp",
        "--url", "https://your-mattermost.com",
        "--token", "YOUR_TOKEN"
      ]
    }
  }
}
```

</details>

<details>
<summary><b>Continue (VS Code)</b></summary>

1. Open Continue extension settings
2. Navigate to MCP configuration
3. Add server configuration:

```json
{
  "mcpServers": {
    "mattermost": {
      "command": "uvx",
      "args": [
        "--from", "git+https://github.com/cockroach-eater/mm-mcp.git",
        "mm-mcp",
        "--url", "https://your-mattermost.com",
        "--token", "YOUR_TOKEN"
      ]
    }
  }
}
```

</details>

<details>
<summary><b>Zed Editor</b></summary>

Edit `~/.config/zed/settings.json`:

```json
{
  "context_servers": {
    "mattermost": {
      "command": "uvx",
      "args": [
        "--from", "git+https://github.com/cockroach-eater/mm-mcp.git",
        "mm-mcp",
        "--url", "https://your-mattermost.com",
        "--token", "YOUR_TOKEN"
      ]
    }
  }
}
```

</details>

<details>
<summary><b>Windsurf</b></summary>

Edit Windsurf config:

```json
{
  "mcp": {
    "servers": {
      "mattermost": {
        "command": "uvx",
        "args": [
          "--from", "git+https://github.com/cockroach-eater/mm-mcp.git",
          "mm-mcp",
          "--url", "https://your-mattermost.com",
          "--token", "YOUR_TOKEN"
        ]
      }
    }
  }
}
```

</details>

<details>
<summary><b>Any MCP Client</b></summary>

**Command:** `uvx`

**Arguments:**
```
--from git+https://github.com/cockroach-eater/mm-mcp.git
mm-mcp
--url https://your-mattermost.com
--token YOUR_TOKEN
```

**Optional:**
- `--port 8065` - Custom port
- `--scheme http` - Use HTTP
- `--no-verify` - Skip SSL verification (dev only)
- `--login user@example.com --password PASS` - Password auth

</details>

## Available Tools

**get_teams** - List your teams

**get_channels** - Get channels in a team

**get_posts** / **get_posts_by_name** - Fetch channel messages

**send_message** / **send_message_by_name** - Post messages or replies

**search_messages** / **search_messages_by_team_name** - Search with filters

**get_channel_by_name** - Find specific channels

**get_user_info** - Get user details

## Usage Tips

### Using by Name vs ID

Tools ending with `_by_name` are simpler - just provide team and channel names:
```
"Get posts from team 'engineering' channel 'backend'"
```

ID-based tools require you to first get IDs via `get_teams` and `get_channels`.

### Authentication

Personal access tokens are more secure than passwords. Get yours at:
**Mattermost → Profile → Security → Personal Access Tokens**

### Self-Hosted Instances

For custom ports or HTTP:
```bash
--url mattermost.company.local --port 8065 --scheme http
```

## Development

```bash
git clone https://github.com/cockroach-eater/mm-mcp.git
cd mm-mcp
uv sync

# Test with MCP Inspector
npx @modelcontextprotocol/inspector uv run python -m mm_mcp.server \
  --url https://your-mattermost.com \
  --token YOUR_TOKEN
```

## Troubleshooting

### Authentication fails
- Verify URL and token validity
- Test: `curl https://your-mattermost.com/api/v4/users/me -H "Authorization: Bearer YOUR_TOKEN"`

### SSL errors
- Production: Ensure valid certificate
- Development: Use `--no-verify` flag

### Permission errors
- Check token scopes in Mattermost
- Confirm team/channel membership

## Docker

For [Glama.ai](https://glama.ai/mcp/servers) and production deployments:

```bash
git clone https://github.com/cockroach-eater/mm-mcp.git
cd mm-mcp
cp .env.example .env
# Edit .env with your Mattermost URL and token
docker-compose up -d
```

Or use the published image:

```bash
docker run -e PYTHONUNBUFFERED=1 \
  ghcr.io/cockroach-eater/mm-mcp:latest \
  --url https://your-mattermost.com \
  --token YOUR_TOKEN
```

## License

MIT

## Links

- [MCP Documentation](https://modelcontextprotocol.io/)
- [Mattermost API](https://api.mattermost.com/)
- [Issues](https://github.com/cockroach-eater/mm-mcp/issues)
