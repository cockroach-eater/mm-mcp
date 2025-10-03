# Project Overview

## Purpose
mm-mcp is a Model Context Protocol (MCP) server that enables AI assistants to connect to and interact with Mattermost. The server provides tools for reading and sending messages, managing channels, and interacting with teams on self-hosted Mattermost instances.

## Tech Stack
- **Language**: Python 3.13
- **Package Manager**: uv
- **MCP Framework**: Official MCP Python SDK (`mcp` package)
- **Mattermost Client**: `mattermostdriver` library
- **Version Control**: Git with GitHub flow
- **Distribution**: PyPI package installable via `uvx` or `uv pip install`

## Key Features
- Two authentication methods:
  - Login/password authentication
  - Personal access token authentication
- Configurable Mattermost server URL (for self-hosted instances)
- MCP tools for:
  - Reading messages and channels
  - Sending messages
  - Managing channels and teams
  - User interactions

## Project Structure
```
mm-mcp/
├── .python-version          # Python version specification (3.13)
├── pyproject.toml           # Project configuration and dependencies
├── README.md                # Project documentation
├── src/
│   └── mm_mcp/
│       ├── __init__.py      # Package initialization
│       ├── server.py        # Main MCP server implementation
│       ├── mattermost.py    # Mattermost API wrapper
│       └── config.py        # Configuration management
└── tests/                   # Test files
```

## Distribution
Users can install and activate the MCP server with:
```bash
uvx mm-mcp
# or
uv pip install mm-mcp
```

Configuration is provided via environment variables or config file for:
- Mattermost server URL
- Authentication credentials (token or login/password)
