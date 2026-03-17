# MCP Integration Core Principles

## 🎯 **The 6 Universal Pillars of MCP Integration**

These principles work for **ANY** resource type - databases, APIs, file systems, external services, hardware, or internal tools.

### 1. **Dynamic Server Lifecycle**
**Principle**: MCP servers must be created per-request, not static.

**Why Universal**:
- **Resource agnostic**: Works for ANY resource type
- **State isolation**: Clean slate for every request
- **Security**: Prevents cross-user contamination
- **Memory management**: No leaks regardless of resource

**Universal Pattern**:
```python
# ❌ WRONG - Static server (breaks with ANY resource)
static_server = MCPServerStdio(params={...})
agent.mcp_servers = [static_server]  # Reused across requests

# ✅ CORRECT - Dynamic server (works with ANY resource)
async def handle_any_request(user_input: str, user_id: str) -> dict:
    server = MCPServerStdio(
        params={
            "command": "uv",
            "args": ["run", "mcp_server.py"]  # Your server file
        }
    )
    agent.mcp_servers = [server]
    try:
        await server.connect()
        enhanced_input = f"[User: {user_id}] {user_input}"
        result = await Runner.run(agent, enhanced_input)
        return {"response": result.final_output}
    finally:
        await server.cleanup()
        agent.mcp_servers = []
```

### 2. **User Isolation**
**Principle**: All tools MUST require user_id parameter from JWT.

**Why Universal**:
- **Security**: Prevents data access across users for ANY resource
- **Compliance**: Required for GDPR, HIPAA, etc. regardless of resource
- **Accountability**: All actions traceable to user
- **Multi-tenancy**: Single resource serves multiple users

**Universal Pattern**:
```python
# ❌ WRONG - No user isolation (dangerous for ANY resource)
@mcp.tool()
def list_resources() -> dict:  # Which user's resources?
    return session.query(Model).all()  # or API call, or file list

# ✅ CORRECT - User isolation (works for ANY resource)
@mcp.tool()
def list_resources(user_id: str) -> dict:  # User from JWT
    """
    List resources for the authenticated user.
    Works for: Database queries, API calls, file operations, etc.
    """
    service = get_service()
    return service.list(user_id=user_id)  # Filters by user internally
```

### 3. **Structured Responses**
**Principle**: All tools return consistent dict format.

**Why Universal**:
- **Consistency**: Agent knows what to expect from ANY resource
- **Error handling**: Graceful failures for ANY operation
- **Frontend parsing**: Uniform handling of ANY resource response
- **Retry logic**: Can attempt ANY operation again

**Universal Pattern**:
```python
# ❌ WRONG - Inconsistent returns (breaks agent for ANY resource)
@mcp.tool()
def tool1(): return "success"  # Database result
@mcp.tool()
def tool2(): return {"data": "..."}  # API result
@mcp.tool()
def tool3(): raise Exception("error")  # File operation fails

# ✅ CORRECT - Consistent format (works for ANY resource)
@mcp.tool()
def universal_operation(user_id: str, operation: str, **params) -> dict:
    """
    Works for ANY resource type with consistent response.
    """
    try:
        service = get_service()
        result = service.execute(user_id, operation, **params)
        return {
            "success": True,
            "data": result,
            "count": len(result) if isinstance(result, list) else None
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### 4. **Context Injection**
**Principle**: User context must be injected into agent input.

**Why Universal**:
- **Automatic authentication**: Agent knows user_id for ANY resource
- **Natural flow**: No "What's your user ID?" questions
- **Security**: Context-based access control for ANY resource
- **Universal compatibility**: Works with ANY authentication system

**Universal Pattern**:
```python
# ❌ WRONG - Agent doesn't know user (breaks with ANY resource)
result = await Runner.run(agent, user_input)

# ✅ CORRECT - Inject user context (works for ANY resource)
async def run_agents(user_input: str, user_id: str) -> dict:
    """
    Universal agent runner that works with ANY resource type.
    """
    server = MCPServerStdio(params={"command": "uv", "args": ["run", "mcp_server.py"]})
    try:
        await server.connect()
        agent.mcp_servers = [server]

        # Inject context for ANY resource
        enhanced_input = f"[Authenticated as user: {user_id}] {user_input}"
        result = await Runner.run(agent, enhanced_input)

        return {"response": result.final_output}
    finally:
        await server.cleanup()
        agent.mcp_servers = []
```

### 5. **Resource Cleanup**
**Principle**: Always cleanup resources in finally blocks.

**Why Universal**:
- **Memory management**: No leaks for ANY resource type
- **Connection handling**: Proper cleanup for databases, APIs, files
- **Process management**: Stops hanging processes for ANY resource
- **Stability**: Clean shutdown for ALL resource types

**Universal Pattern**:
```python
# ❌ WRONG - No cleanup (leaks ANY resource)
server = MCPServerStdio(params={...})
await server.connect()
result = await Runner.run(agent, input)
# Database connections, file handles, API clients stay open!

# ✅ CORRECT - Always cleanup (works for ANY resource)
async def safe_resource_operation(user_input: str, user_id: str):
    server = MCPServerStdio(params={...})
    db_session = None
    file_handle = None
    api_client = None

    try:
        # Connect to resources
        await server.connect()
        db_session = create_db_session()
        file_handle = open_file()
        api_client = create_api_client()

        # Use resources
        agent.mcp_servers = [server]
        result = await Runner.run(agent, user_input)

        return result

    finally:
        # Cleanup ALL resources in reverse order
        if api_client: await api_client.close()
        if file_handle: file_handle.close()
        if db_session: db_session.close()
        if server: await server.cleanup()
```

### 6. **Error Resilience**
**Principle**: Tools must handle errors without crashing agent.

**Why Universal**:
- **Stability**: Agent continues working with ANY resource
- **User experience**: Helpful errors for ANY operation
- **System reliability**: Stable regardless of resource type
- **Debugging**: Preserved context for ANY failure

**Universal Pattern**:
```python
# ❌ WRONG - Crashes agent (ANY resource failure breaks system)
@mcp.tool()
def risky_operation(user_id: str, resource_id: str):
    result = dangerous_resource_call()  # ANY resource can fail
    return result  # Exception crashes agent

# ✅ CORRECT - Graceful errors (works for ANY resource failure)
@mcp.tool()
def safe_operation(user_id: str, operation: str, **params) -> dict:
    """
    Handles errors for ANY resource type gracefully.
    """
    try:
        # Validate input
        if not user_id:
            return {"success": False, "error": "Authentication required"}
        if not operation:
            return {"success": False, "error": "Operation required"}

        # Perform ANY operation
        service = get_service()
        result = service.execute(user_id, operation, **params)

        return {"success": True, "data": result}

    except ValueError as e:
        return {"success": False, "error": f"Invalid input: {e}"}

    except PermissionError as e:
        return {"success": False, "error": f"Access denied: {e}"}

    except ConnectionError as e:
        return {"success": False, "error": f"Resource unavailable: {e}"}

    except Exception as e:
        # Log for debugging ANY resource failure
        print(f"Operation '{operation}' failed: {e}")
        return {"success": False, "error": "Operation failed"}
```

## 🏗️ **Universal Architecture Patterns**

### Pattern 1: Per-Request Isolation (ANY Resource)
```
Request 1: [JWT] → [MCP Server 1] → [Tools 1] → [Cleanup 1] → [Resource 1]
Request 2: [JWT] → [MCP Server 2] → [Tools 2] → [Cleanup 2] → [Resource 2]
Request 3: [JWT] → [MCP Server 3] → [Tools 3] → [Cleanup 3] → [Resource 3]
```

**Benefits for ANY resource**:
- **Clean state**: Fresh connection/session for each request
- **No contamination**: User 1 never affects User 2
- **Independent failures**: One request fails, others work
- **Easy scaling**: Horizontal scaling works for ANY resource

### Pattern 2: User Context Flow (ANY Resource)
```
JWT Token → Extract user_id → Inject to Input → Agent → Tools → Service → Resource
```

**Benefits for ANY resource**:
- **Automatic auth**: Works with JWT, API keys, OAuth
- **Universal filtering**: User isolation at EVERY layer
- **Audit trail**: Every action traceable for ANY resource
- **Compliance**: Meets regulations for ANY data type

### Pattern 3: Tool Response Standardization (ANY Operation)
```
Tool Call → Try Operation → Return {success, data/error} → Agent handles → Frontend parses
```

**Benefits for ANY resource**:
- **Consistent handling**: Agent knows what to expect
- **Universal parsing**: Frontend works with ANY resource
- **Retry logic**: Can attempt ANY operation again
- **Debugging**: Standardized error handling

## 🔐 **Universal Security Principles**

### Principle 1: Never Trust User Input (ANY Resource)
```python
# ❌ WRONG - User provides user_id (dangerous for ANY resource)
@mcp.tool()
def delete_resource(user_id: str, resource_id: str):
    # User could provide ANY user_id!
    session.query(Model).filter(
        Model.user_id == user_id,  # Attacker's ID
        Model.id == resource_id
    ).delete()

# ✅ CORRECT - JWT provides user_id (safe for ANY resource)
async def get_user_from_token(token) -> str:
    """Only JWT can provide verified user_id."""
    payload = await verify_token(token)
    return get_user_id_from_token(payload)

@mcp.tool()
def delete_resource(user_id: str, resource_id: str):
    """
    Delete resource - user_id comes from JWT, not user input.
    Works for: Database records, API endpoints, files, services
    """
    service = get_service()
    return service.delete(user_id=user_id, resource_id=resource_id)
```

### Principle 2: Defense in Depth (ANY Resource)
```python
# Multiple layers work for ANY resource type

# Layer 1: Token validation (JWT, API key, OAuth)
async def validate_auth(token: str) -> dict:
    """Works with ANY authentication provider."""
    if token.endswith('.bypass-signature'):
        return decode_bypass_token(token)  # Dev only

    # Production: JWKS, OAuth introspection, etc.
    return await verify_token_with_provider(token)

# Layer 2: User ID extraction (ANY provider)
def get_user_id_from_token(payload: dict) -> str:
    """Works with Better Auth, Auth0, custom, etc."""
    return payload.get('sub') or payload.get('id') or payload.get('user_id')

# Layer 3: Tool parameter (automatic)
@mcp.tool()
def your_tool(user_id: str, ...):  # user_id required

# Layer 4: Service filtering (ANY resource)
class UniversalService:
    def list(self, user_id: str, filters: dict):
        # Database: query.filter(Model.user_id == user_id)
        # API: headers = {"X-User-ID": user_id}
        # Files: path = f"/data/users/{user_id}/..."
        # Services: user_context = {"id": user_id}
        pass

# Layer 5: Path validation (for file operations)
def validate_path(user_dir: str, requested_path: str):
    """Prevent directory traversal for ANY file operation."""
    full_path = os.path.abspath(os.path.join(user_dir, requested_path))
    if not full_path.startswith(os.path.abspath(user_dir)):
        raise ValueError("Directory traversal detected")
    return full_path
```

### Principle 3: Principle of Least Privilege (ANY Resource)
```python
# Each tool gets minimum necessary access

# ❌ WRONG - Tool gets full access (dangerous for ANY resource)
@mcp.tool()
def tool(user_id: str):
    # Can access ANY table, ANY file, ANY API
    users = session.query(User).all()  # Dangerous!
    files = os.listdir("/data")  # Dangerous!
    api = call_any_endpoint()  # Dangerous!

# ✅ CORRECT - Tool gets specific service (safe for ANY resource)
def get_service():
    """Returns service with limited scope."""
    session = Session(engine)
    return YourService(session)  # Limited to specific operations

@mcp.tool()
def tool(user_id: str):
    """Tool only has access to specific resource operations."""
    service = get_service()
    return service.get_user_data(user_id)  # User-scoped only
```

## 🎨 **Universal Design Principles**

### Principle 1: Natural Language First (ANY Resource)
```python
# Tool should be callable with natural language for ANY resource

# ❌ WRONG - Technical parameters (confusing for ANY resource)
@mcp.tool()
def manage_resource(
    user_id: str,
    resource_type_enum: Literal["database", "api", "file"],  # Too technical
    operation_enum: Literal["list", "get", "create", "update", "delete"],  # Confusing
    resource_id_int: int  # Requires lookup
)

# ✅ CORRECT - Natural parameters (clear for ANY resource)
@mcp.tool()
def manage_resource(
    user_id: str,
    action: str,           # "list", "get", "create", "update", "delete"
    resource_type: str,    # "database_records", "api_endpoints", "files"
    identifier: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    filters: Optional[Dict[str, Any]] = None
) -> dict:
    """
    Manage ANY resource type with natural language.

    Examples:
        - "List all database records"
        - "Get user files in documents folder"
        - "Create new API endpoint"
        - "Update service configuration"
        - "Delete old log files"
    """
```

### Principle 2: Self-Documenting (ANY Resource)
```python
# Tools should explain themselves to the LLM for ANY resource

@mcp.tool()
def universal_operation(
    user_id: str,
    operation: str,
    resource_type: str,
    **params
) -> dict:
    """
    Perform ANY operation on ANY resource type.

    This tool provides a universal interface for managing resources
    across databases, APIs, file systems, and external services.

    Args:
        user_id: User ID from JWT (automatically provided)
        operation: Operation to perform
            - "list": List resources (supports filters, pagination)
            - "get": Get specific resource by ID
            - "create": Create new resource with data
            - "update": Update existing resource
            - "delete": Delete resource
        resource_type: Type of resource to manage
            - Database: "users", "products", "orders"
            - API: "endpoints", "webhooks", "services"
            - Files: "documents", "images", "logs"
            - Services: "configurations", "settings", "monitors"
        **params: Resource-specific parameters
            - filters: Dict for filtering list results
            - data: Dict for create/update operations
            - identifier: Resource ID for get/update/delete
            - limit: Max results (default 50)
            - offset: Pagination offset (default 0)

    Returns:
        dict: {
            "success": True,
            "data": [...],  # List or single object
            "count": 10,    # Total count (for lists)
            "id": "..."     # Created/updated ID
        } or {
            "success": False,
            "error": "Descriptive error message"
        }

    Examples:
        - "List all users in database"
        - "Get API endpoint configuration"
        - "Create new document with content"
        - "Update service settings"
        - "Delete old log files"
        - "List products with category=electronics, limit 20"
    """
    # Implementation
```

### Principle 3: Fail Gracefully (ANY Resource)
```python
# Tools should never crash the agent for ANY resource failure

@mcp.tool()
def robust_operation(user_id: str, operation: str, **params) -> dict:
    """
    Handles errors for ANY resource type gracefully.
    """
    try:
        # Validate input
        if not user_id:
            return {"success": False, "error": "Authentication required"}
        if not operation:
            return {"success": False, "error": "Operation required"}

        # Perform ANY operation
        service = get_service()
        result = service.execute(user_id, operation, **params)

        return {"success": True, "data": result}

    except ValidationError as e:
        return {"success": False, "error": f"Invalid input: {e}"}

    except PermissionError as e:
        return {"success": False, "error": f"Access denied: {e}"}

    except ConnectionError as e:
        return {"success": False, "error": f"Resource unavailable: {e}"}

    except TimeoutError as e:
        return {"success": False, "error": f"Operation timed out: {e}"}

    except Exception as e:
        # Log full error for debugging ANY resource failure
        print(f"Operation '{operation}' failed: {e}")
        return {"success": False, "error": "Operation failed due to unexpected error"}
```

## 📊 **Universal Performance Principles**

### Principle 1: Connection Pooling (ANY Resource)
```python
# Reuse connections for ANY resource type

# ❌ WRONG - New connection per tool (inefficient for ANY resource)
@mcp.tool()
def tool1():
    engine = create_engine(DATABASE_URL)  # New DB connection
    session = Session(engine)
    # ...

@mcp.tool()
def tool2():
    client = httpx.Client()  # New HTTP client
    # ...

# ✅ CORRECT - Shared connections (efficient for ANY resource)
from your_database import engine  # Single DB engine
from your_api import api_client   # Single API client

@mcp.tool()
def tool1():
    session = Session(engine)  # Reuse DB pool
    # ...

@mcp.tool()
def tool2():
    # Reuse API client
    result = api_client.get("/endpoint")
    # ...
```

### Principle 2: Query Optimization (ANY Resource)
```python
# Optimize for ANY resource type

# ❌ WRONG - N+1 queries (bad for ANY resource)
@mcp.tool()
def list_resources(user_id: str):
    items = session.query(Model).filter_by(user_id=user_id).all()
    result = []
    for item in items:
        # Additional query per item!
        user = session.query(User).get(item.user_id)
        result.append({**item.to_dict(), "user": user.name})
    return result

# ✅ CORRECT - Efficient operations (good for ANY resource)
@mcp.tool()
def list_resources(user_id: str, filters: dict = None, limit: int = 50, offset: int = 0) -> dict:
    """
    Efficient listing for ANY resource type.
    """
    service = get_service()
    try:
        # Single optimized operation
        result = service.list(
            user_id=user_id,
            filters=filters or {},
            limit=limit,
            offset=offset
        )
        return {
            "success": True,
            "data": result["items"],
            "count": result["count"]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### Principle 3: Timeout Management (ANY Resource)
```python
# Prevent hanging requests for ANY resource

async def run_agents(user_input: str, user_id: str) -> dict:
    """
    Universal agent runner with timeout for ANY resource.
    """
    server = MCPServerStdio(
        params={"command": "uv", "args": ["run", "mcp_server.py"]},
        client_session_timeout_seconds=60  # MCP timeout
    )

    try:
        await server.connect()
        agent.mcp_servers = [server]
        enhanced_input = f"[User: {user_id}] {user_input}"

        # Overall timeout for ANY operation
        result = await asyncio.wait_for(
            Runner.run(agent, enhanced_input),
            timeout=120  # 2 min total
        )

        return {"response": result.final_output}

    except asyncio.TimeoutError:
        return {"success": False, "error": "Request timed out"}

    finally:
        await server.cleanup()
        agent.mcp_servers = []
```

## 🧪 **Universal Testing Principles**

### Principle 1: Test User Isolation (ANY Resource)
```python
async def test_user_isolation():
    """Verify users cannot access each other's data for ANY resource."""
    # User 1 creates resource
    result1 = await run_agents("Create resource in database", "user-1")
    resource_id = extract_id(result1)

    # User 2 tries to access User 1's resource
    result2 = await run_agents(f"Get resource {resource_id}", "user-2")

    # Should fail or return empty for ANY resource
    assert "not found" in result2["response"].lower() or \
           result2["response"] == "[]"
```

### Principle 2: Test Error Handling (ANY Resource)
```python
async def test_error_handling():
    """Verify graceful error handling for ANY operation."""
    # Invalid resource ID
    result = await run_agents("Get resource: invalid-id", "user-1")
    assert "error" in result["response"].lower()

    # Missing required fields
    result = await run_agents("Create resource: ", "user-1")
    assert "error" in result["response"].lower()

    # Permission violations
    result = await run_agents("Delete all resources", "user-1")
    assert "permission" in result["response"].lower() or \
           "unauthorized" in result["response"].lower()
```

### Principle 3: Test Resource Cleanup (ANY Resource)
```python
async def test_resource_cleanup():
    """Verify no resource leaks for ANY resource type."""
    import asyncio
    initial = len(asyncio.all_tasks())

    # Make multiple requests
    for _ in range(10):
        await run_agents("Create resource: test", "user-1")

    # Verify cleanup for ANY resource
    final = len(asyncio.all_tasks())
    assert final <= initial + 2  # Allow small overhead
```

## 🎯 **Summary: The Universal MCP Manifesto**

These principles work for **ANY** resource type:

1. **Dynamic**: Create servers per request for ANY resource
2. **Isolated**: Every tool needs user_id for ANY resource
3. **Consistent**: All tools return structured responses for ANY operation
4. **Contextual**: Inject user context for ANY resource access
5. **Clean**: Always cleanup for ANY resource lifecycle
6. **Resilient**: Handle errors gracefully for ANY resource failure
7. **Secure**: Multiple validation layers for ANY resource
8. **Natural**: Self-documenting interfaces for ANY resource
9. **Tested**: Verify isolation for ANY resource integration
10. **Performant**: Optimize access for ANY resource type

**Remember**: These principles create production-ready MCP integrations that work for databases, APIs, file systems, external services, hardware, IoT devices, or any future resource type you need to connect.