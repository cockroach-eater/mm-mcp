# Code Style and Conventions

## General Guidelines
- Follow PEP 8 style guide for Python code
- Use Ruff for linting and formatting
- Use type hints throughout the codebase
- Write docstrings for all public functions, classes, and methods
- Keep functions focused and modular

## Naming Conventions
- Variables and functions: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private methods/attributes: `_leading_underscore`
- Module names: `lowercase` or `snake_case`

## Type Hints
- Use modern Python 3.13 type syntax
- Import from `typing` when needed
- Use `Optional[T]` for nullable types
- Use `list[T]`, `dict[K, V]` (lowercase built-ins)

## Code Organization
- Use `src/` layout for packages
- One class per file for major components
- Group related functionality in modules
- Keep MCP server logic separate from Mattermost API logic

## Documentation
- Docstrings in Google style format
- Include type information in docstrings if not obvious from hints
- Add inline comments for complex logic
- Keep README.md up to date with setup and usage instructions

## MCP-Specific Conventions
- Use FastMCP or official MCP SDK patterns
- Leverage decorators for tool definitions
- Use docstrings to generate tool descriptions automatically
- Handle errors gracefully and return meaningful messages

## Testing
- Write tests for all public functions
- Use pytest for testing
- Mock external API calls (Mattermost)
- Aim for high test coverage

## Git Conventions
- Follow GitHub flow branching model
- Main branch: `main` (production-ready code)
- Feature branches: `feature/<feature-name>`
- Bug fix branches: `fix/<bug-name>`
- Use descriptive commit messages
- Squash commits when merging PRs
