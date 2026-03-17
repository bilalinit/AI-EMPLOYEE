# MCP Integration Skill: Pattern-Based Guide

> **Teaches how to design MCP tools for ANY application, not just specific use cases**

## 🎯 **What This Skill Provides**

This skill teaches **universal patterns** for building MCP servers that connect AI agents to ANY resource:
- **Databases** (PostgreSQL, MySQL, SQLite, NoSQL)
- **APIs** (REST, GraphQL, gRPC, custom services)
- **File systems** (local, cloud storage, document management)
- **External services** (email, payments, messaging, analytics)
- **Any programmatic resource** (hardware, IoT, internal tools)

## 🚀 **Core Philosophy: Patterns Over Templates**

### ❌ **What This Skill AVOIDS:**
```python
# These are USELESS for other applications
def create_item(user_id: str, name: str, description: Optional[str] = None):
    # What if app needs: create_user(email, role) or upload_file(path, metadata)?
    # What if schema is completely different?
    # What if it's not even a database operation?
```

### ✅ **What This Skill TEACHES:**
```python
# Universal patterns that work for ANY operation
"""
Pattern: Create Operation
├── Tool signature: user_id (REQUIRED) + domain parameters
├── Service layer: Your business logic
├── Error handling: {success, data/error} format
├── User isolation: Filter by user_id in service
└── Returns: Consistent structured response
"""
```

## 📚 **The 6 Universal Patterns**

Every MCP tool follows these patterns, regardless of domain:

### **Pattern 1: User Isolation**
**Rule**: All tools MUST require `user_id` from JWT
```python
# ❌ WRONG - No user isolation
@mcp.tool()
def get_data() -> dict:  # Whose data?
    return database.query("SELECT * FROM data")

# ✅ CORRECT - User isolation
@mcp.tool()
def get_data(user_id: str) -> dict:  # User from JWT
    # Your service layer filters by user_id
    return your_service.get_user_data(user_id)
```

### **Pattern 2: Structured Responses**
**Rule**: All tools return consistent format
```python
# ❌ WRONG - Inconsistent returns
@mcp.tool()
def operation():
    return {"result": "success"}  # Missing structure
    # or
    return some_object  # Agent can't parse

# ✅ CORRECT - Consistent format
@mcp.tool()
def operation() -> dict:
    try:
        result = your_logic()
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### **Pattern 3: Dynamic Server Lifecycle**
**Rule**: Create fresh server per request
```python
# ❌ WRONG - Static server (memory leaks, cross-user contamination)
server = MCPServerStdio(params={...})  # Reused
agent.mcp_servers = [server]

# ✅ CORRECT - Per-request server
async def handle_request(user_input, user_id):
    server = MCPServerStdio(params={...})  # Fresh
    try:
        await server.connect()
        result = await Runner.run(agent, user_input)
    finally:
        await server.cleanup()  # Always cleanup
```

### **Pattern 4: Context Injection**
**Rule**: Agent knows user identity
```python
# ❌ WRONG - Agent doesn't know user
result = await Runner.run(agent, user_input)

# ✅ CORRECT - Context injection
enhanced_input = f"[Authenticated as user: {user_id}] {user_input}"
result = await Runner.run(agent, enhanced_input)
```

### **Pattern 5: Error Resilience**
**Rule**: Never crash the agent
```python
# ❌ WRONG - Crashes agent
@mcp.tool()
def risky_operation():
    return external_service.call()  # What if it fails?

# ✅ CORRECT - Graceful errors
@mcp.tool()
def safe_operation():
    try:
        result = external_service.call()
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### **Pattern 6: Resource Cleanup**
**Rule**: Always cleanup in finally blocks
```python
# ❌ WRONG - No cleanup
server = MCPServerStdio(params={...})
await server.connect()
# ... use server ...
# Forgot cleanup!

# ✅ CORRECT - Always cleanup
server = MCPServerStdio(params={...})
try:
    await server.connect()
    # ... use server ...
finally:
    await server.cleanup()  # Always runs
```

## 🏗️ **Design Process: 5 Steps to Any MCP Tool**

### **Step 1: Analyze Your Resource**
Ask these questions:
1. **What resource?** (Database table, API endpoint, file system, service)
2. **What operations?** (CRUD, query, search, trigger, stream)
3. **Who uses it?** (Single user, multi-tenant, admin-only)
4. **What auth?** (JWT, API keys, OAuth, internal)
5. **What data?** (Schema, types, relationships)

**Output**: Requirements document
```markdown
## MCP Server Requirements

**Resource**: User file storage system
**Operations**: Upload, list, download, delete, share
**Users**: Multi-tenant (user isolation required)
**Auth**: JWT via Better Auth
**Data**: File metadata (id, name, size, user_id, upload_date)
```

### **Step 2: Design Tool Signatures**
**Template for ANY tool:**
```python
@mcp.tool()
def operation_name(
    user_id: str,  # REQUIRED - from JWT
    param1: type,  # Your domain parameter
    param2: Optional[type] = None,  # Optional
) -> dict:
    """
    Clear description for LLM.

    Args:
        user_id: User ID from JWT (auto-provided)
        param1: Description of this parameter
        param2: Optional parameter description

    Returns:
        dict: {"success": True, "data": {...}} or {"success": False, "error": "..."}
    """
    # Your implementation here
```

**Design checklist:**
- [ ] All tools require `user_id` first parameter
- [ ] Parameters use natural language (not technical enums)
- [ ] Return structured `{success, data/error}` format
- [ ] Include docstring with examples
- [ ] Handle all error cases

### **Step 3: Build Your Service Layer**
**Separate business logic from MCP interface:**
```python
# mcp_server.py
from mcp.server.fastmcp import FastMCP
from your_service import YourService  # Your business logic

mcp = FastMCP("YourServiceName")

def get_service():
    # Your service handles all business logic
    return YourService()

@mcp.tool()
def create_resource(user_id: str, name: str, ...) -> dict:
    """Create a new resource for the user."""
    service = get_service()
    try:
        result = service.create(user_id, name, ...)
        return {"success": True, "data": result.to_dict()}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ... more tools following same pattern
```

### **Step 4: Integrate with Agent**
**Dynamic server creation:**
```python
# agents.py
from agents import Agent, Runner
from agents.mcp import MCPServerStdio
main_agent = Agent(
    name="MainAgent",
    instructions="You have access to tools. Use them naturally.",
    model="xiami:mimo-v2-flash",
    mcp_servers=[]  # Will be populated dynamically
)

async def run_agents(user_input: str, user_id: str) -> dict:
    # Create fresh server per request
    server = MCPServerStdio(
        params={
            "command": "uv",
            "args": ["run", "mcp_server.py"]
        },
        client_session_timeout_seconds=60
    )

    main_agent.mcp_servers = [server]

    try:
        await server.connect()
        # Inject user context
        enhanced_input = f"[User: {user_id}] {user_input}"
        result = await Runner.run(main_agent, enhanced_input)

        return {
            "response": result.final_output,
            "agent_used": result.last_agent.name,
            "tools_used": [t.name for t in result.used_tools] if hasattr(result, 'used_tools') else []
        }
    finally:
        await server.cleanup()
        main_agent.mcp_servers = []
```

### **Step 5: Create FastAPI Endpoint**
**Authentication + endpoint:**
```python
# main.py
from fastapi import FastAPI, Depends, Header, HTTPException
from pydantic import BaseModel

app = FastAPI()

class ChatRequest(BaseModel):
    message: str

async def get_user_id(authorization: str = Header(...)) -> str:
    """Extract user_id from JWT token."""
    try:
        token = authorization.replace("Bearer ", "")
        payload = await verify_token(token)  # Your auth function
        return get_user_id_from_token(payload)  # Your extraction
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

@app.post("/api/agents/chat")
async def chat(request: ChatRequest, user_id: str = Depends(get_user_id)):
    """Main endpoint for agent + MCP integration."""
    result = await run_agents(request.message, user_id)
    return {"success": True, **result}
```

## 🎨 **Pattern Reference Library**

Instead of specific templates, here are **pattern categories** for common scenarios:

### **Database Operations**
```python
"""
Pattern: Database CRUD
├── Create: user_id + fields → {success, data}
├── Read: user_id + filters → {success, data}
├── Update: user_id + id + fields → {success, data}
├── Delete: user_id + id → {success, deleted}
└── Query: user_id + complex filters → {success, data}
"""
```

### **API Integration**
```python
"""
Pattern: API Integration
├── Auth: Get user credentials from user_id
├── Request: Build with user context
├── Response: Parse and structure
├── Errors: Handle network/API failures
└── Rate limiting: Respect API limits
"""
```

### **File Management**
```python
"""
Pattern: File Operations
├── Path validation: Prevent directory traversal
├── User isolation: /data/users/{user_id}/
├── Actions: list, read, write, delete
├── Security: Validate all paths
└── Cleanup: Close file handles
"""
```

### **External Services**
```python
"""
Pattern: Service Integration
├── User credentials: Store per-user config
├── Service calls: With user context
├── Result formatting: Consistent structure
├── Error handling: Service-specific errors
└── Logging: Audit trail for user actions
"""
```

## 🔐 **Security Patterns**

### **JWT Validation Flow**
```
1. User sends request with JWT
2. FastAPI extracts token from header
3. verify_token() validates with JWKS
4. get_user_id_from_token() extracts user_id
5. user_id passed to run_agents()
6. Agent injects into context
7. Tools receive user_id parameter
8. Service layer filters by user_id
```

### **Validation Layers**
```python
# Layer 1: Token validation
payload = await verify_token(token)

# Layer 2: User ID extraction
user_id = get_user_id_from_token(payload)

# Layer 3: Tool parameter
@mcp.tool()
def tool(user_id: str, ...):  # Required

# Layer 4: Database query
query.filter(Model.user_id == user_id)

# Layer 5: Path validation
if not path.startswith(user_dir):
    raise ValueError("Invalid path")
```

## 🧪 **Testing Patterns**

### **Test 1: User Isolation**
```python
async def test_isolation():
    # Create data for user 1
    await run_agents("Create resource for user 1", "user-1")

    # User 2 should not see it
    result = await run_agents("List resources", "user-2")
    assert len(result["data"]) == 0
```

### **Test 2: Error Handling**
```python
async def test_errors():
    # Invalid ID
    result = await run_agents("Get resource: invalid", "user-1")
    assert "error" in result["response"].lower()

    # Missing required field
    result = await run_agents("Create resource: ", "user-1")
    assert "error" in result["response"].lower()
```

### **Test 3: Resource Cleanup**
```python
async def test_cleanup():
    initial = len(asyncio.all_tasks())
    for _ in range(5):
        await run_agents("Create resource: test", "user-1")
    final = len(asyncio.all_tasks())
    assert final <= initial + 2  # No leaks
```

## 📊 **Architecture Overview**

```
┌─────────────────────────────────────────────────────────────┐
│                     User (Frontend)                         │
│                    JWT: Bearer <token>                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Backend (/api/agents/chat)             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  JWT Validation → Extract user_id                    │  │
│  └──────────────────────────────────────────────────────┘  │
│                       │                                     │
│                       ▼                                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Agent Manager (run_agents)                          │  │
│  │  - Creates MCP Server (per-request)                  │  │
│  │  - Injects user context                              │  │
│  └──────────────────────────────────────────────────────┘  │
│                       │                                     │
│                       ▼                                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  OpenAI Agents SDK                                   │  │
│  │  - Agent with MCP tools                              │  │
│  │  - Natural language processing                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                       │                                     │
│                       ▼                                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  MCP Server (stdio transport)                        │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │  Your Tools (following patterns)               │  │  │
│  │  │  - user_id required                            │  │  │
│  │  │  - Structured responses                        │  │  │
│  │  │  - Error handling                              │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
│                       │                                     │
│                       ▼                                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Your Service Layer                                  │  │
│  │  - Business logic                                    │  │
│  │  - User isolation (user_id filter)                  │  │
│  │  - Error handling                                   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 🎯 **When to Use This Skill**

**User says:**
- "Create an MCP tool for [your resource]"
- "How do I connect my agent to [database/API/service]?"
- "What's the pattern for [operation]?"
- "How do I handle authentication?"
- "What should my error responses look like?"

**You provide:**
1. **Pattern guidance** for their specific use case
2. **Design principles** they must follow
3. **Security patterns** they must implement
4. **Testing patterns** to verify
5. **Integration patterns** for their stack

## 📦 **Required Packages**

```toml
openai-agents>=0.6.5    # Agent SDK
fastapi>=0.128.0        # Backend
sqlmodel>=0.0.31        # ORM (if using databases)
pyjwt>=2.10.0           # JWT validation
cryptography>=44.0.0    # Crypto
asyncpg>=0.31.0         # PostgreSQL (if needed)
httpx>=0.28.1           # HTTP client
```

## 🏆 **Success Criteria**

✅ **Pattern understanding**: Agent knows the 6 universal patterns
✅ **Design process**: Can follow 5-step creation protocol
✅ **Security**: Implements all validation layers
✅ **Error handling**: Returns structured responses
✅ **User isolation**: All tools require user_id
✅ **Resource cleanup**: Always uses finally blocks
✅ **Testing**: Verifies isolation, errors, cleanup

## 📚 **Learning Path**

1. **Study**: The 6 Universal Patterns (above)
2. **Practice**: 5-Step Creation Protocol
3. **Apply**: Design tools for your specific resource
4. **Test**: Verify with the 3 test patterns
5. **Deploy**: Follow integration patterns

---

**Result**: Production-ready MCP integration for ANY resource, following universal patterns that work across all applications.

**Remember**: This skill teaches **how to think about MCP integration**, not **what to copy-paste**. Every application is different, but the patterns are universal.