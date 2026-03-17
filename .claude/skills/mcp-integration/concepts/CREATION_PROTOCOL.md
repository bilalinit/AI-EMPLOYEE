# MCP Integration Creation Protocol

## 🎯 **The Universal 5-Step Design Process**

This protocol teaches you how to design MCP integration for **any** resource, not just specific use cases. Follow these steps to create tools that work for databases, APIs, file systems, or any programmatic resource.

### **Step 1: Resource Analysis**
**Ask these universal questions:**

1. **What resource type?**
   - Database (PostgreSQL, MySQL, SQLite, NoSQL)
   - API (REST, GraphQL, gRPC, custom)
   - File system (local, cloud storage)
   - External service (email, payments, messaging)
   - Hardware/IoT device
   - Internal tool/system

2. **What operations are needed?**
   - CRUD (Create, Read, Update, Delete)
   - Query/Search operations
   - Stream/Real-time data
   - Trigger/Action execution
   - Batch operations

3. **Who uses it?**
   - Single user application
   - Multi-tenant (user isolation required)
   - Admin-only access
   - Mixed permissions

4. **What authentication?**
   - JWT tokens (Better Auth, Auth0, etc.)
   - API keys
   - OAuth flows
   - Internal system auth
   - No auth (public resources)

5. **What data structures?**
   - Database schema
   - API response format
   - File metadata
   - Service-specific models

**Output**: Requirements document
```markdown
## MCP Server Requirements

**Resource Type**: [Database/API/File/Service/etc]
**Operations**: [CRUD, Query, Search, Stream, etc]
**Users**: [Single/Multi-tenant/Admin/Mixed]
**Auth**: [JWT/API Key/OAuth/Internal]
**Data Model**: [Schema definition]
**Constraints**: [Rate limits, permissions, etc]
```

### **Step 2: Universal Tool Design**
**Pattern for ANY tool:**
```python
@mcp.tool()
def operation_name(
    user_id: str,  # REQUIRED - from JWT
    # Your domain parameters here
    resource_id: Optional[str] = None,
    filters: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    limit: int = 50,
    offset: int = 0
) -> dict:
    """
    Clear description of what this operation does.

    Args:
        user_id: User ID from JWT (automatically provided)
        resource_id: Identifier for specific resource (if applicable)
        filters: Key-value pairs for filtering results
        data: Data payload for create/update operations
        limit: Maximum number of results to return
        offset: Pagination offset

    Returns:
        dict: {
            "success": True,
            "data": {...},  # Operation result
            "count": 10     # Optional: result count
        } or {
            "success": False,
            "error": "Descriptive error message"
        }

    Examples:
        - "Get all resources"
        - "Find resources with specific filter"
        - "Create new resource with data"
    """
    # Implementation follows pattern below
```

**Universal Design Checklist:**
- [ ] All tools require `user_id` first parameter
- [ ] Parameters use natural language (not technical enums)
- [ ] Return structured `{success, data/error}` format
- [ ] Include comprehensive docstring with examples
- [ ] Handle all error cases gracefully
- [ ] Support pagination (limit/offset) where applicable
- [ ] Accept flexible filters/data parameters

### **Step 3: Pattern-Based Implementation**
**Choose your architecture pattern:**

#### **Pattern A: Single-File Server** (Recommended for simplicity)
```python
# mcp_server.py
from mcp.server.fastmcp import FastMCP
from typing import Optional, Dict, Any, List
import your_resource_module  # Your actual resource access

# 1. Server setup
mcp = FastMCP("YourResourceService")

# 2. Resource access layer (your business logic)
def get_resource_service():
    """
    Returns your service layer that handles all business logic.
    This separates MCP interface from implementation.
    """
    return YourResourceService()

# 3. Universal tool patterns
@mcp.tool()
def list_resources(
    user_id: str,
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 50,
    offset: int = 0
) -> dict:
    """List resources with optional filtering."""
    service = get_resource_service()
    try:
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

@mcp.tool()
def get_resource(
    user_id: str,
    resource_id: str
) -> dict:
    """Get specific resource by ID."""
    service = get_resource_service()
    try:
        result = service.get(user_id, resource_id)
        if result:
            return {"success": True, "data": result}
        return {"success": False, "error": "Resource not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def create_resource(
    user_id: str,
    data: Dict[str, Any]
) -> dict:
    """Create new resource."""
    service = get_resource_service()
    try:
        result = service.create(user_id, data)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def update_resource(
    user_id: str,
    resource_id: str,
    data: Dict[str, Any]
) -> dict:
    """Update existing resource."""
    service = get_resource_service()
    try:
        result = service.update(user_id, resource_id, data)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def delete_resource(
    user_id: str,
    resource_id: str
) -> dict:
    """Delete resource."""
    service = get_resource_service()
    try:
        success = service.delete(user_id, resource_id)
        return {"success": success, "deleted": success}
    except Exception as e:
        return {"success": False, "error": str(e)}

# 4. Main execution
if __name__ == "__main__":
    mcp.run(transport="stdio")
```

#### **Pattern B: Multi-File Modular** (For complex applications)
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

### **Step 4: Agent Integration Pattern**
**Universal integration approach:**
```python
# agents.py
from agents import Agent, Runner
from agents.mcp import MCPServerStdio
# Create agent with generic instructions
agent = Agent(
    name="ResourceAgent",
    instructions="""You have access to tools for managing resources.
    - User ID is known from authentication
    - Use tools naturally with plain language
    - Explain errors clearly and suggest fixes
    - Handle pagination for large result sets
    - Ask for clarification if parameters are unclear
    """,
    model="xiami:mimo-v2-flash",
    mcp_servers=[]  # Will be populated dynamically
)

async def run_agents(user_input: str, user_id: str) -> dict:
    """
    Universal agent runner for MCP integration.

    Args:
        user_input: Natural language request
        user_id: User ID from JWT

    Returns:
        dict: {
            "response": "Agent output",
            "agent_used": "Agent name",
            "tools_used": ["tool1", "tool2"]
        }
    """
    # Create fresh server per request
    server = MCPServerStdio(
        params={
            "command": "uv",
            "args": ["run", "mcp_server.py"]
        },
        client_session_timeout_seconds=60
    )

    agent.mcp_servers = [server]

    try:
        await server.connect()
        # Inject user context
        enhanced_input = f"[Authenticated as user: {user_id}] {user_input}"
        result = await Runner.run(agent, enhanced_input)

        return {
            "response": result.final_output,
            "agent_used": result.last_agent.name,
            "tools_used": [t.name for t in result.used_tools] if hasattr(result, 'used_tools') else []
        }
    finally:
        await server.cleanup()
        agent.mcp_servers = []
```

### **Step 5: FastAPI Endpoint Pattern**
**Universal endpoint structure:**
```python
# main.py
from fastapi import FastAPI, Depends, Header, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

class ChatRequest(BaseModel):
    message: str

# Universal authentication dependency
async def get_user_id(authorization: str = Header(...)) -> str:
    """
    Extract user_id from JWT token.
    Works with any JWT provider (Better Auth, Auth0, custom).
    """
    try:
        token = authorization.replace("Bearer ", "")

        # Development bypass
        if token.endswith('.bypass-signature'):
            return decode_bypass_token(token)

        # Production validation
        payload = await verify_token(token)
        return get_user_id_from_token(payload)

    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {e}")

@app.post("/api/agents/chat")
async def chat(
    request: ChatRequest,
    user_id: str = Depends(get_user_id)
):
    """
    Universal MCP integration endpoint.

    Request:
        POST /api/agents/chat
        Authorization: Bearer <jwt_token>
        {"message": "Your natural language request"}

    Response:
        {
            "success": True,
            "response": "Agent response",
            "agent_used": "...",
            "tools_used": [...]
        }
    """
    try:
        result = await run_agents(request.message, user_id)
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

## 🎨 **Universal Pattern Reference**

### **Pattern: Database Operations**
```python
# Service Layer Pattern
class DatabaseService:
    def __init__(self, session):
        self.session = session

    def list(self, user_id: str, filters: dict, limit: int, offset: int):
        query = self.session.query(Model).filter(Model.user_id == user_id)

        # Apply filters dynamically
        for key, value in filters.items():
            if hasattr(Model, key):
                query = query.filter(getattr(Model, key) == value)

        total = query.count()
        items = query.limit(limit).offset(offset).all()

        return {
            "items": [item.to_dict() for item in items],
            "count": total
        }

    def get(self, user_id: str, resource_id: str):
        return self.session.query(Model).filter(
            Model.user_id == user_id,
            Model.id == resource_id
        ).first()

    def create(self, user_id: str, data: dict):
        item = Model(user_id=user_id, **data)
        self.session.add(item)
        self.session.commit()
        return item.to_dict()

    def update(self, user_id: str, resource_id: str, data: dict):
        item = self.get(user_id, resource_id)
        if not item:
            raise ValueError("Resource not found")

        for key, value in data.items():
            if hasattr(item, key):
                setattr(item, key, value)

        self.session.commit()
        return item.to_dict()

    def delete(self, user_id: str, resource_id: str):
        item = self.get(user_id, resource_id)
        if item:
            self.session.delete(item)
            self.session.commit()
            return True
        return False
```

### **Pattern: API Integration**
```python
# Service Layer Pattern
class APIService:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def get_user_credentials(self, user_id: str) -> dict:
        """Retrieve user-specific API credentials."""
        # Your implementation: database lookup, secrets manager, etc.
        return {"token": "user-api-token"}

    def call_api(
        self,
        user_id: str,
        endpoint: str,
        method: str = "GET",
        data: Optional[dict] = None
    ) -> dict:
        """Universal API caller with user context."""
        creds = self.get_user_credentials(user_id)

        import httpx
        response = httpx.request(
            method=method,
            url=f"{self.base_url}/{endpoint}",
            headers={"Authorization": f"Bearer {creds['token']}"},
            json=data,
            timeout=30.0
        )

        return {
            "status": response.status_code,
            "data": response.json(),
            "headers": dict(response.headers)
        }
```

### **Pattern: File Operations**
```python
# Service Layer Pattern
class FileService:
    def __init__(self, base_path: str = "/data"):
        self.base_path = base_path

    def get_user_dir(self, user_id: str) -> str:
        """Get user's directory path."""
        return f"{self.base_path}/users/{user_id}"

    def validate_path(self, user_dir: str, path: str) -> str:
        """Security: Prevent directory traversal."""
        import os
        full_path = os.path.abspath(os.path.join(user_dir, path))
        if not full_path.startswith(os.path.abspath(user_dir)):
            raise ValueError("Invalid path - directory traversal detected")
        return full_path

    def list_files(self, user_id: str, path: str = "") -> dict:
        """List files in user directory."""
        import os
        user_dir = self.get_user_dir(user_id)
        full_path = self.validate_path(user_dir, path or ".")

        try:
            items = []
            for item in os.listdir(full_path):
                item_path = os.path.join(full_path, item)
                items.append({
                    "name": item,
                    "type": "directory" if os.path.isdir(item_path) else "file",
                    "size": os.path.getsize(item_path) if os.path.isfile(item_path) else 0
                })
            return {"files": items}
        except Exception as e:
            raise Exception(f"Failed to list files: {e}")

    def read_file(self, user_id: str, path: str) -> dict:
        """Read file content."""
        import os
        user_dir = self.get_user_dir(user_id)
        full_path = self.validate_path(user_dir, path)

        if not os.path.isfile(full_path):
            raise ValueError("File not found")

        with open(full_path, 'r') as f:
            return {"content": f.read()}

    def write_file(self, user_id: str, path: str, content: str) -> dict:
        """Write file content."""
        import os
        user_dir = self.get_user_dir(user_id)
        full_path = self.validate_path(user_dir, path)

        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, 'w') as f:
            f.write(content)

        return {"message": "File written successfully"}
```

## 🔐 **Universal Security Protocol**

### **Authentication Flow**
```
1. HTTP Request → JWT Token in Header
2. FastAPI Dependency → Extract & Validate Token
3. Token Validation → Verify signature & expiration
4. User ID Extraction → Get user identifier
5. Agent Integration → Inject into context
6. Tool Execution → user_id parameter
7. Service Layer → Filter by user_id
8. Response → Return user-scoped data
```

### **Validation Layers (Defense in Depth)**
```python
# Layer 1: Token validation
async def verify_token(token: str) -> dict:
    """Validate JWT token."""
    if token.endswith('.bypass-signature'):
        return decode_bypass_token(token)  # Dev only

    # Production: Use JWKS client
    jwks_client = get_jwks_client()
    signing_key = jwks_client.get_signing_key_from_jwt(token)

    return pyjwt.decode(
        token,
        signing_key.key,
        algorithms=["EdDSA", "ES256", "RS256"],
        audience=BETTER_AUTH_URL,
        issuer=BETTER_AUTH_URL,
    )

# Layer 2: User ID extraction
def get_user_id_from_token(payload: dict) -> str:
    """Extract user_id from token payload."""
    return payload.get('sub') or payload.get('id')

# Layer 3: Tool parameter (automatic)
@mcp.tool()
def your_tool(user_id: str, ...):  # user_id required

# Layer 4: Service filtering
def list_items(self, user_id: str, ...):
    return session.query(Model).filter(
        Model.user_id == user_id,  # User isolation
        ...
    ).all()

# Layer 5: Path validation (for file operations)
def validate_path(self, user_dir: str, path: str):
    full_path = os.path.abspath(os.path.join(user_dir, path))
    if not full_path.startswith(os.path.abspath(user_dir)):
        raise ValueError("Invalid path")
    return full_path
```

## 🧪 **Universal Testing Patterns**

### **Test 1: User Isolation**
```python
async def test_user_isolation():
    """Verify users cannot access each other's data."""
    # User 1 creates resource
    result1 = await run_agents("Create resource: User 1 data", "user-1")
    resource_id = extract_id(result1)

    # User 2 tries to access User 1's resource
    result2 = await run_agents(f"Get resource {resource_id}", "user-2")

    # Should fail or return empty
    assert "not found" in result2["response"].lower() or \
           result2["response"] == "[]"
```

### **Test 2: Error Resilience**
```python
async def test_error_handling():
    """Verify graceful error handling."""
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

### **Test 3: Resource Cleanup**
```python
async def test_resource_cleanup():
    """Verify no resource leaks."""
    import asyncio
    initial_tasks = len(asyncio.all_tasks())

    # Make multiple requests
    for _ in range(10):
        await run_agents("Create resource: test", "user-1")

    # Verify cleanup
    final_tasks = len(asyncio.all_tasks())
    assert final_tasks <= initial_tasks + 2  # Allow small overhead
```

## 🎯 **Quick Start Template**

### **Step 1: Create Your Service**
```python
# your_service.py
class YourResourceService:
    def __init__(self, session_or_client):
        self.client = session_or_client

    def list(self, user_id: str, filters: dict, limit: int, offset: int):
        # Your implementation
        pass

    def get(self, user_id: str, resource_id: str):
        # Your implementation
        pass

    def create(self, user_id: str, data: dict):
        # Your implementation
        pass

    def update(self, user_id: str, resource_id: str, data: dict):
        # Your implementation
        pass

    def delete(self, user_id: str, resource_id: str):
        # Your implementation
        pass
```

### **Step 2: Create MCP Server**
```python
# mcp_server.py
from mcp.server.fastmcp import FastMCP
from your_service import YourResourceService

mcp = FastMCP("YourService")

def get_service():
    return YourResourceService(your_connection)

@mcp.tool()
def list_resources(user_id: str, filters: dict = None, limit: int = 50, offset: int = 0) -> dict:
    """List resources with filtering."""
    service = get_service()
    try:
        result = service.list(user_id, filters or {}, limit, offset)
        return {"success": True, "data": result["items"], "count": result["count"]}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Add more tools following same pattern...

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

### **Step 3: Test Directly**
```bash
uv run python mcp_server.py
```

### **Step 4: Integrate with FastAPI**
```python
# main.py
from fastapi import FastAPI, Depends, Header
from agents import run_agents

app = FastAPI()

async def get_user_id(authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "")
    payload = await verify_token(token)
    return get_user_id_from_token(payload)

@app.post("/api/agents/chat")
async def chat(message: str, user_id: str = Depends(get_user_id)):
    return await run_agents(message, user_id)
```

This protocol ensures you can create MCP integration for **any** resource type while maintaining security, consistency, and scalability.