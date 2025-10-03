# Recent Changes and Fixes

## Latest Bug Fix (2025-10-03)

### Issue: Session Expiry Not Retrying
**Problem**: Despite implementing retry logic, session expiry errors like "Invalid or expired session, please login again" were not triggering re-authentication.

**Root Cause**: The `mattermostdriver` library raises `NoAccessTokenProvided` exception for 401 errors (including session expiry), but we were only checking error message strings.

**Solution**: 
- Added explicit `isinstance(error, NoAccessTokenProvided)` check
- This catches the exception type directly before checking message strings
- Located in `src/mm_mcp/mattermost.py` in `_is_auth_error()` method

**Code Change**:
```python
def _is_auth_error(self, error: Exception) -> bool:
    # Check if it's the specific mattermostdriver auth exception
    if isinstance(error, NoAccessTokenProvided):
        return True
    
    # Also check error message for auth-related patterns
    error_msg = str(error).lower()
    auth_patterns = [...]
    return any(phrase in error_msg for phrase in auth_patterns)
```

**Status**: Fixed in main branch, ready for v1.2.0 release

## Auto Re-authentication Implementation

### How It Works
1. Every API call is wrapped with `_with_retry()` decorator
2. When an exception occurs, `_is_auth_error()` checks if it's auth-related
3. If auth error + password auth: calls `_authenticate()` to login again
4. Retries the original API call once
5. If retry fails, returns clear error message

### Protected Methods
All Mattermost API methods are protected:
- `get_teams()`
- `get_channels()`
- `get_channel_by_name()`
- `get_posts()`
- `create_post()` (send_message)
- `search_posts()` (search_messages)
- `get_user()`
- `get_channel_members()`

### Error Detection Patterns
- Exception type: `NoAccessTokenProvided`
- Message patterns:
  - "session is invalid"
  - "invalid or expired session"
  - "session expired"
  - "expired session"
  - "invalid session"
  - "unauthorized"
  - "401"
  - "authentication required"
  - "token expired"
  - "please login again"

## URL Parsing Fix

### Issue
The `mattermostdriver` expects hostname separately from scheme, but full URLs were being passed.

### Solution
Created `get_parsed_config()` method in `MattermostConfig`:
- Parses URL with `urlparse()`
- Extracts hostname using `parsed.hostname`
- Extracts scheme and port from URL or uses defaults
- Returns dict with separate components for driver

### Supported URL Formats
- `https://mm.example.com` → hostname: `mm.example.com`, scheme: `https`, port: `443`
- `http://mm.example.com:8065` → hostname: `mm.example.com`, scheme: `http`, port: `8065`
- `mm.example.com` → hostname: `mm.example.com`, scheme: `https`, port: `443`

## Search Messages Fix

### Issue
Error: `'Posts' object has no attribute 'search_posts'`

### Solution
Correct method name in `mattermostdriver` is `search_for_team_posts`, not `search_posts`.

Changed from:
```python
self.driver.posts.search_posts(team_id=team_id, terms=terms)
```

To:
```python
self.driver.posts.search_for_team_posts(
    team_id=team_id,
    options={
        "terms": terms,
        "is_or_search": False,
    }
)
```

## Configuration Changes

### From Environment Variables to CLI Arguments
Originally designed with env vars, changed to CLI args per MCP best practices.

**Old approach**:
```bash
export MATTERMOST_URL=https://example.com
export MATTERMOST_TOKEN=token
```

**New approach**:
```bash
mm-mcp --url https://example.com --token token
```

**Benefits**:
- More explicit configuration
- Better for MCP tool usage
- Easier to configure per instance
- No global env var pollution

### Configuration File Removed
- Deleted `.env.example` file
- Updated README with CLI args examples
- Updated Claude Desktop config examples

## Release Automation

### Scripts Created
Three Bash scripts for semantic versioning:
- `release-patch.sh` - Increments patch (1.1.1 → 1.1.2)
- `release-minor.sh` - Increments minor, resets patch (1.1.5 → 1.2.0)
- `release-major.sh` - Increments major, resets minor and patch (1.5.3 → 2.0.0)

### Each Script:
1. Reads current version from `pyproject.toml`
2. Calculates new version
3. Shows version change and asks for confirmation
4. Updates `pyproject.toml` and `src/mm_mcp/__init__.py`
5. Commits changes
6. Creates annotated git tag
7. Pushes to GitHub (triggers Actions)

### GitHub Actions Workflow
- Triggers on tags matching `v*`
- Builds with `uv build`
- Creates GitHub release
- Attaches `.whl` and `.tar.gz` files
- Generates release notes automatically

## Dependencies
All pinned in `pyproject.toml`:
- `mcp>=1.2.0` - Official MCP SDK
- `mattermostdriver>=7.3.0` - Mattermost API client
- `pydantic>=2.0.0` - Config validation

Dev dependencies:
- `pytest>=7.0.0`
- `pytest-asyncio>=0.21.0`
- `ruff>=0.1.0` - Linting and formatting
- `mypy>=1.0.0` - Type checking
- `mcp-cli>=0.1.0` - MCP testing tools
