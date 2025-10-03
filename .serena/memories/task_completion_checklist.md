# Task Completion Checklist

When completing a task, ensure the following steps are done:

## Code Quality
- [ ] Code follows PEP 8 and project style conventions
- [ ] All functions have type hints
- [ ] All public functions/classes have docstrings (Google style)
- [ ] Code is formatted with Ruff: `uv run ruff format`
- [ ] Code passes linting: `uv run ruff check`
- [ ] Type checking passes: `uv run mypy src/mm_mcp`

## Testing
- [ ] Unit tests written for new functionality
- [ ] All tests pass: `uv run pytest`
- [ ] MCP server tested with Inspector or Claude Desktop
- [ ] Manual testing of Mattermost integration completed

## Documentation
- [ ] README.md updated if functionality changes
- [ ] Docstrings added for new functions/classes
- [ ] Comments added for complex logic
- [ ] Configuration examples updated if needed

## Version Control
- [ ] Changes committed with descriptive messages
- [ ] Working on appropriate feature branch
- [ ] Branch is up to date with main
- [ ] Ready to create/update pull request

## MCP-Specific
- [ ] Tool descriptions are clear and helpful
- [ ] Error handling provides meaningful messages
- [ ] Authentication is properly handled
- [ ] Configuration is documented

## Before Release
- [ ] Version number updated in pyproject.toml
- [ ] CHANGELOG updated
- [ ] Build succeeds: `uv build`
- [ ] Package can be installed: `uvx mm-mcp`
- [ ] Release notes prepared
