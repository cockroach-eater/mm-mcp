# Suggested Commands

## Development Commands
- Install dependencies: `uv sync`
- Run MCP server: `uv run python -m mm_mcp.server --url URL --token TOKEN`
- Run in dev mode: `uv run mcp dev src/mm_mcp/server.py`
- Install server locally: `uv run mcp install src/mm_mcp/server.py`
- Run tests: `uv run pytest`
- Format code: `uv run ruff format`
- Lint code: `uv run ruff check`
- Type check: `uv run mypy src/mm_mcp`

## Building and Distribution
- Build package: `uv build`
- Publish to PyPI: `uv publish`
- Test installation: `uvx mm-mcp --url https://example.com --token test`

## GitHub Flow Commands
- Create feature branch: `git checkout -b feature/feature-name`
- Push feature: `git push -u origin feature/feature-name`
- Create PR: `gh pr create` (or via GitHub web interface)
- Merge to main: Merge pull request on GitHub
- Create release: `gh release create v0.1.0`
- Tag release: `git tag -a v0.1.0 -m "Release v0.1.0"`

## Git Commands
- Check status: `git status`
- Stage changes: `git add <file>` or `git add -A`
- Commit: `git commit -m "message"`
- Push: `git push`
- Pull: `git pull`
- Switch branches: `git checkout branch-name`

## Testing MCP Server
- Use MCP Inspector: `npx @modelcontextprotocol/inspector uv run python -m mm_mcp.server --url URL --token TOKEN`
- Test in Claude Desktop: Configure in Claude Desktop settings with args

## macOS System Commands
- List files: `ls` or `ls -la`
- Find files: `find . -name "*.py"`
- Search content: `grep -r "pattern" .`
- Change directory: `cd <path>`
