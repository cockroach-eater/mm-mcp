# Reconnection Diagnostic Guide

## If Disconnection Still Happens Every Second Try

### Diagnosis Steps

1. **Check stderr output** - The server now logs errors to stderr:
   ```
   [mm-mcp] Authentication error detected: <type>: <message>
   [mm-mcp] Tool error: <type>: <message>
   ```

2. **Look for specific error patterns**:
   - "Token authentication failed" → Invalid token
   - "session expired" → Session timeout (password auth)
   - "401" or "unauthorized" → Authentication failure
   - Other errors → Network/API issues

### Recent Fixes Applied

**1. Added Token Validation (src/mm_mcp/mattermost.py:44-67)**
   - Now tests token with actual API call during `_authenticate()`
   - Previously just set `_authenticated = True` without testing
   - This catches invalid tokens immediately

**2. Improved Error Detection (src/mm_mcp/server.py:426-458)**
   - More specific auth error patterns
   - Added logging to stderr for debugging
   - Only resets client on actual auth errors

**3. Client Cleanup (src/mm_mcp/server.py:28-38)**
   - Proper disconnect on shutdown
   - Prevents stale connections

### Common Causes

**A. Token Issues**
- **Symptom:** First call fails, second succeeds
- **Cause:** Token not properly set or invalid format
- **Solution:** Verify token in config, regenerate if needed

**B. Network/DNS Issues**
- **Symptom:** Intermittent failures
- **Cause:** DNS resolution delay or network timeout
- **Solution:** Check network connectivity, try with IP address

**C. Rate Limiting**
- **Symptom:** Every other request fails
- **Cause:** Mattermost rate limiting
- **Solution:** Check Mattermost rate limit settings

**D. Server-Side Session Management**
- **Symptom:** Pattern of fail-success-fail-success
- **Cause:** Server creating/destroying sessions incorrectly
- **Solution:** Check Mattermost server logs

### Debugging Commands

**1. Check if error is being logged:**
```bash
# Run your MCP server and check stderr
# Look for lines starting with [mm-mcp]
```

**2. Test connection directly:**
```bash
# Use curl to test your Mattermost connection
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://your-mattermost.com/api/v4/users/me
```

**3. Monitor server logs:**
```bash
# Check Mattermost server logs for errors
# Look for authentication or rate limit messages
```

### Configuration Check

**Verify your Claude Desktop config:**
```json
{
  "mcpServers": {
    "mattermost": {
      "command": "uvx",
      "args": [
        "--from", "git+https://github.com/cockroach-eater/mm-mcp.git",
        "mm-mcp",
        "--url", "https://your-mattermost.com",
        "--token", "your-actual-token-here"  ← Check this!
      ]
    }
  }
}
```

### What to Look For in stderr

**Good (working):**
```
[No errors - silence is golden]
```

**Authentication Issue:**
```
[mm-mcp] Authentication error detected: Exception: Token authentication failed: ...
```

**Network Issue:**
```
[mm-mcp] Tool error: ConnectionError: Failed to connect to ...
```

**Rate Limiting:**
```
[mm-mcp] Tool error: HTTPError: 429 Too Many Requests
```

### If Problem Persists

1. **Collect information:**
   - Error messages from stderr
   - Pattern of failures (every N requests?)
   - Which tool calls fail vs succeed
   - Timestamp of failures

2. **Try these tests:**
   ```bash
   # Test 1: Direct API call
   curl -H "Authorization: Bearer TOKEN" \
     https://your-mattermost.com/api/v4/users/me

   # Test 2: Multiple rapid calls
   for i in {1..5}; do
     curl -H "Authorization: Bearer TOKEN" \
       https://your-mattermost.com/api/v4/users/me
   done

   # Test 3: Check rate limits
   curl -I -H "Authorization: Bearer TOKEN" \
     https://your-mattermost.com/api/v4/users/me
   # Look for X-RateLimit-* headers
   ```

3. **Check Mattermost server:**
   - Server version (older versions have different auth behavior)
   - Rate limit settings
   - Session timeout settings
   - Any proxy/load balancer in front

### Expected Behavior After Fix

**Scenario 1: Valid Token**
```
Request 1: Create client → Test auth → Success
Request 2: Reuse client → Success
Request 3: Reuse client → Success
...
```

**Scenario 2: Invalid Token**
```
Request 1: Create client → Test auth → FAIL (logged to stderr)
           → Client reset to None
Request 2: Create client → Test auth → FAIL (if token still invalid)
           → OR Success (if token was fixed)
```

**Scenario 3: Session Expiry (password auth)**
```
Request 1-10: Working fine
Request 11: Session expired → Detected → Client reset
Request 12: Auto-reconnect → Success
```

### Code Changes Reference

**File: src/mm_mcp/mattermost.py**
- Line 44-67: Enhanced `_authenticate()` with token testing

**File: src/mm_mcp/server.py**
- Line 28-38: Added `cleanup_client()`
- Line 40-58: Enhanced `get_client()` with error recovery
- Line 426-458: Improved error detection and logging

### Still Not Working?

If you still see "disconnects every second try" after these fixes:

1. **Enable verbose logging** - Check stderr for `[mm-mcp]` messages
2. **Test with curl** - Verify token works outside of MCP
3. **Check server logs** - Look for rate limiting or auth issues
4. **Try different timing** - Add small delay between requests
5. **Report issue** - Include stderr logs and error patterns

The issue should be resolved, but if not, the logging will reveal the actual cause.
