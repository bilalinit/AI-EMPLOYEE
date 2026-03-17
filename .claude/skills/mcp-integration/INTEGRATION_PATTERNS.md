# MCP Integration Patterns: Universal Architecture Guide

> **Reference guide for designing MCP integration architecture for ANY application**

## 🎯 **Pattern Philosophy**

This document provides **architectural patterns**, not code templates. Each pattern describes the **structure and flow** that you must implement using your application's specific tools and data models.

## 🏗️ **Server Architecture Patterns**

### **Pattern 1: Single-File Server**
**When to use**: Simple applications, 1-5 tools, quick prototypes
**Structure**:
```
mcp_server.py
├── Imports (your dependencies)
├── Server creation (FastMCP)
├── Service setup (your business logic)
├── Tool definitions (your operations)
└── Main execution
```

**Flow**:
```
Request → MCP Server → Tool → Your Service → Your Data → Response
```

**Implementation approach**:
- All tools in one file
- Direct service calls
- Simple error handling
- Good for: file managers, simple APIs, basic CRUD

### **Pattern 2: Multi-File Modular Server**
**When to use**: Complex applications, 5+ tools, team development
**Structure**:
```
mcp_server/
├── __init__.py
├── server.py          # Main server setup
├── tools/
│   ├── __init__.py
│   ├── database_tools.py
│   ├── api_tools.py
│   └── file_tools.py
├── services/
│   ├── __init__.py
│   ├── database_service.py
│   ├── api_service.py
│   └── file_service.py
└── models/
    ├── __init__.py
    └── schemas.py
```

**Flow**:
```
Request → MCP Server → Tool Router → Specific Tool → Service Layer → Data Layer → Response
```

**Implementation approach**:
- Tools organized by domain
- Service layer separates business logic
- Models define data structures
- Good for: enterprise apps, multi-resource systems

### **Pattern 3: Hybrid Server**
**When to use**: Mix of simple and complex operations
**Structure**:
```
mcp_server.py              # Main server
├── Simple tools (inline)
├── Complex tools (delegated)
└── Service imports

services/
├── simple_service.py      # Simple operations
└── complex_service.py     # Complex operations
```

**Flow**:
```
Request → MCP Server → Tool Router → Simple (inline) or Complex (service) → Response
```

**Implementation approach**:
- Simple tools: inline implementation
- Complex tools: service delegation
- Good for: applications with mixed complexity

## 🤖 **Agent Integration Patterns**

### **Pattern 1: Direct Integration**
**When**: Single agent, single MCP server
**Structure**:
```python
# agents.py
async def run_agents(user_input: str, user_id: str) -> dict:
    # 1. Create server
    server = MCPServerStdio(params={...})

    # 2. Configure agent
    agent.mcp_servers = [server]

    # 3. Run with context
    try:
        await server.connect()
        enhanced_input = f"[User: {user_id}] {user_input}"
        result = await Runner.run(agent, enhanced_input)
        return parse_result(result)
    finally:
        await server.cleanup()
```

**Use case**: Most applications, single purpose tools

### **Pattern 2: Multi-Server Integration**
**When**: Multiple MCP servers for different resource types
**Structure**:
```python
# agents.py
async def run_agents(user_input: str, user_id: str) -> dict:
    # Create multiple servers
    servers = [
        MCPServerStdio(params={"command": "uv", "args": ["run", "db_server.py"]}),
        MCPServerStdio(params={"command": "uv", "args": ["run", "api_server.py"]}),
        MCPServerStdio(params={"command": "uv", "args": ["run", "file_server.py"]})
    ]

    agent.mcp_servers = servers

    try:
        for server in servers:
            await server.connect()

        enhanced_input = f"[User: {user_id}] {user_input}"
        result = await Runner.run(agent, enhanced_input)
        return parse_result(result)
    finally:
        for server in servers:
            await server.cleanup()
```

**Use case**: Applications with multiple resource types

### **Pattern 3: Agent Handoff Integration**
**When**: Multiple agents with different responsibilities
**Structure**:
```python
# agents.py
main_agent = Agent(name="Router", instructions="Route to specialists", ...)
db_agent = Agent(name="DB_Specialist", instructions="Handle database", ...)
api_agent = Agent(name="API_Specialist", instructions="Handle APIs", ...)

main_agent.handoffs = [db_agent, api_agent]

async def run_agents(user_input: str, user_id: str) -> dict:
    servers = [MCPServerStdio(params={...}) for _ in range(2)]

    # Assign servers to agents
    db_agent.mcp_servers = [servers[0]]
    api_agent.mcp_servers = [servers[1]]

    try:
        for server in servers:
            await server.connect()

        enhanced_input = f"[User: {user_id}] {user_input}"
        result = await Runner.run(main_agent, enhanced_input)
        return parse_result(result)
    finally:
        for server in servers:
            await server.cleanup()
```

**Use case**: Complex applications with specialized agents

## 🔐 **Authentication Integration Patterns**

### **Pattern 1: JWT Extraction**
**Flow**:
```
HTTP Request → Header → Token → Validation → User ID → Agent Context
```

**Implementation**:
```python
# FastAPI dependency
async def get_user_id(authorization: str = Header(...)) -> str:
    token = authorization.replace("Bearer ", "")
    payload = await verify_token(token)  # Your implementation
    return get_user_id_from_token(payload)  # Your implementation
```

**Key points**:
- Validate token signature
- Extract user identifier
- Handle expiration
- Return clean user_id string

### **Pattern 2: Token Bypass (Development)**
**Flow**:
```
Development Request → Bypass validation → Mock user_id
```

**Implementation**:
```python
async def get_user_id(authorization: str = Header(...)) -> str:
    token = authorization.replace("Bearer ", "")

    # Development bypass
    if token.endswith('.bypass-signature'):
        return decode_bypass_token(token)

    # Production validation
    payload = await verify_token(token)
    return get_user_id_from_token(payload)
```

**Use case**: Local development, testing

### **Pattern 3: Multi-Provider Auth**
**Flow**:
```
Request → Determine Provider → Validate → Extract User ID
```

**Implementation**:
```python
async def get_user_id(authorization: str = Header(...)) -> str:
    token = authorization.replace("Bearer ", "")

    # Determine provider
    if token.startswith('jwt_'):
        return await validate_jwt(token)
    elif token.startswith('api_'):
        return await validate_api_key(token)
    elif token.endswith('.bypass'):
        return decode_bypass(token)

    raise HTTPException(status_code=401, detail="Unknown auth provider")
```

**Use case**: Applications with multiple auth methods

## 📊 **Data Flow Patterns**

### **Pattern 1: Direct Database Access**
**Flow**:
```
Tool → Service → Database Session → Query → Result → Response
```

**Structure**:
```python
@mcp.tool()
def operation(user_id: str, ...) -> dict:
    session = Session(engine)
    try:
        # Query with user_id filter
        result = session.query(Model).filter(
            Model.user_id == user_id,
            ...
        ).all()
        return {"success": True, "data": [r.to_dict() for r in result]}
    finally:
        session.close()
```

**Use case**: Simple database applications

### **Pattern 2: Service Layer Abstraction**
**Flow**:
```
Tool → Service Method → Business Logic → Data Access → Result → Response
```

**Structure**:
```python
# Tool
@mcp.tool()
def operation(user_id: str, ...) -> dict:
    service = get_service()
    try:
        result = service.operation(user_id, ...)
        return {"success": True, "data": result.to_dict()}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Service
class YourService:
    def operation(self, user_id: str, ...) -> Model:
        # Business logic here
        # Validation, transformation, etc.
        # Data access with user isolation
        pass
```

**Use case**: Complex business logic, reusable services

### **Pattern 3: API Integration**
**Flow**:
```
Tool → Service → User Credentials → API Call → Parse → Response
```

**Structure**:
```python
# Tool
@mcp.tool()
def call_api(user_id: str, endpoint: str, method: str = "GET") -> dict:
    service = get_service()
    try:
        result = service.api_call(user_id, endpoint, method)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Service
class APIService:
    def api_call(self, user_id: str, endpoint: str, method: str):
        # Get user-specific credentials
        creds = self.get_user_credentials(user_id)

        # Make API call
        response = httpx.request(
            method=method,
            url=f"{BASE_URL}/{endpoint}",
            headers={"Authorization": f"Bearer {creds.token}"}
        )

        return response.json()
```

**Use case**: External API integrations

### **Pattern 4: File System Operations**
**Flow**:
```
Tool → Path Validation → User Directory → File Operation → Response
```

**Structure**:
```python
# Tool
@mcp.tool()
def manage_files(user_id: str, action: str, path: str, content: Optional[str] = None) -> dict:
    service = get_service()
    try:
        result = service.file_operation(user_id, action, path, content)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Service
class FileService:
    def file_operation(self, user_id: str, action: str, path: str, content: Optional[str] = None):
        # Security: Validate path
        user_dir = f"/data/users/{user_id}"
        full_path = self.validate_path(user_dir, path)

        # Perform operation
        if action == "list":
            return os.listdir(full_path)
        elif action == "read":
            with open(full_path, 'r') as f:
                return f.read()
        # ... etc

    def validate_path(self, user_dir: str, path: str) -> str:
        full_path = os.path.abspath(os.path.join(user_dir, path))
        if not full_path.startswith(os.path.abspath(user_dir)):
            raise ValueError("Invalid path - directory traversal detected")
        return full_path
```

**Use case**: File management, document storage

## 🧪 **Testing Architecture Patterns**

### **Pattern 1: Unit Test Pattern**
**Structure**:
```python
# test_unit.py
async def test_tool_directly():
    # Test tool function directly
    result = await your_tool(user_id="test-user", param="value")
    assert result["success"] == True
    assert "data" in result
```

**Use case**: Testing individual tool logic

### **Pattern 2: Integration Test Pattern**
**Structure**:
```python
# test_integration.py
async def test_full_flow():
    # Test complete agent + MCP flow
    result = await run_agents("Test operation", "test-user")
    assert "response" in result
    assert result["agent_used"] in ["MainAgent", "Specialist"]
```

**Use case**: Testing complete system

### **Pattern 3: Security Test Pattern**
**Structure**:
```python
# test_security.py
async def test_user_isolation():
    # Create data for user 1
    await run_agents("Create resource", "user-1")

    # User 2 should not access it
    result = await run_agents("List resources", "user-2")
    assert len(result["data"]) == 0

async def test_path_traversal():
    # Attempt directory traversal
    result = await run_agents("Read file: ../secret.txt", "user-1")
    assert "error" in result["response"].lower()
```

**Use case**: Security verification

### **Pattern 4: Performance Test Pattern**
**Structure**:
```python
# test_performance.py
async def test_cleanup():
    initial = len(asyncio.all_tasks())

    # Make multiple requests
    for _ in range(10):
        await run_agents("Test operation", "user-1")

    # Verify no resource leaks
    final = len(asyncio.all_tasks())
    assert final <= initial + 2
```

**Use case**: Resource management verification

## 🔧 **Error Handling Patterns**

### **Pattern 1: Graceful Degradation**
**Structure**:
```python
try:
    result = risky_operation()
    return {"success": True, "data": result}
except SpecificError as e:
    # Expected error - return helpful message
    return {"success": False, "error": f"Specific issue: {e}"}
except Exception as e:
    # Unexpected error - generic message
    return {"success": False, "error": "Operation failed"}
```

### **Pattern 2: Retry Logic**
**Structure**:
```python
async def operation_with_retry(user_id: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            return await your_operation(user_id)
        except TransientError as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

### **Pattern 3: Circuit Breaker**
**Structure**:
```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failures = 0
        self.last_failure = None
        self.state = "closed"  # closed, open, half-open

    async def call(self, func):
        if self.state == "open":
            if time.time() - self.last_failure > self.timeout:
                self.state = "half-open"
            else:
                raise Exception("Circuit breaker is open")

        try:
            result = await func()
            self.failures = 0
            self.state = "closed"
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure = time.time()
            if self.failures >= self.failure_threshold:
                self.state = "open"
            raise
```

## 📋 **Implementation Checklist**

For ANY MCP integration, verify:

### **Server Patterns**
- [ ] Choose appropriate server architecture (single-file, modular, hybrid)
- [ ] Implement service layer separation
- [ ] Use consistent tool signature pattern
- [ ] Apply structured responses

### **Integration Patterns**
- [ ] Choose agent integration pattern (direct, multi-server, handoff)
- [ ] Implement dynamic server creation
- [ ] Apply context injection
- [ ] Use proper cleanup in finally blocks

### **Authentication Patterns**
- [ ] Implement JWT extraction
- [ ] Add user_id to all tools
- [ ] Apply validation layers
- [ ] Handle development bypass

### **Data Flow Patterns**
- [ ] Choose data access pattern (direct, service layer, API, file)
- [ ] Implement user isolation in data layer
- [ ] Apply path validation for file operations
- [ ] Use connection pooling for databases

### **Testing Patterns**
- [ ] Write unit tests for tools
- [ ] Write integration tests for full flow
- [ ] Write security tests for isolation
- [ ] Write performance tests for cleanup

### **Error Handling Patterns**
- [ ] Implement graceful degradation
- [ ] Add retry logic for transient errors
- [ ] Use circuit breaker for external services
- [ ] Return consistent error format

## 🎯 **Pattern Selection Guide**

### **Choose Server Architecture:**
- **Single-file**: < 5 tools, simple operations
- **Multi-file**: 5+ tools, complex operations
- **Hybrid**: Mix of simple and complex

### **Choose Integration Pattern:**
- **Direct**: Single resource type
- **Multi-server**: Multiple resource types
- **Handoff**: Multiple specialized agents

### **Choose Data Flow:**
- **Direct DB**: Simple CRUD, no business logic
- **Service layer**: Complex business logic, reusability
- **API integration**: External services
- **File operations**: Document management

### **Choose Testing:**
- **Unit**: Individual tool logic
- **Integration**: Complete system flow
- **Security**: Isolation and access control
- **Performance**: Resource management

---

**Remember**: These are **patterns**, not **templates**. You must implement them using your application's specific:
- Data models and schemas
- Business logic and services
- Authentication methods
- Error types and handling
- Resource types and operations

The patterns provide the **structure and flow** - you provide the **implementation details**.