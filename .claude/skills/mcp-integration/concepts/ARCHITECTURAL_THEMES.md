# MCP Integration Architectural Themes

## 🎯 **Theme 1: The Dynamic Lifecycle**
**Core Concept**: MCP servers are born, live, and die with each request.

**Universal Pattern**:
```python
async def handle_any_request(user_input: str, user_id: str) -> dict:
    """
    Works for ANY resource type - database, API, files, etc.
    """
    # Birth: Create fresh server
    server = MCPServerStdio(
        params={
            "command": "uv",
            "args": ["run", "mcp_server.py"]  # Your server file
        }
    )

    try:
        # Life: Connect and use
        await server.connect()
        agent.mcp_servers = [server]

        # Inject context
        enhanced_input = f"[User: {user_id}] {user_input}"
        result = await Runner.run(agent, enhanced_input)

        return {"response": result.final_output}

    finally:
        # Death: Always cleanup
        await server.cleanup()
        agent.mcp_servers = []
```

**Why Universal**:
- **Resource type agnostic**: Works for databases, APIs, files, services
- **State isolation**: Clean slate for every request
- **Security**: Prevents cross-user contamination
- **Memory management**: No leaks across requests

## 🎯 **Theme 2: The User Identity Chain**
**Core Concept**: User identity flows through every layer of the system.

**Universal Pattern**:
```
JWT Token → Extract user_id → Agent Context → Tool Parameter → Service Filter → Data Layer
```

**Implementation for ANY resource**:
```python
# Layer 1: Authentication (FastAPI)
async def get_user_id(authorization: str = Header(...)) -> str:
    token = authorization.replace("Bearer ", "")
    payload = await verify_token(token)
    return get_user_id_from_token(payload)

# Layer 2: Agent Integration
async def run_agents(user_input: str, user_id: str) -> dict:
    enhanced_input = f"[Authenticated as user: {user_id}] {user_input}"
    # ... server creation and execution

# Layer 3: Tool Definition (works for ANY resource)
@mcp.tool()
def list_resources(user_id: str, filters: dict = None) -> dict:
    """Universal tool - works for DB, API, files, etc."""
    service = get_service()
    return service.list(user_id=user_id, filters=filters or {})

# Layer 4: Service Layer (your business logic)
class YourService:
    def list(self, user_id: str, filters: dict):
        # Database: query.filter(Model.user_id == user_id)
        # API: headers = {"X-User-ID": user_id}
        # Files: path = f"/data/users/{user_id}/..."
        # Service: user_context = {"id": user_id}
        pass
```

**Why Universal**:
- **Security**: Identity verified at entry point
- **Isolation**: Automatic data separation
- **Audit**: Every action traceable to user
- **Compliance**: Works with any auth system

## 🎯 **Theme 3: The Response Standard**
**Core Concept**: All tools speak the same language, regardless of resource type.

**Universal Pattern**:
```python
@mcp.tool()
def universal_operation(
    user_id: str,
    # Your parameters here
    operation: str = "list",
    resource_id: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None
) -> dict:
    """
    Works for ANY operation on ANY resource.
    """
    try:
        # Validate input
        if not user_id:
            return {"success": False, "error": "Authentication required"}

        # Perform operation (database, API, file, etc.)
        service = get_service()
        result = service.execute(
            user_id=user_id,
            operation=operation,
            resource_id=resource_id,
            data=data
        )

        return {
            "success": True,
            "data": result,
            "count": len(result) if isinstance(result, list) else None
        }

    except ValidationError as e:
        return {"success": False, "error": f"Invalid input: {e}"}

    except PermissionError as e:
        return {"success": False, "error": f"Access denied: {e}"}

    except Exception as e:
        # Log full error for debugging
        print(f"Operation failed: {e}")
        return {"success": False, "error": "Operation failed"}
```

**Why Universal**:
- **Consistency**: Agent knows what to expect
- **Error handling**: Graceful failures for any resource
- **Retry logic**: Agent can attempt alternatives
- **Frontend parsing**: Uniform response handling

## 🎯 **Theme 4: The Security Fortress**
**Core Concept**: Multiple defense layers work for ANY resource type.

**Universal Validation Stack**:
```python
# Layer 1: Token Validation (JWT, API Key, OAuth, etc.)
async def validate_auth(token: str) -> dict:
    if token.endswith('.bypass-signature'):
        return decode_bypass_token(token)  # Dev only

    # Production: JWKS, OAuth introspection, etc.
    return await verify_token_with_provider(token)

# Layer 2: User ID Extraction (works with any provider)
def extract_user_id(payload: dict) -> str:
    # Better Auth: payload.get('sub') or payload.get('id')
    # Auth0: payload.get('sub')
    # Custom: payload.get('user_id')
    # API Key: lookup user from key
    return payload.get('sub') or payload.get('id') or payload.get('user_id')

# Layer 3: Tool Parameter (automatic from JWT)
@mcp.tool()
def your_tool(user_id: str, ...):  # user_id required

# Layer 4: Resource-Specific Filtering
class UniversalService:
    def list(self, user_id: str, filters: dict):
        # Database: query.filter(Model.user_id == user_id)
        # API: Add user header/context
        # Files: Validate path under user directory
        # External: Use user credentials
        pass

# Layer 5: Path Validation (for file operations)
def validate_path(user_dir: str, requested_path: str) -> str:
    full_path = os.path.abspath(os.path.join(user_dir, requested_path))
    if not full_path.startswith(os.path.abspath(user_dir)):
        raise ValueError("Directory traversal detected")
    return full_path
```

**Why Universal**:
- **Defense in depth**: Multiple independent checks
- **Fail-safe**: One layer fails, others protect
- **Resource agnostic**: Works for DB, API, files, services
- **Compliance**: Meets security standards regardless of resource

## 🎯 **Theme 5: The Error Resilience**
**Core Concept**: Never crash the agent, regardless of resource type or operation.

**Universal Error Handling**:
```python
@mcp.tool()
def resilient_operation(
    user_id: str,
    operation: str,
    **params
) -> dict:
    """
    Handles errors for ANY resource type gracefully.
    """
    try:
        # Input validation
        if not user_id:
            return {"success": False, "error": "Authentication required"}
        if not operation:
            return {"success": False, "error": "Operation required"}

        # Resource-specific operation
        service = get_service()
        result = service.execute(user_id, operation, **params)

        return {"success": True, "data": result}

    except ValueError as e:
        # Invalid input for this resource type
        return {"success": False, "error": f"Invalid input: {e}"}

    except KeyError as e:
        # Missing required parameter
        return {"success": False, "error": f"Missing parameter: {e}"}

    except PermissionError as e:
        # Access denied for this resource
        return {"success": False, "error": f"Access denied: {e}"}

    except ConnectionError as e:
        # API/Database connection failed
        return {"success": False, "error": f"Service unavailable: {e}"}

    except Exception as e:
        # Unexpected error - log and return generic message
        print(f"Unexpected error in {operation}: {e}")
        return {"success": False, "error": "Operation failed due to unexpected error"}
```

**Why Universal**:
- **Stability**: Agent continues working
- **User experience**: Helpful errors for any resource
- **Debugging**: Preserved context for any operation
- **Retry capability**: Agent can try alternatives

## 🎯 **Theme 6: The Natural Language Bridge**
**Core Concept**: Tools should be callable in plain English for ANY resource.

**Universal Design**:
```python
@mcp.tool()
def manage_resources(
    user_id: str,
    action: str,           # "list", "get", "create", "update", "delete"
    resource_type: str,    # "database_records", "api_endpoints", "files", "services"
    identifier: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 50
) -> dict:
    """
    Universal resource management tool.

    Args:
        user_id: User ID from JWT (automatically provided)
        action: What to do - list, get, create, update, delete
        resource_type: What resource to manage
        identifier: Specific resource ID (if applicable)
        data: Data for create/update operations
        filters: Filter criteria (for list operations)
        limit: Maximum results to return

    Returns:
        dict: {
            "success": True,
            "data": [...],  # Operation result
            "count": 10     # Result count
        } or {
            "success": False,
            "error": "Descriptive message"
        }

    Examples:
        - "List all database records"
        - "Get user files in documents folder"
        - "Create new API endpoint with these settings"
        - "Update service configuration"
        - "Delete old logs"
        - "List resources with status=active, limit 10"
    """
    # Implementation
```

**Why Universal**:
- **Usability**: No technical knowledge needed
- **Flexibility**: Many ways to express same operation
- **Discovery**: Agent learns capabilities dynamically
- **Documentation**: Docstrings teach the LLM about ANY resource

## 🎯 **Theme 7: The Resource Lifecycle**
**Core Concept**: Manage connections, sessions, and processes carefully for ANY resource.

**Universal Pattern**:
```python
# Database connections
def get_db_service():
    engine = create_engine(DATABASE_URL, pool_size=10)
    session = Session(engine)
    return DatabaseService(session)

# API clients
def get_api_service():
    client = httpx.Client(timeout=30.0)
    return APIService(client)

# File handles
def get_file_service():
    return FileService(base_path="/data")

# MCP servers
async def run_with_mcp(user_input: str, user_id: str):
    server = MCPServerStdio(params={...})
    try:
        await server.connect()
        # Use server
    finally:
        await server.cleanup()

# Unified cleanup pattern
class ResourceManager:
    def __init__(self):
        self.resources = []

    def add(self, resource, cleanup_func):
        self.resources.append((resource, cleanup_func))

    def cleanup(self):
        for resource, cleanup_func in reversed(self.resources):
            try:
                cleanup_func(resource)
            except Exception as e:
                print(f"Cleanup failed: {e}")
```

**Why Universal**:
- **Performance**: Connection pooling for any resource
- **Memory**: No leaks regardless of resource type
- **Stability**: Clean shutdown for all resources
- **Scalability**: Handles many concurrent requests

## 🎯 **Theme 8: The Testing Mindset**
**Core Concept**: Test isolation, errors, and cleanup for ANY resource.

**Universal Test Patterns**:
```python
async def test_user_isolation():
    """Works for ANY resource type."""
    # User 1 creates resource
    result1 = await run_agents("Create resource in database", "user-1")
    resource_id = extract_id(result1)

    # User 2 should not access it
    result2 = await run_agents(f"Get resource {resource_id}", "user-2")
    assert "not found" in result2["response"].lower() or \
           result2["response"] == "[]"

async def test_error_handling():
    """Works for ANY operation."""
    # Invalid resource ID
    result = await run_agents("Get resource: invalid-id", "user-1")
    assert "error" in result["response"].lower()

    # Missing required fields
    result = await run_agents("Create resource: ", "user-1")
    assert "error" in result["response"].lower()

async def test_resource_cleanup():
    """Works for ANY resource lifecycle."""
    import asyncio
    initial = len(asyncio.all_tasks())

    for _ in range(10):
        await run_agents("Create resource: test", "user-1")

    final = len(asyncio.all_tasks())
    assert final <= initial + 2
```

**Why Universal**:
- **Reliability**: Catches bugs in ANY resource integration
- **Confidence**: Deploy ANY resource without fear
- **Documentation**: Tests show how to use ANY resource
- **Regression**: Prevents breaks in ANY resource type

## 🎯 **Theme 9: The Performance Principle**
**Core Concept**: Optimize for speed and efficiency for ANY resource.

**Universal Optimization**:
```python
# Connection pooling (works for DB, API, etc.)
class ConnectionPool:
    def __init__(self, max_connections=10):
        self.pool = []
        self.max_connections = max_connections

    def get_connection(self):
        if self.pool:
            return self.pool.pop()
        elif len(self.pool) < self.max_connections:
            return create_new_connection()
        else:
            # Wait for available connection
            pass

# Query optimization (universal)
def optimized_query(service, user_id: str, filters: dict, limit: int, offset: int):
    # Database: Single query with filters
    # API: Batch requests
    # Files: Efficient directory traversal
    # Services: Cached results
    return service.list(user_id=user_id, filters=filters, limit=limit, offset=offset)

# Avoid N+1 problems
def get_related_data(user_id: str, resource_ids: list):
    # Database: Single JOIN query
    # API: Batch endpoint
    # Files: Bulk read
    # Services: Parallel requests
    pass
```

**Why Universal**:
- **Speed**: Faster responses for ANY resource
- **Scale**: Handle more users across ALL resources
- **Cost**: Efficient resource usage
- **Experience**: Consistent performance

## 🎯 **Theme 10: The Documentation Culture**
**Core Concept**: Every tool tells its own story, regardless of resource type.

**Universal Documentation**:
```python
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

    Notes:
        - All operations are user-scoped automatically
        - Pagination supported for large result sets
        - Error messages are descriptive and actionable
        - Works with ANY resource type transparently
    """
    # Implementation
```

**Why Universal**:
- **LLM understanding**: Agent knows how to use ANY resource
- **Developer experience**: Clear expectations for ALL operations
- **Maintenance**: Future developers understand ANY resource
- **Discovery**: Self-documenting API for ANY resource type

## 🎯 **Theme 11: The Evolution Pattern**
**Core Concept**: Start simple for ANY resource, add complexity as needed.

**Universal Evolution**:
```python
# v1: Basic tool (works for ANY resource)
@mcp.tool()
def basic_resource(user_id: str, action: str) -> dict:
    service = get_service()
    return service.execute(user_id, action)

# v2: Add error handling
@mcp.tool()
def resource_with_errors(user_id: str, action: str) -> dict:
    try:
        service = get_service()
        result = service.execute(user_id, action)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

# v3: Add validation
@mcp.tool()
def resource_with_validation(user_id: str, action: str, data: dict = None) -> dict:
    if not user_id:
        return {"success": False, "error": "Authentication required"}
    if not action:
        return {"success": False, "error": "Action required"}

    try:
        service = get_service()
        result = service.execute(user_id, action, data or {})
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

# v4: Add logging/monitoring
@mcp.tool()
def resource_with_monitoring(user_id: str, action: str, data: dict = None) -> dict:
    print(f"User {user_id} performing {action}")
    start_time = time.time()

    try:
        result = resource_with_validation(user_id, action, data)
        duration = time.time() - start_time
        print(f"Operation completed in {duration}s")
        return result
    except Exception as e:
        print(f"Operation failed: {e}")
        raise

# v5: Add caching/performance
class CachedService:
    def __init__(self, underlying_service):
        self.service = underlying_service
        self.cache = {}

    def execute(self, user_id: str, action: str, data: dict = None):
        cache_key = f"{user_id}:{action}:{str(data)}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        result = self.service.execute(user_id, action, data)
        self.cache[cache_key] = result
        return result
```

**Why Universal**:
- **MVP**: Get ANY resource working quickly
- **Iteration**: Improve ANY resource incrementally
- **Feedback**: Learn from ANY resource usage
- **Quality**: Build robustly for ANY resource

## 🎯 **Theme 12: The Integration Mindset**
**Core Concept**: MCP is the universal bridge between natural language and ANY resource.

**Universal Integration**:
```
Natural Language → Agent → MCP Tools → [Database | API | Files | Services] → Results → Natural Language
```

**Universal Implementation**:
```python
# Your resource (ANY type)
class YourResource:
    def execute(self, user_id: str, operation: str, **params):
        # Database: SQL queries with user isolation
        # API: HTTP requests with user credentials
        # Files: File operations in user directory
        # Services: Service calls with user context
        # Hardware: Device commands with user permissions
        pass

# Universal MCP bridge
@mcp.tool()
def manage_resource(user_id: str, operation: str, **params) -> dict:
    """Universal bridge to ANY resource."""
    resource = YourResource()
    try:
        result = resource.execute(user_id, operation, **params)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Universal agent integration
async def run_agents(user_input: str, user_id: str) -> dict:
    server = MCPServerStdio(params={"command": "uv", "args": ["run", "mcp_server.py"]})
    try:
        await server.connect()
        agent.mcp_servers = [server]
        enhanced_input = f"[User: {user_id}] {user_input}"
        result = await Runner.run(agent, enhanced_input)
        return {"response": result.final_output}
    finally:
        await server.cleanup()

# Natural language flow
# User: "List all my database records"
# Agent: Uses manage_resource tool
# Resource: DatabaseService.list(user_id="user-1")
# Response: "Here are your 15 records..."

# User: "Upload file to cloud storage"
# Agent: Uses manage_resource tool
# Resource: FileService.upload(user_id="user-1", file=...)
# Response: "File uploaded successfully"

# User: "Check API status"
# Agent: Uses manage_resource tool
# Resource: APIService.health_check(user_id="user-1")
# Response: "API is running normally"
```

**Why Universal**:
- **Abstraction**: Hide complexity of ANY resource
- **Power**: Give agents superpowers over ANY resource
- **Flexibility**: Connect ANY resource type
- **Future-proof**: Adapt to ANY new resource

## 🎯 **Summary: The 12 Universal Themes**

These themes work for **ANY** resource type:

1. **Dynamic Lifecycle**: Per-request servers for ANY resource
2. **User Identity Chain**: JWT → ANY resource with user isolation
3. **Response Standard**: Consistent format for ANY operation
4. **Security Fortress**: Multiple layers for ANY resource
5. **Error Resilience**: Graceful handling for ANY failure
6. **Natural Language Bridge**: Plain English for ANY resource
7. **Resource Lifecycle**: Manage ANY resource connections
8. **Testing Mindset**: Verify ANY resource integration
9. **Performance Principle**: Optimize ANY resource access
10. **Documentation Culture**: Self-documenting for ANY resource
11. **Evolution Pattern**: Start simple, iterate on ANY resource
12. **Integration Mindset**: Bridge to ANY resource type

**Remember**: These themes create production-ready MCP integrations that work for databases, APIs, file systems, external services, hardware, or any future resource type.