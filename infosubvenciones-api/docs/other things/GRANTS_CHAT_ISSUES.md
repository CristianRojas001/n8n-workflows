# Grants Chat System - Issue Tracker & Action Plan

**Last Updated**: 2025-12-08
**Related Doc**: [GRANTS_CHAT_SYSTEM.md](./GRANTS_CHAT_SYSTEM.md)

---

## How to Use This Document

### Adding New Issues
1. Add issue to appropriate priority section
2. Use format: `[ISSUE-XXX] Short title`
3. Include: Description, Impact, Location, Status
4. Link to relevant code files with line numbers

### Issue Lifecycle
```
🔴 Open → 🟡 In Progress → ✅ Fixed → 🧪 Testing → ✅ Verified
```

### Priority Levels
- **P0 (Critical)**: System broken, blocks users
- **P1 (High)**: Major functionality impaired
- **P2 (Medium)**: Quality issues, minor bugs
- **P3 (Low)**: Nice to have, technical debt

---

## Latest Updates (2025-12-08)

### ✅ All P1 Search Issues Resolved!

Three high-priority search issues from holistic testing have been fixed:
- **[ISSUE-014]** Region filter returning zero results → ✅ RESOLVED
- **[ISSUE-015]** Search ranking noise → ✅ RESOLVED
- **[ISSUE-016]** Search recall failure → ✅ RESOLVED

**See**: [HOLISTIC_TESTING_ISSUES.md](./HOLISTIC_TESTING_ISSUES.md) for full details and [SESSION_2025-12-08_SEARCH_FIXES_COMPLETE.md](./SESSION_2025-12-08_SEARCH_FIXES_COMPLETE.md) for implementation report.

---

## P0 - Critical Issues (Blocks Users)

**Currently**: No P0 issues! ✅

*(Previously resolved P0 issues moved to Fixed Issues section)*

---

## P1 - High Priority Issues

**Currently**: No open P1 issues! ✅

*(All P1 issues resolved as of 2025-12-08)*

### [ISSUE-013] PostgreSQL pgvector Extension Not Installed
**Status**: ✅ RESOLVED (2025-12-08)
**Impact**: Degraded search performance, higher memory usage
**Location**: Database configuration / [search_engine.py:99-124](../ARTISTING-main/backend/apps/grants/services/search_engine.py#L99-L124)
**Reported by**: User journey testing (2025-12-08)
**Fixed by**: User - pgvector extension installed

**Description**:
The PostgreSQL database doesn't have the `pgvector` extension installed. All semantic searches fail with:
```
psycopg.errors.UndefinedObject: type "vector" does not exist
```

The system gracefully falls back to Python-based similarity search, but this has performance implications.

**Current Behavior**:
- System logs: "pgvector semantic search failed; falling back to Python implementation"
- Searches still work (fallback is functional)
- Every query generates exception traceback in logs
- Python fallback is slower and uses more memory

**Impact**:
- ⚠️ Non-blocking: System still works with fallback
- Performance: Slower search times (especially with many grants)
- Resource usage: Higher memory consumption for in-Python similarity calculations
- Logs: Cluttered with repeated error tracebacks
- Scalability: Won't scale as well as native pgvector

**Root Cause**:
PostgreSQL database missing the pgvector extension. This needs to be installed at the database level.

**Solution**:
```sql
-- Connect to PostgreSQL as superuser
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify installation
\dx vector
```

**Acceptance Criteria**:
- [ ] pgvector extension installed in PostgreSQL
- [ ] No more "type vector does not exist" errors
- [ ] Semantic search uses native pgvector implementation
- [ ] Search performance improved (measure before/after)
- [ ] Logs clean (no fallback warnings)
- [ ] Add to deployment documentation

**Workaround**: Python fallback is working, so this doesn't block users

---

## P1 - High Priority Issues

### [ISSUE-010] No API Key Validation on Startup
**Status**: 🔴 Open
**Impact**: Application starts without valid API key, fails silently at runtime
**Location**: [rag_engine_v2.py:32-35](../ARTISTING-main/backend/apps/grants/services/rag_engine_v2.py#L32-L35)
**Reported by**: Code review (2025-12-08)

**Description**:
The application configures the Gemini API key but doesn't validate it's present or valid:
```python
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
```

If the API key is missing or invalid, the application starts normally but all chat requests fail at runtime. This makes deployment issues difficult to catch.

**Impact**:
- Failed deployments aren't caught early
- No clear indication in logs that API key is missing
- Silent failures when key is present but expired
- Difficult debugging for operators

**Proposed Solution**:
```python
# On application startup (in apps.py or settings.py)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ImproperlyConfigured("GEMINI_API_KEY environment variable is required")

# Validate key is working
try:
    genai.configure(api_key=GEMINI_API_KEY)
    # Make a test call
    model = genai.GenerativeModel("gemini-2.5-flash")
    model.generate_content("test", generation_config={"max_output_tokens": 10})
    logger.info("Gemini API key validated successfully")
except Exception as e:
    raise ImproperlyConfigured(f"Invalid Gemini API key: {e}")
```

**Acceptance Criteria**:
- [ ] Application refuses to start without GEMINI_API_KEY
- [ ] API key validation on startup (test call)
- [ ] Clear error message if key is invalid
- [ ] Documented in deployment guide
- [ ] Health check endpoint includes API key status

---

### [ISSUE-011] Missing Database Null Checks in Tool Functions
**Status**: 🔴 Open
**Impact**: Potential crashes when grant data has null fields
**Location**: [rag_engine_v2.py:236-263](../ARTISTING-main/backend/apps/grants/services/rag_engine_v2.py#L236-L263)
**Reported by**: Code review (2025-12-08)

**Description**:
In `_serialize_tool_result`, the code accesses grant fields without null checks:
```python
serialized['grants_found'].append({
    'numero': grant.numero_convocatoria,  # Could be None
    'titulo': grant.titulo or 'Sin título',  # Has fallback
    'organismo': grant.organismo,  # Could be None
    'abierto': grant.abierto  # Could be None
})
```

If critical fields like `numero_convocatoria` or `organismo` are NULL in the database, this will cause serialization errors.

**Impact**:
- Tool execution failures for grants with incomplete data
- Cryptic error messages for users
- Inconsistent behavior across different grants

**Proposed Solution**:
```python
serialized['grants_found'].append({
    'numero': grant.numero_convocatoria or 'N/A',
    'titulo': grant.titulo or 'Sin título',
    'organismo': grant.organismo or 'Organismo no especificado',
    'abierto': grant.abierto if grant.abierto is not None else False
})
```

**Acceptance Criteria**:
- [ ] All grant field accesses have null/None fallbacks
- [ ] Test cases with grants that have NULL fields
- [ ] No serialization errors for incomplete data
- [ ] Graceful degradation for missing information

---

### [ISSUE-012] Conversation History Size Not Enforced Consistently
**Status**: 🔴 Open
**Impact**: Potential memory issues and context window overflow
**Location**: Multiple locations
**Reported by**: Code review (2025-12-08)

**Description**:
Conversation history limiting is inconsistent:

1. In `store_conversation_message` (line 460): Keeps last 20 messages (10 exchanges)
2. In `_build_conversation_messages` (line 171): Only sends last 10 messages

This mismatch could cause:
- Context window overflow if all 20 messages are very long
- Unexpected behavior when stored history != sent history
- No hard limit on message length

**Impact**:
- API errors from Gemini if context window exceeded
- Higher API costs from sending too much context
- Memory issues with very long conversations
- Inconsistent conversation behavior

**Proposed Solution**:
```python
# Consistent limits
MAX_HISTORY_MESSAGES = 20  # Store in cache
MAX_CONTEXT_MESSAGES = 10  # Send to Gemini
MAX_MESSAGE_LENGTH = 2000  # Truncate long messages

def _build_conversation_messages(self, history, current_query):
    messages = []

    # Take only recent history
    recent_history = history[-MAX_CONTEXT_MESSAGES:]

    for msg in recent_history:
        # Truncate very long messages
        content = msg["content"][:MAX_MESSAGE_LENGTH]
        messages.append({
            "role": msg["role"],
            "parts": [{"text": content}]
        })

    # Current query also truncated
    messages.append({
        "role": "user",
        "parts": [{"text": current_query[:MAX_MESSAGE_LENGTH]}]
    })

    return messages
```

**Acceptance Criteria**:
- [ ] Consistent history limits across codebase
- [ ] Document maximum message lengths
- [ ] Truncate very long messages gracefully
- [ ] Monitor context window usage
- [ ] Test with long conversations (20+ messages)

---

## P2 - Medium Priority Issues

### [ISSUE-003] Broad Error Handling in RAG Engine
**Status**: 🔴 Open
**Impact**: Poor error visibility, difficult debugging
**Location**: [rag_engine_v2.py:132-134](../ARTISTING-main/backend/apps/grants/services/rag_engine_v2.py#L132-L134)
**Reported by**: Gemini analysis

**Description**:
The `generate_response` method uses a generic `except Exception as e` block that catches all errors without distinguishing between:
- API errors (content safety violations, rate limits, authentication)
- Network errors (timeout, connection lost)
- Code errors (bugs in tool execution)
- Data errors (missing fields, invalid data)

This makes debugging difficult and gives users unhelpful error messages.

**Current Code**:
```python
except Exception as e:
    logger.error(f"[{response_id}] Error in smart RAG: {e}", exc_info=True)
    return self._create_error_response(response_id, str(e))
```

**Proposed Solution**:
```python
except google.api_core.exceptions.GoogleAPIError as e:
    # Handle API-specific errors (rate limits, safety, auth)
    return self._create_api_error_response(response_id, e)
except requests.exceptions.RequestException as e:
    # Handle network errors
    return self._create_network_error_response(response_id, e)
except Exception as e:
    # Unexpected errors
    logger.error(f"[{response_id}] Unexpected error: {e}", exc_info=True)
    return self._create_error_response(response_id, str(e))
```

**Acceptance Criteria**:
- [ ] Different error types return different user messages
- [ ] API rate limit errors suggest "Try again in a moment"
- [ ] Content safety errors explain why request was blocked
- [ ] Network errors suggest checking connection
- [ ] All errors logged with full context

---

### [ISSUE-004] Simplistic Function Call Parsing
**Status**: 🔴 Open
**Impact**: Tools might not execute when they should
**Location**: [rag_engine_v2.py:98-106](../ARTISTING-main/backend/apps/grants/services/rag_engine_v2.py#L98-L106)
**Reported by**: Gemini analysis

**Description**:
The code assumes a function call is always in the first part of the response:
```python
for part in response.parts:
    if hasattr(part, 'function_call') and part.function_call:
        function_call = part.function_call
        has_function_call = True
        break  # Only processes first function_call
```

If Gemini returns multiple parts (e.g., text + function_call), this might miss the function call or only process the first one.

**Proposed Solution**:
```python
# Collect all function calls and text parts
function_calls = []
text_parts = []

for part in response.parts:
    if hasattr(part, 'function_call') and part.function_call:
        function_calls.append(part.function_call)
    elif hasattr(part, 'text') and part.text:
        text_parts.append(part.text)

# Process function calls first, then text
if function_calls:
    # Execute all function calls
    # ...
elif text_parts:
    # Return direct text response
    # ...
```

**Acceptance Criteria**:
- [ ] Handles multiple function calls in one response
- [ ] Handles mixed text + function_call parts
- [ ] Logs warning if unexpected part structure detected
- [ ] Tests cover edge cases

---

### [ISSUE-005] No Recursive/Chained Tool Calls
**Status**: 🔴 Open
**Impact**: Limited agent capabilities, requires multiple user messages
**Location**: [rag_engine_v2.py:87-130](../ARTISTING-main/backend/apps/grants/services/rag_engine_v2.py#L87-L130)
**Reported by**: Gemini analysis

**Description**:
The system only supports a single tool call per user message:
1. User asks question
2. LLM calls tool
3. Tool returns results
4. LLM generates final answer

It cannot do:
- Search for grants → Get details of top result → Search for similar grants
- List recent grants → Get details of each → Compare them

**Example Scenario**:
```
User: "¿Cuál de las últimas 5 subvenciones tiene mayor cuantía?"

Current behavior:
1. LLM calls list_recent_grants() → Returns 5 grants
2. LLM responds with grant numbers but NO AMOUNTS (not in list results)
3. User must ask "Get details of each one" as separate message

Desired behavior:
1. LLM calls list_recent_grants() → Returns 5 grants
2. LLM calls get_grant_by_numero() for each → Gets amounts
3. LLM compares and responds "La subvención 870435 con 55,000€"
```

**Proposed Solution**:
Implement a tool execution loop with max iterations:
```python
MAX_TOOL_ITERATIONS = 5
iteration = 0

while iteration < MAX_TOOL_ITERATIONS:
    response = model.generate_content(messages)

    if has_function_calls(response):
        # Execute tools, add results to messages
        iteration += 1
        continue
    else:
        # No more tools needed, return final answer
        return response
```

**Acceptance Criteria**:
- [ ] Supports up to 5 chained tool calls per user message
- [ ] Prevents infinite loops
- [ ] Logs each tool execution
- [ ] Returns error if max iterations exceeded
- [ ] Test case: "Compare amounts of last 3 grants"

---

### [ISSUE-006] High Frontend Component Complexity
**Status**: 🔴 Open
**Impact**: Hard to maintain, prone to state bugs
**Location**: ChatView.tsx
**Reported by**: Gemini analysis

**Description**:
ChatView.tsx is a very large component managing many states:
- `isRunning`, `currentRun`, `plan`, `messages`, `awaitingInput`
- WebSocket connection state
- Agent protocol (plan, thought, tool_input, tool_output, input_request)
- Message history
- UI state (loading, errors)

This complexity makes it:
- Hard to debug state synchronization issues
- Difficult to add new features
- Prone to bugs where UI doesn't reflect true state

**Proposed Solution**:
Break into smaller components:
```typescript
// Main component
<ChatView>
  <ChatHeader />
  <AgentStatus status={agentState} />
  <MessageList messages={messages} />
  <ToolExecutionLog tools={executedTools} />
  <ChatInput onSend={handleSend} disabled={isRunning} />
</ChatView>

// Extract state management
const useAgentState = () => {
  // Manages agent running state, plan, tools
}

const useChatMessages = () => {
  // Manages message history
}

const useWebSocketChat = (url) => {
  // Manages WebSocket connection
}
```

**Acceptance Criteria**:
- [ ] Component split into 5-7 smaller components
- [ ] Each component has single responsibility
- [ ] State management extracted to custom hooks
- [ ] Easier to test individual pieces
- [ ] No regression in functionality

---

### [ISSUE-007] No UI Error Display
**Status**: 🔴 Open
**Impact**: Silent failures, users confused
**Location**: ChatView.tsx (WebSocket error handling)
**Reported by**: Gemini analysis

**Description**:
When WebSocket errors occur, they're only logged to console:
```typescript
onError: (error) => {
  console.error('WebSocket error:', error)
  // No user-facing error message!
}
```

Users don't see:
- Connection errors
- Backend failures
- Tool execution failures
- Rate limit errors

**Proposed Solution**:
```typescript
const [error, setError] = useState<string | null>(null)

onError: (error) => {
  console.error('WebSocket error:', error)
  setError('Error de conexión. Verifica tu internet e intenta de nuevo.')
}

// In render:
{error && (
  <ErrorBanner
    message={error}
    onDismiss={() => setError(null)}
    severity="error"
  />
)}
```

**Acceptance Criteria**:
- [ ] All WebSocket errors shown to user
- [ ] Backend error messages passed through and displayed
- [ ] Errors are dismissible
- [ ] Different error types have appropriate messages
- [ ] Error banner doesn't block chat interface

---

### [ISSUE-008] State Sync Issues on Reconnect
**Status**: 🔴 Open
**Impact**: Stale UI after network interruption
**Location**: ChatView.tsx (useWebSocket)
**Reported by**: Gemini analysis

**Description**:
If WebSocket connection drops and reconnects, there's no logic to:
- Re-sync agent state (is it still running?)
- Retrieve missed messages
- Update plan/tool execution state
- Notify user of reconnection

This can lead to:
- UI showing "Agent running" when it's actually stopped
- Missing messages from while disconnected
- User thinks system is frozen

**Proposed Solution**:
```typescript
onReconnect: async () => {
  // 1. Fetch current agent state
  const state = await api.getAgentState(sessionId)

  // 2. Fetch missed messages
  const missedMessages = await api.getMessages(sessionId, lastMessageId)

  // 3. Update UI
  setAgentState(state)
  setMessages(prev => [...prev, ...missedMessages])

  // 4. Notify user
  showNotification('Reconectado. Sincronizando...')
}
```

**Acceptance Criteria**:
- [ ] On reconnect, fetch current agent state
- [ ] Retrieve any missed messages
- [ ] Update UI to match server state
- [ ] Show reconnection notification
- [ ] Handle case where agent finished while disconnected

---

## P3 - Low Priority Issues

### [ISSUE-009] *(Placeholder - add low priority issues here)*
**Status**: 🔴 Open
**Impact**:
**Location**:
**Description**:
**Acceptance Criteria**:

---

## Fixed Issues ✅

### [ISSUE-001] Gemini API Key Expired
**Status**: ✅ Resolved (2025-12-08)
**Impact**: Complete system failure - chat feature was completely non-functional
**Location**: Environment variables / [rag_engine_v2.py:32-35](../ARTISTING-main/backend/apps/grants/services/rag_engine_v2.py#L32-L35)
**Reported by**: User journey testing (2025-12-08)
**Fixed by**: User - API key renewed

**Description**:
The Gemini API key had expired, causing all chat requests to fail with "400 API key expired" error.

**Solution**:
API key was renewed and system is now operational.

**Follow-up Actions Needed**:
- [ ] Implement ISSUE-010 (API key validation on startup)
- [ ] Add monitoring for API key expiration
- [ ] Document API key renewal process

**Verification**:
- ✅ All user journey tests passing
- ✅ Simple searches working (35 grants found for "ayudas para pymes")
- ✅ Specific grant lookups working
- ✅ Multi-turn conversations working

---

### [ISSUE-000] get_grant_by_numero uses wrong field name
**Status**: ✅ Verified (2025-12-05)
**Impact**: Users couldn't get grant details
**Location**: [chat_tools.py:110](../ARTISTING-main/backend/apps/grants/services/chat_tools.py#L110)
**Fixed by**: Claude

**Description**:
Function was trying to use non-existent ForeignKey relationship:
```python
extraction = PDFExtraction.objects.get(convocatoria=grant)  # ❌ Wrong
```

**Solution**:
```python
extraction = PDFExtraction.objects.get(convocatoria_id=grant.id)  # ✅ Fixed
```

**Tests**:
- ✅ test_grant_details.py - Passed
- ✅ test_chat_grant_details.py - Passed

---

## Backlog / Future Enhancements

### [ENHANCEMENT-001] Support voice input
**Priority**: P3
**Description**: Allow users to speak their questions
**Status**: 🔵 Backlog

### [ENHANCEMENT-002] Add grant comparison feature
**Priority**: P2
**Description**: "Compare grants 123 and 456"
**Status**: 🔵 Backlog

### [ENHANCEMENT-003] Export conversation to PDF
**Priority**: P3
**Description**: Download chat history with grant recommendations
**Status**: 🔵 Backlog

---

## Holistic Testing Issues

**Important**: 7 new issues discovered from holistic testing (search quality + data ingestion).

See detailed analysis: **[HOLISTIC_TESTING_ISSUES.md](./HOLISTIC_TESTING_ISSUES.md)**

**Quick Summary**:
- **[ISSUE-014]** Region filter broken (P1) - Returns 0 results
- **[ISSUE-015]** Search ranking noise (P1) - Irrelevant results in top 5
- **[ISSUE-016]** Recall failure (P1) - Missing known grants
- **[ISSUE-017]** Amount inconsistencies (P2) - Prose vs numeric
- **[ISSUE-018]** Procedural fields missing (P2) - Many NULLs
- **[ISSUE-019]** Title/description mismatches (P2)
- **[ISSUE-020]** Backfill incomplete (P2)

---

## Statistics

- **Total Issues**: 19
  - Chat system: 12 (ISSUE-000 through ISSUE-012)
  - Holistic testing: 7 (ISSUE-014 through ISSUE-020)
- **Critical (P0)**: 0 ✅ (ISSUE-001 resolved!)
- **High (P1)**: 6
  - Chat: ISSUE-010, ISSUE-011, ISSUE-012
  - Search: ISSUE-014, ISSUE-015, ISSUE-016
- **Medium (P2)**: 10
  - Chat: ISSUE-003 through ISSUE-008
  - Data: ISSUE-017, ISSUE-018, ISSUE-019, ISSUE-020
- **Low (P3)**: 0
- **Fixed**: 3 (ISSUE-000, ISSUE-001, ISSUE-013)
- **In Progress**: 0

**Updated**: 2025-12-08 after Phase 1 completion, live testing, and holistic testing analysis

---

## Sprint Planning

### Sprint 1: Error Handling & Stability
**Goal**: Make error cases visible and helpful
**Issues**: ISSUE-003, ISSUE-007
**Duration**: 2-3 days

### Sprint 2: Function Calling Improvements
**Goal**: Robust tool execution
**Issues**: ISSUE-004, ISSUE-005
**Duration**: 3-4 days

### Sprint 3: Frontend Refactoring
**Goal**: Maintainable UI code
**Issues**: ISSUE-006, ISSUE-008
**Duration**: 4-5 days

---

## Notes

- Always add regression tests when fixing issues
- Update this document when new issues discovered
- Link PRs to issue numbers
- Close issues only after verification in production

---

**Remember**: Issues found ≠ Issues fixed. Document first, prioritize, then execute systematically.
