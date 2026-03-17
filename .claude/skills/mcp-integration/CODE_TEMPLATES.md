# MCP Pattern Reference Library

> **Pattern-based examples for common MCP integration scenarios**

## 🎯 **Pattern Library Philosophy**

This document provides **pattern examples** for common scenarios. Each example shows the **pattern structure** that you must adapt to your specific application.

**Important**: These are **illustrative patterns**, not **copy-paste templates**. You must replace:
- `YourModel` → Your actual data model
- `YourService` → Your actual service class
- `your_operation()` → Your actual business logic
- Parameter names → Your actual parameters

## 🏗️ **Server Setup Patterns**

### **Pattern 1: Basic Server Setup**
```python
# mcp_server.py
from mcp.server.fastmcp import FastMCP
from typing import Optional, List, Dict, Any

# Create server instance
mcp = FastMCP("YourServiceName")

# Your service setup (implement this)
def get_service():
    # Return your service instance
    # Example: return YourService(engine)
    pass

# Tools go here (see patterns below)

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

**When to use**: All applications start here

### **Pattern 2: Server with Configuration**
```python
# mcp_server.py
from mcp.server.fastmcp import FastMCP
from typing import Optional
import os

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
BASE_API_URL = os.getenv("BASE_API_URL", "https://api.example.com")

# Server
mcp = FastMCP("YourServiceName")

# Service with config
def get_service():
    from your_service import YourService
    return YourService(DATABASE_URL, BASE_API_URL)

# Tools...

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

**When to use**: Applications needing environment configuration

## 🔧 **Tool Pattern Categories**

### **Category 1: Database Operations**

#### **Pattern: Create Operation**
```python
@mcp.tool()
def create_resource(
    user_id: str,  # REQUIRED - from JWT
    name: str,
    description: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> dict:
    """
    Create a new resource for the user.

    Args:
        user_id: User ID from JWT (auto-provided)
        name: Name/identifier for the resource
        description: Optional description
        metadata: Optional additional data

    Returns:
        dict: {"success": True, "data": {...}} or {"success": False, "error": "..."}
    """
    service = get_service()
    try:
        result = service.create(
            user_id=user_id,
            name=name,
            description=description,
            metadata=metadata
        )
        return {"success": True, "data": result.to_dict()}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

**Pattern structure**:
- User ID first parameter
- Domain-specific parameters
- Optional parameters with defaults
- Service delegation
- Structured response
- Error handling

#### **Pattern: Read/Query Operation**
```python
@mcp.tool()
def list_resources(
    user_id: str,
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> dict:
    """
    List resources with filtering and pagination.

    Args:
        user_id: User ID from JWT
        status: Filter by status
        search: Search in name/description
        limit: Max results (default 50)
        offset: Pagination offset

    Returns:
        dict: {"success": True, "data": [...], "count": 10}
    """
    service = get_service()
    try:
        results = service.list(
            user_id=user_id,
            status=status,
            search=search,
            limit=limit,
            offset=offset
        )
        return {
            "success": True,
            "data": [r.to_dict() for r in results],
            "count": len(results)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
```

**Pattern structure**:
- User ID first
- Filter parameters (optional)
- Pagination parameters
- Service delegation
- List conversion
- Count metadata

#### **Pattern: Get Single Resource**
```python
@mcp.tool()
def get_resource(user_id: str, resource_id: str) -> dict:
    """
    Get a specific resource by ID.

    Args:
        user_id: User ID from JWT
        resource_id: ID of the resource

    Returns:
        dict: {"success": True, "data": {...}} or {"success": False, "error": "Not found"}
    """
    service = get_service()
    try:
        result = service.get(user_id, resource_id)
        if result:
            return {"success": True, "data": result.to_dict()}
        return {"success": False, "error": "Resource not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

**Pattern structure**:
- User ID + resource ID
- Handle "not found" case
- Return specific error message

#### **Pattern: Update Operation**
```python
@mcp.tool()
def update_resource(
    user_id: str,
    resource_id: str,
    **fields
) -> dict:
    """
    Update resource fields.

    Args:
        user_id: User ID from JWT
        resource_id: ID of the resource
        **fields: Fields to update (name, description, etc.)

    Returns:
        dict: {"success": True, "data": {...}} or {"success": False, "error": "..."}
    """
    service = get_service()
    try:
        result = service.update(user_id, resource_id, fields)
        return {"success": True, "data": result.to_dict()}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

**Pattern structure**:
- User ID + resource ID
- Flexible field updates via **fields
- Service handles validation
- Return updated resource

#### **Pattern: Delete Operation**
```python
@mcp.tool()
def delete_resource(user_id: str, resource_id: str) -> dict:
    """
    Delete a resource.

    Args:
        user_id: User ID from JWT
        resource_id: ID of the resource

    Returns:
        dict: {"success": True, "deleted": True} or {"success": False, "error": "..."}
    """
    service = get_service()
    try:
        success = service.delete(user_id, resource_id)
        return {"success": success, "deleted": success}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

**Pattern structure**:
- User ID + resource ID
- Boolean success return
- Consistent delete response

### **Category 2: API Integration Patterns**

#### **Pattern: API Call with User Context**
```python
@mcp.tool()
def call_api(
    user_id: str,
    endpoint: str,
    method: str = "GET",
    data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None
) -> dict:
    """
    Call external API with user credentials.

    Args:
        user_id: User ID from JWT
        endpoint: API endpoint path
        method: HTTP method (GET, POST, PUT, DELETE)
        data: Request body for POST/PUT
        headers: Additional headers

    Returns:
        dict: {"success": True, "status": 200, "data": {...}} or {"success": False, "error": "..."}
    """
    service = get_service()
    try:
        result = service.api_call(
            user_id=user_id,
            endpoint=endpoint,
            method=method,
            data=data,
            headers=headers
        )
        return {
            "success": True,
            "status": result.get("status", 200),
            "data": result.get("data")
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
```

**Pattern structure**:
- User ID for credential lookup
- Flexible API parameters
- Service handles auth and request
- Return status + data

#### **Pattern: Batch API Operations**
```python
@mcp.tool()
def batch_api_call(
    user_id: str,
    operations: List[Dict[str, Any]]
) -> dict:
    """
    Execute multiple API calls in batch.

    Args:
        user_id: User ID from JWT
        operations: List of operation dicts with endpoint/method/data

    Returns:
        dict: {"success": True, "results": [...]} or {"success": False, "error": "..."}
    """
    service = get_service()
    try:
        results = []
        for op in operations:
            result = service.api_call(
                user_id=user_id,
                endpoint=op["endpoint"],
                method=op.get("method", "GET"),
                data=op.get("data")
            )
            results.append(result)

        return {"success": True, "results": results}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

**Pattern structure**:
- User ID first
- List of operations
- Process each operation
- Return aggregated results

### **Category 3: File System Patterns**

#### **Pattern: File Management**
```python
@mcp.tool()
def manage_files(
    user_id: str,
    action: str,  # "list", "read", "write", "delete"
    path: str,
    content: Optional[str] = None,
    overwrite: bool = False
) -> dict:
    """
    Manage user files with security validation.

    Args:
        user_id: User ID from JWT
        action: Operation to perform
        path: Relative path within user directory
        content: Content for write operations
        overwrite: Whether to overwrite existing files

    Returns:
        dict: {"success": True, "data": {...}} or {"success": False, "error": "..."}
    """
    service = get_service()
    try:
        if action == "list":
            files = service.list_files(user_id, path)
            return {"success": True, "files": files}

        elif action == "read":
            content = service.read_file(user_id, path)
            return {"success": True, "content": content}

        elif action == "write":
            service.write_file(user_id, path, content or "", overwrite)
            return {"success": True, "message": "File written"}

        elif action == "delete":
            service.delete_file(user_id, path)
            return {"success": True, "message": "File deleted"}

        else:
            return {"success": False, "error": "Invalid action"}

    except Exception as e:
        return {"success": False, "error": str(e)}
```

**Pattern structure**:
- User ID first
- Action parameter for operation type
- Path validation in service
- Content for write operations
- Action-specific responses

#### **Pattern: File Upload/Download**
```python
@mcp.tool()
def upload_file(
    user_id: str,
    filename: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None
) -> dict:
    """
    Upload a file with metadata.

    Args:
        user_id: User ID from JWT
        filename: Name for the file
        content: File content (base64 or text)
        metadata: Additional file metadata

    Returns:
        dict: {"success": True, "file_id": "...", "size": 1234}
    """
    service = get_service()
    try:
        result = service.upload(user_id, filename, content, metadata)
        return {
            "success": True,
            "file_id": result["id"],
            "size": result["size"],
            "url": result.get("url")
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def download_file(user_id: str, file_id: str) -> dict:
    """
    Download a file by ID.

    Args:
        user_id: User ID from JWT
        file_id: ID of the file

    Returns:
        dict: {"success": True, "content": "...", "filename": "..."}
    """
    service = get_service()
    try:
        result = service.download(user_id, file_id)
        return {
            "success": True,
            "content": result["content"],
            "filename": result["filename"]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
```

**Pattern structure**:
- User ID first
- File identification (name or ID)
- Content handling
- Metadata support
- Return file details

### **Category 4: External Service Patterns**

#### **Pattern: Email Service**
```python
@mcp.tool()
def send_email(
    user_id: str,
    to: str,
    subject: str,
    body: str,
    cc: Optional[List[str]] = None,
    attachments: Optional[List[str]] = None
) -> dict:
    """
    Send email on behalf of user.

    Args:
        user_id: User ID from JWT
        to: Recipient email
        subject: Email subject
        body: Email body (text or HTML)
        cc: Optional CC recipients
        attachments: Optional file paths

    Returns:
        dict: {"success": True, "message_id": "..."} or {"success": False, "error": "..."}
    """
    service = get_service()
    try:
        result = service.send_email(
            user_id=user_id,
            to=to,
            subject=subject,
            body=body,
            cc=cc,
            attachments=attachments
        )
        return {"success": True, "message_id": result["id"]}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

**Pattern structure**:
- User ID for sender identity
- Standard email parameters
- Service handles authentication
- Return message identifier

#### **Pattern: Payment Processing**
```python
@mcp.tool()
def create_payment(
    user_id: str,
    amount: float,
    currency: str,
    description: str,
    metadata: Optional[Dict[str, Any]] = None
) -> dict:
    """
    Create a payment for the user.

    Args:
        user_id: User ID from JWT
        amount: Payment amount
        currency: Currency code (USD, EUR, etc.)
        description: Payment description
        metadata: Additional payment data

    Returns:
        dict: {"success": True, "payment_id": "...", "status": "..."}
    """
    service = get_service()
    try:
        result = service.create_payment(
            user_id=user_id,
            amount=amount,
            currency=currency,
            description=description,
            metadata=metadata
        )
        return {
            "success": True,
            "payment_id": result["id"],
            "status": result["status"],
            "url": result.get("url")  # Payment URL if needed
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
```

**Pattern structure**:
- User ID for customer identity
- Payment details
- Service handles payment provider
- Return payment status

## 🤖 **Agent Integration Patterns**

### **Pattern 1: Single Agent + Single Server**
```python
# agents.py
from agents import Agent, Runner
from agents.mcp import MCPServerStdio
# Agent definition
main_agent = Agent(
    name="MainAgent",
    instructions="""You are a helpful assistant with access to tools.
    - User ID is known from authentication
    - Use tools naturally in conversation
    - Explain errors clearly
    """,
    model="xiami:mimo-v2-flash",
    mcp_servers=[]  # Will be populated dynamically
)

async def run_agents(user_input: str, user_id: str) -> dict:
    """
    Run agent with MCP server for single request.

    Args:
        user_input: User message
        user_id: User ID from JWT

    Returns:
        dict: {"response": "...", "agent_used": "...", "tools_used": [...]}
    """
    # Create server
    server = MCPServerStdio(
        params={
            "command": "uv",
            "args": ["run", "mcp_server.py"]
        },
        client_session_timeout_seconds=60
    )

    # Add to agent
    main_agent.mcp_servers = [server]

    try:
        # Connect
        await server.connect()

        # Inject context
        enhanced_input = f"[Authenticated as user: {user_id}] {user_input}"

        # Run
        result = await Runner.run(main_agent, enhanced_input)

        # Parse result
        return {
            "response": result.final_output,
            "agent_used": result.last_agent.name,
            "tools_used": [t.name for t in result.used_tools] if hasattr(result, 'used_tools') else []
        }

    finally:
        # Cleanup
        await server.cleanup()
        main_agent.mcp_servers = []
```

**Pattern structure**:
- Agent definition with instructions
- Dynamic server creation
- Context injection
- Try/finally cleanup
- Result parsing

### **Pattern 2: Multi-Agent with Handoffs**
```python
# agents.py
from agents import Agent, Runner
from agents.mcp import MCPServerStdio
# Create agents
router_agent = Agent(
    name="Router",
    instructions="""Route requests to appropriate specialist.
    - Database operations → DB_Specialist
    - API calls → API_Specialist
    - File operations → File_Specialist
    """,
    model="xiami:mimo-v2-flash",
    mcp_servers=[]
)

db_agent = Agent(
    name="DB_Specialist",
    instructions="Handle all database operations",
    model="xiami:mimo-v2-flash",
    mcp_servers=[]
)

api_agent = Agent(
    name="API_Specialist",
    instructions="Handle all API integrations",
    model="xiami:mimo-v2-flash",
    mcp_servers=[]
)

file_agent = Agent(
    name="File_Specialist",
    instructions="Handle all file operations",
    model="xiami:mimo-v2-flash",
    mcp_servers=[]
)

# Set up handoffs
router_agent.handoffs = [db_agent, api_agent, file_agent]

async def run_agents(user_input: str, user_id: str) -> dict:
    """
    Run multi-agent system with multiple MCP servers.

    Args:
        user_input: User message
        user_id: User ID from JWT

    Returns:
        dict: {"response": "...", "agent_used": "...", "tools_used": [...]}
    """
    # Create multiple servers
    servers = {
        "db": MCPServerStdio(params={"command": "uv", "args": ["run", "db_server.py"]}),
        "api": MCPServerStdio(params={"command": "uv", "args": ["run", "api_server.py"]}),
        "file": MCPServerStdio(params={"command": "uv", "args": ["run", "file_server.py"]})
    }

    # Assign servers to agents
    db_agent.mcp_servers = [servers["db"]]
    api_agent.mcp_servers = [servers["api"]]
    file_agent.mcp_servers = [servers["file"]]

    try:
        # Connect all servers
        for server in servers.values():
            await server.connect()

        # Inject context
        enhanced_input = f"[User: {user_id}] {user_input}"

        # Run from router
        result = await Runner.run(router_agent, enhanced_input)

        return {
            "response": result.final_output,
            "agent_used": result.last_agent.name,
            "tools_used": [t.name for t in result.used_tools] if hasattr(result, 'used_tools') else []
        }

    finally:
        # Cleanup all servers
        for server in servers.values():
            await server.cleanup()

        # Reset agent servers
        router_agent.mcp_servers = []
        db_agent.mcp_servers = []
        api_agent.mcp_servers = []
        file_agent.mcp_servers = []
```

**Pattern structure**:
- Multiple specialized agents
- Router for handoffs
- Multiple servers
- Server-to-agent assignment
- Coordinated cleanup

## 🔐 **Authentication Patterns**

### **Pattern 1: JWT Validation**
```python
# auth/jwt.py
import jwt
from jwt import PyJWKClient
from typing import Dict, Optional

# Configuration
BETTER_AUTH_URL = "http://localhost:3000"
BETTER_AUTH_SECRET = os.getenv("BETTER_AUTH_SECRET", "dev-secret")

def get_jwks_client():
    """Create JWKS client for Better Auth."""
    jwks_url = f"{BETTER_AUTH_URL}/api/auth/jwks"
    return PyJWKClient(jwks_url)

def decode_bypass_token(token: str) -> Dict:
    """Decode development bypass token."""
    parts = token.split('.')
    if len(parts) != 3:
        raise ValueError("Invalid token format")

    payload_json = parts[1]
    padding = 4 - len(payload_json) % 4
    if padding != 4:
        payload_json += '=' * padding

    import base64, json
    payload_bytes = base64.b64decode(payload_json)
    return json.loads(payload_bytes)

async def verify_token(token: str) -> Dict:
    """
    Verify JWT token from Better Auth.

    Args:
        token: JWT token string

    Returns:
        Decoded payload

    Raises:
        Exception: If token invalid
    """
    # Check for bypass token
    if token.endswith('.bypass-signature'):
        return decode_bypass_token(token)

    # Production: Validate with JWKS
    jwks_client = get_jwks_client()
    signing_key = jwks_client.get_signing_key_from_jwt(token)

    payload = jwt.decode(
        token,
        signing_key.key,
        algorithms=["EdDSA", "ES256", "RS256"],
        audience=BETTER_AUTH_URL,
        issuer=BETTER_AUTH_URL,
    )

    return payload

def get_user_id_from_token(payload: Dict) -> str:
    """
    Extract user ID from JWT payload.

    Better Auth typically uses 'sub' or custom 'id' field.
    """
    return payload.get('sub') or payload.get('id') or payload.get('userId')

def create_bypass_token(user_id: str) -> str:
    """
    Create development bypass token.

    ⚠️  FOR DEVELOPMENT ONLY
    """
    import base64, json
    header = base64.b64encode(
        json.dumps({"alg": "HS256", "typ": "JWT"}).encode()
    ).decode().rstrip('=')

    payload = base64.b64encode(
        json.dumps({
            "sub": user_id,
            "email": "dev@example.com",
            "name": "Dev User",
            "exp": 9999999999,
            "iat": 1234567890
        }).encode()
    ).decode().rstrip('=')

    return f"{header}.{payload}.bypass-signature"
```

**Pattern structure**:
- JWKS client setup
- Bypass for development
- Token validation
- User ID extraction
- Token creation for testing

### **Pattern 2: FastAPI Auth Dependency**
```python
# dependencies.py
from fastapi import Header, HTTPException
from typing import Optional

async def get_user_id_dependency(
    authorization: Optional[str] = Header(None)
) -> str:
    """FastAPI dependency to get user_id from JWT."""
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization header")

    try:
        token = authorization.replace("Bearer ", "")
        from auth.jwt import verify_token, get_user_id_from_token

        payload = await verify_token(token)
        return get_user_id_from_token(payload)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

# Usage in endpoint
@app.post("/api/protected")
async def protected_endpoint(
    data: dict,
    user_id: str = Depends(get_user_id_dependency)
):
    return {"user_id": user_id, "data": data}
```

**Pattern structure**:
- Header extraction
- Token validation
- User ID extraction
- Error handling
- FastAPI dependency

## 🧪 **Testing Patterns**

### **Pattern 1: Direct Tool Test**
```python
# test_tools.py
import asyncio
from your_mcp_server import your_tool

async def test_tool_direct():
    """Test tool function directly."""
    result = await your_tool(
        user_id="test-user-123",
        name="Test Resource",
        description="Test description"
    )

    assert result["success"] == True
    assert "data" in result
    assert "id" in result["data"]

async def test_tool_error():
    """Test tool error handling."""
    result = await your_tool(
        user_id="test-user-123",
        # Missing required parameters
    )

    assert result["success"] == False
    assert "error" in result
```

**Pattern structure**:
- Direct function calls
- Success case assertion
- Error case assertion
- No agent overhead

### **Pattern 2: Full Integration Test**
```python
# test_integration.py
import asyncio
from agents import run_agents

async def test_full_flow():
    """Test complete agent + MCP flow."""
    test_cases = [
        ("Create resource: Test Item", "user-1"),
        ("List all resources", "user-1"),
        ("Get resource with ID 123", "user-1"),
        ("Update resource 123 with new data", "user-1"),
        ("Delete resource 456", "user-1"),
    ]

    for message, user_id in test_cases:
        print(f"\nTesting: {message}")
        result = await run_agents(message, user_id)

        assert "response" in result
        assert result["agent_used"] in ["MainAgent", "DB_Specialist", "API_Specialist"]
        print(f"✅ Success: {result['response']}")

if __name__ == "__main__":
    asyncio.run(test_full_flow())
```

**Pattern structure**:
- Multiple test cases
- Full agent flow
- Response validation
- Agent routing verification

### **Pattern 3: Security Test**
```python
# test_security.py
import asyncio
from agents import run_agents

async def test_user_isolation():
    """Verify users cannot access each other's data."""
    # User 1 creates resource
    result1 = await run_agents("Create resource: User 1 Data", "user-1")
    assert result1["success"] == True

    # Extract resource ID from response
    # (Implementation depends on your response format)
    resource_id = extract_id(result1["response"])

    # User 2 tries to access User 1's resource
    result2 = await run_agents(f"Get resource {resource_id}", "user-2")

    # Should fail or return empty
    assert "not found" in result2["response"].lower() or \
           "error" in result2["response"].lower()

async def test_path_traversal():
    """Test path traversal protection."""
    result = await run_agents("Read file: ../secret.txt", "user-1")
    assert "error" in result["response"].lower()

async def test_sql_injection():
    """Test SQL injection protection."""
    result = await run_agents("List resources: ' OR '1'='1", "user-1")
    # Should be handled gracefully
    assert result["success"] == False or "error" in result["response"].lower()
```

**Pattern structure**:
- User isolation tests
- Path validation tests
- Injection attack tests
- Security boundary verification

### **Pattern 4: Performance Test**
```python
# test_performance.py
import asyncio
from agents import run_agents

async def test_resource_cleanup():
    """Verify no resource leaks."""
    initial_tasks = len(asyncio.all_tasks())

    # Make multiple requests
    for i in range(10):
        await run_agents(f"Create resource: Test {i}", "user-1")

    # Wait a moment for cleanup
    await asyncio.sleep(0.1)

    # Check task count
    final_tasks = len(asyncio.all_tasks())
    assert final_tasks <= initial_tasks + 2

async def test_concurrent_requests():
    """Test handling concurrent requests."""
    user_ids = [f"user-{i}" for i in range(5)]

    # Run concurrent requests
    tasks = [
        run_agents("Create resource: Concurrent", user_id)
        for user_id in user_ids
    ]

    results = await asyncio.gather(*tasks)

    # All should succeed
    for result in results:
        assert result["success"] == True
```

**Pattern structure**:
- Task count verification
- Concurrent request handling
- Resource leak detection
- Performance under load

## 🎯 **Pattern Selection Guide**

### **When to use each pattern:**

**Server Patterns:**
- **Basic**: All applications start here
- **Config**: Need environment variables

**Tool Patterns:**
- **Database CRUD**: Standard data operations
- **API Integration**: External service calls
- **File Operations**: Document management
- **External Services**: Email, payments, etc.

**Integration Patterns:**
- **Single Agent**: Most applications
- **Multi-Agent**: Complex systems with multiple domains

**Authentication:**
- **JWT Validation**: Production systems
- **FastAPI Dependency**: Backend endpoints

**Testing:**
- **Direct Tool**: Unit testing
- **Full Integration**: System testing
- **Security**: Security verification
- **Performance**: Resource management

---

**Remember**: These patterns show **structure and flow**. You must implement them with your:
- Actual data models
- Real business logic
- Specific error types
- Custom parameters
- Application-specific validation

Use these patterns as **architectural guides**, not **code templates**.