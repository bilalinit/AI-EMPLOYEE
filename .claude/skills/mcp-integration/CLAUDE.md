# CLAUDE.md - MCP Integration Skill

## ⚡️ Usage Guidelines
This skill MUST be consulted whenever the user requests:
- "Create an MCP tool for X"
- "Add [resource] access to my agent"
- "Build a tool that can [action]"
- "Connect agent to [database/API/service]"
- "How do I authenticate MCP tools?"

## 🛡️ Core Constraints
1. **NEVER** hardcode user IDs - always get from JWT token
2. **ALWAYS** use dynamic MCP server creation (per-request)
3. **NEVER** share database sessions between tools
4. **ALWAYS** include proper cleanup in finally blocks
5. **NEVER** expose tools without user isolation

## 🔍 Discovery
- **Setup**: `TOKENS.md` (Packages, env vars, security)
- **Structure**: `INTEGRATION_PATTERNS.md` (Server, tools, integration)
- **Templates**: `CODE_TEMPLATES.md` (Code examples)

## ❌ Common Mistakes
- **Static MCP servers** (should be per-request)
- **Missing user isolation** (all tools need user_id)
- **No cleanup** (memory leaks, hanging connections)
- **Hardcoded credentials** (use environment variables)
- **No error handling** (agent crashes on tool errors)

## ✅ Success Checklist
- [ ] MCP server created with FastMCP
- [ ] Tools require user_id parameter
- [ ] JWT token provides user_id automatically
- [ ] Dynamic server lifecycle (connect/cleanup)
- [ ] Error handling returns structured responses
- [ ] Tests verify user isolation
- [ ] Environment variables for secrets