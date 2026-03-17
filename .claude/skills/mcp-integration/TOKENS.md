# MCP Integration Tokens & Requirements

## 📦 Required Packages

### Core Dependencies (Universal)
```toml
# OpenAI Agents SDK (with MCP support)
openai-agents>=0.6.5

# FastAPI & Web Framework
fastapi>=0.128.0
uvicorn>=0.40.0

# Authentication
pyjwt>=2.10.0
cryptography>=44.0.0

# HTTP & Utilities
httpx>=0.28.1
python-dotenv>=1.0.0
```

### Resource-Specific Dependencies (Choose as needed)
```toml
# Database (if using databases)
sqlmodel>=0.0.31
asyncpg>=0.31.0          # Async PostgreSQL
psycopg2-binary>=2.9.11  # Sync PostgreSQL

# File operations (if using file system)
# No additional packages needed (use standard library)

# External APIs (if using API integration)
# httpx already included above

# Additional services (if needed)
# Add specific packages for your resource type
```

### MCP Package
```bash
# Install MCP server capabilities
uv add mcp
# OR (if using OpenAI Agents SDK bundled)
# MCP is included in openai-agents
```

## 🔐 Environment Variables

### Required (Universal)
```env
# AI Service (for agent)
XIAOMI_API_KEY="your-xiaomi-key"
# OR
OPENAI_API_KEY="your-openai-key"

# CORS (for frontend access)
CORS_ORIGINS="http://localhost:3000,https://yourdomain.com"
```

### Resource-Specific (Choose as needed)
```env
# Database (if using)
DATABASE_URL="postgresql://user:pass@host:5432/dbname"

# Better Auth (JWT Validation - if using)
BETTER_AUTH_SECRET="your-secret-key"
BETTER_AUTH_URL="http://localhost:3000"

# Custom JWT (if using)
JWT_SECRET="your-secret"
JWT_ISSUER="your-issuer"

# API Integration (if using external APIs)
API_BASE_URL="https://api.example.com"
API_KEY="your-api-key"

# File System (if using)
BASE_DATA_PATH="/data"
```

### Optional (Development)
```env
# Enable bypass tokens (dev only)
AUTH_BYPASS=true

# Debug logging
DEBUG=true

# Development ports
BACKEND_PORT=8000
FRONTEND_PORT=3000
```

## 🛡️ Universal Security Patterns

### 1. JWT Token Validation (Universal)
```python
# Works with ANY JWT provider
async def verify_token(token: str) -> dict:
    """
    Validate JWT token from ANY provider.
    Supports: Better Auth, Auth0, custom, etc.
    """
    # Development bypass
    if token.endswith('.bypass-signature'):
        return decode_bypass_token(token)

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
```

### 2. User ID Extraction (Universal)
```python
def get_user_id_from_token(payload: dict) -> str:
    """
    Extract user_id from ANY JWT provider.
    Works with: Better Auth, Auth0, custom, etc.
    """
    # Try multiple common fields
    return (
        payload.get('sub') or
        payload.get('id') or
        payload.get('user_id') or
        payload.get('userId')
    )
```

### 3. Bypass Token (Development Only)
```python
def create_bypass_token(user_id: str) -> str:
    """
    Create development token for ANY resource testing.
    """
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

## 🎨 Universal Tool Design Patterns

### 1. User-Scoped Tools (MANDATORY for ANY resource)
```python
@mcp.tool()
def manage_resources(
    user_id: str,
    action: str,
    resource_type: str,
    **params
) -> dict:
    """
    Universal tool for ANY resource type.

    All tools MUST require user_id parameter from JWT.
    This works for: databases, APIs, files, services, hardware
    """
    service = get_service()
    try:
        result = service.execute(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            **params
        )
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### 2. Structured Responses (Universal)
```python
@mcp.tool()
def universal_operation(
    user_id: str,
    operation: str,
    **params
) -> dict:
    """
    Consistent response format for ANY resource operation.
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
        return {
            "success": False,
            "error": str(e)
        }
```

### 3. Tool Documentation (Universal)
```python
@mcp.tool()
def comprehensive_tool(
    user_id: str,
    operation: str,
    resource_type: str,
    identifier: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 50,
    offset: int = 0
) -> dict:
    """
    Universal tool with comprehensive documentation.

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
            - Services: "configurations", "settings"
        identifier: Resource ID for get/update/delete operations
        data: Data payload for create/update operations
        filters: Filter criteria for list operations
        limit: Maximum results to return (default 50)
        offset: Pagination offset (default 0)

    Returns:
        dict: {
            "success": True,
            "data": [...],  # Operation result
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

## 🏗️ Universal File Structure

### Single-File Pattern (Recommended for simplicity)
```
your_project/
├── mcp_server.py              # Main server with all tools
├── agents.py                  # Agent integration
├── main.py                    # FastAPI endpoint
├── your_service.py            # Your business logic
├── auth.py                    # JWT validation
├── tests/                     # Tests
│   └── test_integration.py
└── .env                       # Environment variables
```

### Multi-File Pattern (For complex applications)
```
your_project/
├── mcp_server/
│   ├── __init__.py
│   ├── server.py              # Main server setup
│   ├── tools/                 # Tool implementations
│   │   ├── __init__.py
│   │   ├── database_tools.py
│   │   ├── api_tools.py
│   │   └── file_tools.py
│   ├── services/              # Business logic
│   │   ├── __init__.py
│   │   ├── database_service.py
│   │   ├── api_service.py
│   │   └── file_service.py
│   └── models/                # Data models
│       ├── __init__.py
│       └── schemas.py
├── agents.py                  # Agent integration
├── main.py                    # FastAPI endpoint
├── auth.py                    # JWT utilities
├── tests/
│   ├── test_isolation.py
│   ├── test_errors.py
│   └── test_cleanup.py
└── .env
```

## 🔧 Universal Development Commands

### Setup (Any Resource Type)
```bash
# 1. Create project structure
mkdir your-mcp-project && cd your-mcp-project

# 2. Initialize with uv
uv init --package your_project

# 3. Add core dependencies
uv add openai-agents fastapi uvicorn pyjwt cryptography httpx python-dotenv

# 4. Add resource-specific dependencies (as needed)
uv add sqlmodel asyncpg  # For databases
# uv add ...            # For other resources

# 5. Add MCP
uv add mcp

# 6. Set up environment
cp .env.example .env
# Edit .env with your values
```

### Testing (Universal Patterns)
```bash
# Test MCP server directly
uv run python mcp_server.py

# Test with agent integration
uv run python test_integration.py

# Test user isolation
uv run python -m pytest tests/test_isolation.py

# Test error handling
uv run python -m pytest tests/test_errors.py

# Test resource cleanup
uv run python -m pytest tests/test_cleanup.py
```

### Running (Universal)
```bash
# Start backend
uv run uvicorn main:app --host 0.0.0.0 --port 8000

# Test endpoint (universal)
curl -X POST http://localhost:8000/api/agents/chat \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "List all resources"}'
```

## 📊 Universal Architecture Reference

### Complete Flow (ANY Resource)
```
User Request → JWT Token → Backend /api/agents/chat
    ↓
JWT Validation → Extract user_id (works with ANY provider)
    ↓
Dynamic MCP Server Creation → Connect
    ↓
Agent + Tools → Natural Language Processing
    ↓
MCP Tools → Your Service Layer → [Database | API | Files | Services]
    ↓
Response → Cleanup → Return to User
```

### Universal Tool Execution Flow
```
Natural Language → Agent → MCP Tool → Service Layer → Resource
    ↓
User ID from JWT → Parameter → Filter → Operation → Result
    ↓
Structured Response → Agent → Natural Language Response
```

## 🎯 Quick Start Templates

### Template 1: Database Integration
```python
# mcp_server.py
from mcp.server.fastmcp import FastMCP
from sqlmodel import Session, create_engine

mcp = FastMCP("DatabaseService")
engine = create_engine(DATABASE_URL)

def get_session():
    return Session(engine)

@mcp.tool()
def list_records(user_id: str, filters: dict = None, limit: int = 50, offset: int = 0) -> dict:
    """List database records for user."""
    session = get_session()
    try:
        query = session.query(Record).filter(Record.user_id == user_id)
        # Apply filters...
        total = query.count()
        items = query.limit(limit).offset(offset).all()
        return {"success": True, "data": [item.to_dict() for item in items], "count": total}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        session.close()

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

### Template 2: API Integration
```python
# mcp_server.py
from mcp.server.fastmcp import FastMCP
import httpx

mcp = FastMCP("APIService")

@mcp.tool()
def call_api(user_id: str, endpoint: str, method: str = "GET", data: dict = None) -> dict:
    """Call external API with user credentials."""
    try:
        # Get user credentials (from database, secrets manager, etc.)
        api_key = get_user_api_key(user_id)

        response = httpx.request(
            method=method,
            url=f"{BASE_URL}/{endpoint}",
            headers={"Authorization": f"Bearer {api_key}"},
            json=data,
            timeout=30.0
        )

        return {"success": True, "status": response.status_code, "data": response.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

### Template 3: File System Integration
```python
# mcp_server.py
from mcp.server.fastmcp import FastMCP
import os

mcp = FastMCP("FileService")

@mcp.tool()
def manage_files(user_id: str, action: str, path: str, content: str = None) -> dict:
    """Manage user files securely."""
    user_dir = f"/data/users/{user_id}"

    # Security: Prevent directory traversal
    full_path = os.path.abspath(os.path.join(user_dir, path))
    if not full_path.startswith(os.path.abspath(user_dir)):
        return {"success": False, "error": "Invalid path"}

    try:
        if action == "list":
            return {"success": True, "files": os.listdir(full_path)}
        elif action == "read":
            with open(full_path, 'r') as f:
                return {"success": True, "content": f.read()}
        elif action == "write":
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(content or "")
            return {"success": True, "message": "Written"}
        elif action == "delete":
            os.remove(full_path)
            return {"success": True, "message": "Deleted"}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

### Universal Integration with Agent
```python
# agents.py
from agents import Agent, Runner
from agents.mcp import MCPServerStdio

agent = Agent(
    name="UniversalAgent",
    instructions="""You have access to tools for managing ANY resource type.
    - User ID is known from authentication
    - Use tools naturally with plain language
    - Explain errors clearly
    - Handle pagination for large results
    """,
    model="xiami:mimo-v2-flash",
    mcp_servers=[]
)

async def run_agents(user_input: str, user_id: str) -> dict:
    """Universal agent runner for ANY resource type."""
    server = MCPServerStdio(
        params={"command": "uv", "args": ["run", "mcp_server.py"]},
        client_session_timeout_seconds=60
    )

    agent.mcp_servers = [server]

    try:
        await server.connect()
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

# main.py
from fastapi import FastAPI, Depends, Header

app = FastAPI()

async def get_user_id(authorization: str = Header(...)) -> str:
    """Extract user_id from JWT - works with ANY provider."""
    token = authorization.replace("Bearer ", "")
    payload = await verify_token(token)
    return get_user_id_from_token(payload)

@app.post("/api/agents/chat")
async def chat(message: str, user_id: str = Depends(get_user_id)):
    """Universal endpoint for ANY resource type."""
    return await run_agents(message, user_id)
```

## 🎯 Success Criteria

✅ **Universal**: Works for ANY resource type (database, API, files, services, hardware)
✅ **Pattern-based**: No hardcoded function names or schemas
✅ **Secure**: Multiple validation layers for ANY resource
✅ **Scalable**: Per-request isolation for ANY resource
✅ **Testable**: Universal testing patterns for ANY resource
✅ **Documented**: Self-documenting for ANY resource type

This skill provides everything needed to build production-ready MCP integrations for OpenAI Agents SDK with ANY resource type.