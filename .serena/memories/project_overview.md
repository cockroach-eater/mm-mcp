# Project Overview

## Purpose
mm-mcp is a Model Context Protocol (MCP) server that enables AI assistants to connect to and interact with Mattermost. The server provides tools for reading and sending messages, managing channels, and interacting with teams on self-hosted Mattermost instances.

## Tech Stack
- **Language**: Python 3.13 (compatible with Python 3.10+)
- **Package Manager**: uv
- **MCP Framework**: Official MCP Python SDK (`mcp` package)
- **Mattermost Client**: `mattermostdriver` library
- **Version Control**: Git with GitHub flow
- **Distribution**: PyPI package installable via `uvx` or `uv pip install`

## Key Features
- Two authentication methods:
  - Personal access token authentication (recommended)
  - Login/password authentication
- Configurable Mattermost server URL via command-line arguments
- Self-hosted instance support
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
├── .gitignore               # Git ignore rules
├── src/
│   └── mm_mcp/
│       ├── __init__.py      # Package initialization
│       ├── server.py        # Main MCP server implementation
│       ├── mattermost.py    # Mattermost API wrapper
│       └── config.py        # Configuration management
└── tests/                   # Test files
```

## Configuration
The server is configured via command-line arguments (NOT environment variables):
- Mattermost server URL
- Authentication credentials (token or login/password)
- Optional: scheme, port, SSL verification

## Distribution
Users can install and activate the MCP server with:
```bash
uvx mm-mcp --url https://mattermost.example.com --token your_token
```

## Branching Strategy
Uses GitHub flow:
- `main` branch for production-ready code
- Feature branches for development
- Pull requests for code review
- Direct merges to main after approval
