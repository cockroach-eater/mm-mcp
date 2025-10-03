# Suggested Commands

## Development Commands
- Install dependencies: `uv sync`
- Run MCP server in dev mode: `uv run mcp dev src/mm_mcp/server.py`
- Install server locally: `uv run mcp install src/mm_mcp/server.py`
- Run tests: `uv run pytest`
- Format code: `uv run ruff format`
- Lint code: `uv run ruff check`
- Type check: `uv run mypy src/mm_mcp`

## Building and Distribution
- Build package: `uv build`
- Publish to PyPI: `uv publish`
- Test installation: `uvx mm-mcp`

## GitHub Flow Commands
- Create feature branch: `git checkout -b feature/feature-name`
- Push feature: `git push -u origin feature/feature-name`
- Create PR: `gh pr create`
- Merge to main: `gh pr merge`
- Create release: `gh release create v0.1.0`

## Git Commands
- Check status: `git status`
- Stage changes: `git add <file>` or `git add -A`
- Commit: `git commit -m "message"`
- Push: `git push`
- Pull: `git pull`

## Testing MCP Server
- Use MCP Inspector: `npx @modelcontextprotocol/inspector uv run src/mm_mcp/server.py`
- Test in Claude Desktop: Configure in Claude Desktop settings

## macOS System Commands
- List files: `ls` or `ls -la`
- Find files: `find . -name "*.py"`
- Search content: `grep -r "pattern" .`
- Change directory: `cd <path>`
