# Token Optimization Enhancements Plan

## Problem Analysis

### Current Token Inefficiencies

1. **User ID Resolution in Posts**
   - `get_posts` returns only `user_id` field
   - AI must make separate `get_user_info(user_id)` calls for each unique user
   - Example: 20 posts with 5 unique users = 1 + 5 = 6 API calls
   
2. **Channel ID Resolution in Search**
   - `search_messages` returns `user_id` and `channel_id`
   - AI needs 2 additional calls per unique user/channel combination
   - Example: 10 search results = 1 + up to 20 lookups
   
3. **Team/Channel Name Lookups**
   - AI must first call `get_teams` to get team ID
   - Then call `get_channel_by_name(team_id, channel_name)`
   - Simple task requires 2 API calls minimum
   
4. **Repeated Data Fetching**
   - No caching mechanism for user/team/channel data
   - Same data fetched multiple times across interactions
   - High token overhead for repeated lookups

## Proposed Enhancements

### Phase 1: Data Enrichment (High Priority)

#### 1.1 Enhanced `get_posts` Tool
**Current behavior:**
```json
{
  "id": "post123",
  "user_id": "user456",
  "message": "Hello world",
  "create_at": 1234567890
}
```

**Enhanced behavior:**
```json
{
  "id": "post123",
  "user_id": "user456",
  "username": "john.doe",
  "user_display_name": "John Doe",
  "message": "Hello world",
  "create_at": 1234567890,
  "create_at_formatted": "2024-10-04 10:30:00"
}
```

**Implementation:**
- Collect unique `user_id` values from posts
- Batch fetch user info for all unique users
- Enrich post objects with user data
- Add formatted timestamp for readability

**Token savings:** ~70% reduction (from 6 calls to 2 calls for typical use case)

#### 1.2 Enhanced `search_messages` Tool
**Current behavior:**
```json
{
  "id": "post123",
  "user_id": "user456",
  "channel_id": "chan789",
  "message": "bug fix",
  "create_at": 1234567890
}
```

**Enhanced behavior:**
```json
{
  "id": "post123",
  "user_id": "user456",
  "username": "john.doe",
  "user_display_name": "John Doe",
  "channel_id": "chan789",
  "channel_name": "engineering",
  "channel_display_name": "Engineering Team",
  "message": "bug fix",
  "create_at": 1234567890,
  "create_at_formatted": "2024-10-04 10:30:00"
}
```

**Implementation:**
- Batch fetch user info for unique users
- Batch fetch channel info for unique channels
- Enrich results with both user and channel data

**Token savings:** ~80% reduction (from up to 21 calls to 3 calls)

### Phase 2: Name-Based Interface (Medium Priority)

#### 2.1 New Tool: `get_posts_by_channel_name`
**Interface:**
```python
get_posts_by_channel_name(
    team_name: str,        # Accept team name instead of ID
    channel_name: str,     # Accept channel name instead of ID
    limit: int = 20
) -> list[EnrichedPost]
```

**Implementation:**
- Internal: resolve team name → team ID (with caching)
- Internal: resolve channel name → channel ID (with caching)
- Call existing get_posts logic with enrichment
- Return enriched posts

**Benefit:** AI can directly use "engineering" instead of needing team/channel IDs

#### 2.2 New Tool: `send_message_by_channel_name`
**Interface:**
```python
send_message_by_channel_name(
    team_name: str,
    channel_name: str,
    message: str,
    reply_to: str | None = None
) -> dict
```

**Implementation:**
- Resolve team and channel names to IDs
- Call existing send_message logic
- Return success with channel context

**Benefit:** Simpler AI interaction, no ID lookups needed

#### 2.3 Enhanced `search_messages` - Accept Team Name
**Current:**
```python
search_messages(team_id: str, query: str)
```

**Enhanced:**
```python
search_messages(
    team_name: str,  # Changed from team_id
    query: str
) -> list[EnrichedSearchResult]
```

**Implementation:**
- Resolve team_name → team_id internally
- Apply existing enrichment logic
- Cache team name mappings

### Phase 3: Caching Layer (Medium Priority)

#### 3.1 In-Memory Cache
**Cache entries:**
- Team ID ↔ Team Name mappings
- Channel ID ↔ Channel Name mappings (per team)
- User ID → User info
- Cache TTL: 5 minutes (configurable)

**Implementation:**
```python
class CacheManager:
    def __init__(self, ttl: int = 300):
        self.teams: dict[str, dict] = {}
        self.channels: dict[str, dict] = {}
        self.users: dict[str, dict] = {}
        self.timestamps: dict[str, float] = {}
```

**Benefits:**
- Eliminates repeated API calls within same session
- Reduces token usage for AI follow-up queries
- Faster response times

#### 3.2 Batch Fetching Utilities
**Helper functions:**
```python
def batch_get_users(user_ids: list[str]) -> dict[str, dict]:
    """Fetch multiple users with caching."""
    
def batch_get_channels(channel_ids: list[str], team_id: str) -> dict[str, dict]:
    """Fetch multiple channels with caching."""
```

### Phase 4: Advanced Features (Lower Priority)

#### 4.1 Tool: `get_conversation_context`
Get full context for a conversation thread including all user info.

**Interface:**
```python
get_conversation_context(
    team_name: str,
    channel_name: str,
    limit: int = 50
) -> dict
```

**Returns:**
```json
{
  "team": {"id": "...", "name": "...", "display_name": "..."},
  "channel": {"id": "...", "name": "...", "display_name": "..."},
  "participants": [
    {"id": "...", "username": "...", "display_name": "..."}
  ],
  "posts": [
    {...enriched posts with full user data...}
  ]
}
```

**Benefit:** Single call provides complete conversation context

#### 4.2 Tool: `get_channel_summary`
Get overview of a channel with recent activity.

**Interface:**
```python
get_channel_summary(
    team_name: str,
    channel_name: str
) -> dict
```

**Returns:**
```json
{
  "channel": {...},
  "member_count": 15,
  "recent_posts_count": 42,
  "top_participants": ["user1", "user2", "user3"],
  "recent_posts": [...enriched posts...]
}
```

#### 4.3 Tool: `list_all_channels`
Get all accessible channels across all teams with team context.

**Interface:**
```python
list_all_channels() -> dict
```

**Returns:**
```json
{
  "teams": [
    {
      "id": "...",
      "name": "engineering",
      "display_name": "Engineering",
      "channels": [
        {"id": "...", "name": "general", "display_name": "General", "type": "O"}
      ]
    }
  ]
}
```

**Benefit:** Single call gives complete workspace structure

## Implementation Priority

### High Priority (Immediate Impact)
1. Enhanced `get_posts` with user enrichment
2. Enhanced `search_messages` with user + channel enrichment
3. Basic caching for users

### Medium Priority (Next Phase)
4. Name-based interface for common operations
5. Full caching layer with TTL
6. Batch fetching utilities

### Lower Priority (Future Enhancement)
7. Advanced context tools
8. Summary and aggregation tools
9. Workspace overview tools

## Expected Token Savings

### Typical Use Cases
1. **"Show me messages in #general"**
   - Current: 3 calls (get_teams, get_channel_by_name, get_posts) + N user lookups
   - Enhanced: 2 calls (enriched get_posts_by_channel_name)
   - Savings: ~70-80%

2. **"Search for 'deployment' mentions"**
   - Current: 1 + N user lookups + M channel lookups
   - Enhanced: 1 enriched call
   - Savings: ~80-90%

3. **"Send message to #engineering"**
   - Current: 2-3 calls (get_teams, get_channel_by_name, send_message)
   - Enhanced: 1 call (send_message_by_channel_name)
   - Savings: ~60%

## Implementation Notes

### Backward Compatibility
- Keep existing ID-based tools for backward compatibility
- Add new name-based tools alongside existing ones
- Mark ID-based tools as "advanced" or "legacy" in documentation

### Error Handling
- Handle ambiguous team/channel names gracefully
- Provide clear error messages with suggestions
- Cache negative lookups to avoid repeated failures

### Testing Strategy
- Unit tests for cache functionality
- Integration tests for enrichment logic
- Performance tests for batch operations
- Token usage comparison tests

## Configuration Options

Add optional settings:
```python
--enable-enrichment     # Enable data enrichment (default: true)
--cache-ttl SECONDS     # Cache TTL in seconds (default: 300)
--batch-size N          # Batch fetch size (default: 50)
```

## Metrics to Track

After implementation:
1. Average API calls per AI interaction
2. Token usage reduction percentage
3. Cache hit rate
4. Response time improvements
