# MCP Integration Skill: OpenAI Agents + Model Context Protocol

## Overview
This skill teaches how to build **MCP (Model Context Protocol) tools** for OpenAI Agents SDK, enabling AI agents to access external resources, databases, and APIs through standardized tool interfaces.

## 🛑 **MANDATORY REFERENCE**
> **ALWAYS** check these files before creating MCP tools:
> 1. **`CLAUDE.md`**: Usage guidelines and core constraints
> 2. **`TOKENS.md`**: Required packages, environment setup, security patterns
> 3. **`INTEGRATION_PATTERNS.md`**: Server structure, tool patterns, integration flow
> 4. **`CODE_TEMPLATES.md`**: Code templates for tools, agents, auth

## Core Capabilities
- **Create MCP servers** with FastMCP
- **Integrate with OpenAI Agents SDK** dynamically
- **Handle JWT authentication** for user isolation
- **Build user-scoped tools** for databases/APIs
- **Manage server lifecycle** (connect/cleanup)
- **Error handling** and testing patterns

## When to Use This Skill
**User requests:**
- "Create an MCP tool for [resource]"
- "Add [database/API] access to my agent"
- "Build a tool that can [action]"
- "How do I authenticate MCP with JWT?"
- "Connect my agent to [external service]"

## Common Patterns & Responses

**User:** "Create an MCP tool to manage user files"
**You:** *Generates FastMCP server with file tools, integrates with agent, adds JWT auth, provides test suite*

**User:** "My agent needs database access"
**You:** *Creates SQLModel tools, user-scoped queries, connection pooling, error handling*

**User:** "How do I add authentication to MCP tools?"
**You:** *Shows JWT validation pattern, user_id extraction, secure context injection*