# LinkedIn API MCP Server Documentation

**Part of:** Personal AI Employee - Silver/Gold Tier
**File:** `ai_employee_scripts/mcp_servers/linkedin_api_mcp.py`
**MCP Name:** `linkedin-api`
**OAuth Helper:** `get_token.py`

---

## Table of Contents

- [Overview](#overview)
- [Architecture & Workflow](#architecture--workflow)
- [Setup Instructions](#setup-instructions)
- [Configuration](#configuration)
- [Available Tools](#available-tools)
- [Usage Examples](#usage-examples)
- [Integration with AI Employee](#integration-with-ai-employee)
- [Troubleshooting](#troubleshooting)
- [Token Refresh](#token-refresh)

---

## Overview

The LinkedIn API MCP Server enables the AI Employee to post content to LinkedIn via the LinkedIn Share API (User Generated Content Posts). It uses OAuth 2.0 authentication with access tokens.

### Features

| Feature | Description |
|---------|-------------|
| **Post to LinkedIn** | Publish text content to LinkedIn profile |
| **Get Profile Info** | Fetch authenticated user's profile details |
| **OAuth Authentication** | Secure token-based auth via get_token.py |
| **Auto-truncation** | Handles LinkedIn's 3000 character limit |

### Key Files

| File | Location | Purpose |
|------|----------|---------|
| `linkedin_api_mcp.py` | `ai_employee_scripts/mcp_servers/` | MCP server implementation |
| `get_token.py` | Project root | OAuth callback server for token generation |
| `.env` | `ai_employee_scripts/` | Stores credentials and access token |

---

## Architecture & Workflow

### System Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    LINKEDIN POSTING WORKFLOW                             │
└─────────────────────────────────────────────────────────────────────────┘

     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
     │ LinkedIn App  │     │ get_token.py │     │linkedin_api   │
     │ Creation     │     │(OAuth Server) │     │_mcp.py       │
     └──────┬───────┘     └──────┬───────┘     └──────┬───────┘
            │                    │                    │
            ▼                    ▼                    ▼
     Client ID              Authorization         Access Token
     Client Secret          Code Exchange         (saved to .env)
            │                    │                    │
            └────────────────────┴────────────────────┘
                                    │
                                    ▼
                         ┌─────────────────────────────────────┐
                         │    AI Employee System              │
                         │                                     │
                         │  1. Cron triggers /linkedin-posting   │
                         │  2. Post created in Pending_Approval/ │
                         │  3. Human approves → Approved/      │
                         │  4. /execute-approved calls MCP      │
                         │  5. linkedin_api_mcp posts to LinkedIn │
                         └─────────────────────────────────────┘
```

### Authentication Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    LINKEDIN OAUTH 2.0 FLOW                                │
└─────────────────────────────────────────────────────────────────────────┘

STEP 1: CREATE LINKEDIN APP
┌──────────────────────────────────────────────────────────────┐
│ https://www.linkedin.com/developers/tools                     │
│                                                              │
│ 1. Create App                                                 │
│ 2. Configure OAuth 2.0                                        │
│ 3. Add Redirect URI: http://localhost:8000/callback          │
│ 4. Add Scopes: w_member_social, openid, profile, email        │
│ 5. Get Client ID and Client Secret                              │
└──────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
STEP 2: RUN get_token.py
┌──────────────────────────────────────────────────────────────┐
│ python get_token.py                                         │
│                                                              │
│ 1. Loads credentials from .env                              │
│ 2. Starts HTTP server on port 8000                          │
│ 3. Generates authorization URL                                │
│ 4. Opens browser (you log in and authorize)                   │
│ 5. LinkedIn redirects to localhost:8000/callback?code=...    │
│ 6. Exchanges code for access token                           │
│ 7. Displays token in terminal                                │
└──────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
STEP 3: SAVE TOKEN TO .env
┌──────────────────────────────────────────────────────────────┐
│ LINKEDIN_ACCESS_TOKEN=your_access_token_here... │
└──────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
STEP 4: linkedin_api_mcp.py USES TOKEN
┌──────────────────────────────────────────────────────────────┐
│ All API calls include:                                       │
│ Authorization: Bearer {LINKEDIN_ACCESS_TOKEN}                 │
│ LinkedIn-Version: 202501                                     │
│ X-Restli-Protocol-Version: 2.0.0                            │
└──────────────────────────────────────────────────────────────┘
```

---

## Setup Instructions

### Prerequisites

- Python 3.13+ with UV package manager
- LinkedIn account (any account can create apps)
- Local development environment (for OAuth callback)

### Step 1: Create LinkedIn Application

1. **Go to LinkedIn Developer Portal:**
   ```
   https://www.linkedin.com/developers/tools
   ```

2. **Sign In** with your LinkedIn credentials

3. **Create a New App:**
   - Click **"Create App"**
   - Choose **"Auth Code"** flow (recommended)
   - Fill in app details:
     - **App Name**: AI Employee (or your preferred name)
     - **Logo**: Upload any image (optional)
     - **Description**: Automated content posting system

4. **Configure OAuth 2.0:**
   - Go to **"Auth"** tab in your app dashboard
   - Set **Default Redirect URL** to: `http://localhost:8000/callback`
   - Add the same URL to **"Redirect URLs"** list
   - Add **OAuth 2.0 Scopes** (click "Add scope" for each):
     - `w_member_social` - Required for posting UGC content
     - `openid` - Get user profile ID
     - `profile` - Read profile data
     - `email` - Get user email (optional)

5. **Copy Your Credentials:**
   - **Client ID** (also called API Key) - Save this
   - **Client Secret** - Save this (starts with `WPL_AP1...`)

### Step 2: Configure .env File

Add your credentials to `ai_employee_scripts/.env`:

```bash
# LinkedIn OAuth Credentials
LINKEDIN_CLIENT_ID=your_client_id_here
LINKEDIN_CLIENT_SECRET=your_client_secret_here
```

**Example:**
```bash
LINKEDIN_CLIENT_ID=your_client_id_here
LINKEDIN_CLIENT_SECRET=your_client_secret_here
```

### Step 3: Generate Access Token

Run the OAuth helper script from the project root:

```bash
python get_token.py
```

**What happens:**

1. Script loads credentials from `.env`
2. Starts HTTP server on `http://localhost:8000`
3. Displays message:
   ```
   Waiting for LinkedIn... Open the URL in your browser now.
   ```
4. **Authorization URL is displayed** (or browser opens automatically):
   ```
   https://www.linkedin.com/oauth/v2/authorization?
     response_type=code
     &client_id=YOUR_CLIENT_ID
     &redirect_uri=http://localhost:8000/callback
     &scope=w_member_social+openid+profile+email
     &state=STATE_STRING
   ```

5. **In your browser:**
   - Sign in to LinkedIn (if not already)
   - Review permissions
   - Click **"Allow"**

6. **LinkedIn redirects back** to `http://localhost:8000/callback?code=AUTH_CODE`

7. **Script exchanges code for token** and displays:
   ```
   ======================================================================
   ✅ ACCESS TOKEN RECEIVED!
   ======================================================================

   Copy this token to your .env file as LINKEDIN_ACCESS_TOKEN:

   your_access_token_here_truncated_example...

   ======================================================================
   ```

8. **Copy the token** and add to `.env`:
   ```bash
   LINKEDIN_ACCESS_TOKEN=AQVs2Z0diDSInXm78Fq7bSsV1T2DU9rtuxz3nZkS5inTGS58tQTu...
   ```

### Step 4: Enable MCP in Claude Code

The LinkedIn API MCP server is configured in `AI_Employee_Vault/.mcp.json`. This file contains all MCP server configurations for the AI Employee project.

**Project MCP Configuration (`AI_Employee_Vault/.mcp.json`):**

```json
{
  "mcpServers": {
    "linkedin-api": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts",
        "run",
        "mcp_servers/linkedin_api_mcp.py"
      ],
      "env": {
        "PYTHONPATH": "/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts"
      }
    }
  }
}
```

**Alternative: Claude Code Settings**

You can also configure in `.claude/settings.local.json`:

```json
{
  "mcpServers": {
    "linkedin-api": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "./ai_employee_scripts",
        "run",
        "mcp_servers/linkedin_api_mcp.py"
      ],
      "env": {
        "PYTHONPATH": "./ai_employee_scripts"
      }
    }
  }
}
```

**Important:** Update the paths to match your project directory if different from the example above.

Restart Claude Code to load the MCP server.

---

## Configuration

### Required Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `LINKEDIN_CLIENT_ID` | OAuth client ID from LinkedIn app | `your_client_id_here` |
| `LINKEDIN_CLIENT_SECRET` | OAuth client secret from LinkedIn app | `your_client_secret_here` |
| `LINKEDIN_ACCESS_TOKEN` | OAuth access token (generated by get_token.py) | `your_access_token_here` |

### File Locations

| File | Location | Purpose |
|------|----------|---------|
| `linkedin_api_mcp.py` | `ai_employee_scripts/mcp_servers/` | MCP server implementation |
| `get_token.py` | Project root | OAuth callback server |
| `.env` | `ai_employee_scripts/.env` | Credentials and token storage |

### LinkedIn API Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `https://api.linkedin.com/v2/userinfo` | Get user profile (Person URN) |
| `https://api.linkedin.com/v2/ugcPosts` | Create UGC post |

---

## Available Tools

### 1. post_to_linkedin

Post text content to LinkedIn using the LinkedIn Share API.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `text` | string | Yes | Post content (max 3000 chars for articles) |
| `title` | string | No | Optional title/headline (prepended to text) |

**Returns:** Success message with post URN or error details

**Example:**
```python
await mcp__linkedin_api__post_to_linkedin(
    text="Here's an insight about AI automation..."
)
```

**With title:**
```python
await mcp__linkedin_api__post_to_linkedin(
    title="3 AI Mistakes to Avoid",
    text="Everyone's talking about AI, but most businesses..."
)
```

---

### 2. get_linkedin_profile

Fetch the authenticated user's LinkedIn profile information.

**Parameters:** None

**Returns:** Profile information including name, email, Person URN

**Example:**
```python
profile = await mcp__linkedin_api__get_linkedin_profile()
```

**Return format:**
```
LinkedIn Profile Information:

Name: John Doe
Email: john.doe@email.com
Person URN: 785123456

Full Profile Data:
{...}
```

---

## Usage Examples

### Example 1: Simple Text Post

```python
await mcp__linkedin_api__post_to_linkedin(
    text="Just shipped a new feature! 🚀\n\n#AI #Automation #ProductLaunch"
)
```

### Example 2: Article with Title

```python
await mcp__linkedin_api__post_to_linkedin(
    title="The Future of AI in Business",
    text="""Here's what most businesses get wrong about AI implementation...

The businesses winning with AI aren't using it for everything—they're using it for specific, high-impact tasks.

Read more to learn the 3 mistakes that waste money..."""
)
```

### Example 3: Get Profile Before Posting

```python
# First get the profile to ensure token works
profile = await mcp__linkedin_api__get_linkedin_profile()

# Then post content
await mcp__linkedin_api__post_to_linkedin(
    text="Great to connect with this community!"
)
```

---

## Integration with AI Employee

### Cron Automation

Daily at 2 AM, the LinkedIn cron trigger runs:

```bash
0 2 * * * cd "/path/to/ai_employee_scripts" && uv run python scripts/linkedin_cron_trigger.py
```

**Workflow:**
1. Cron trigger executes `/linkedin-posting` skill
2. Skill generates post content
3. Creates approval file in `Pending_Approval/`
4. Human reviews and moves to `Approved/`
5. `/execute-approved` skill posts via `linkedin-api` MCP

### Skills That Use This MCP

| Skill | Purpose |
|-------|---------|
| `/linkedin-posting` | Generate LinkedIn post content |
| `/execute-approved` | Post approved content to LinkedIn |

---

## Troubleshooting

### Problem: "LINKEDIN_ACCESS_TOKEN not found"

**Error:**
```
❌ LINKEDIN_ACCESS_TOKEN not found in environment!
```

**Solution:**
1. Run `python get_token.py` to generate token
2. Copy displayed token to `.env` as `LINKEDIN_ACCESS_TOKEN`

---

### Problem: "redirect_uri_mismatch"

**Error in browser:**
```
Error: redirect_uri_mismatch
The redirect URI in the request, http://localhost:8000/callback, does not match...
```

**Solution:**
1. Go to LinkedIn Developer Dashboard
2. Edit your app → Auth → Redirect URLs
3. Add `http://localhost:8000/callback` exactly (no trailing slash differences)

---

### Problem: "401 Unauthorized"

**Error when posting:**
```
Error: Failed to post to LinkedIn. Status: 401
```

**Solution:**
1. Token may have expired - LinkedIn access tokens expire
2. Re-run `python get_token.py` to get fresh token
3. Update `.env` with new token

---

### Problem: "Port 8000 already in use"

**Error:**
```
OSError: [Errno 48] Address already in use
```

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 [PID]

# Or wait a moment and retry
```

---

### Problem: "No person URN found"

**Error:**
```
Error: No person ID found in profile response
```

**Solution:**
1. Check your app has required scopes: `w_member_social`, `openid`, `profile`
2. Re-authorize by running `python get_token.py` again
3. Verify token is correct in `.env`

---

### Problem: "Post content truncated"

**Warning:**
```
⚠️ Post content truncated to 3000 characters
```

**Solution:**
- This is expected behavior - LinkedIn has character limits
- Important content is preserved with `...` at the end
- Edit content to be under 3000 characters if full text needed

---

## Token Refresh

LinkedIn access tokens do expire. When your posts start failing with 401 errors:

1. **Re-run the OAuth flow:**
   ```bash
   python get_token.py
   ```

2. **Authorize in browser** (you may stay logged in)

3. **Copy new token** to `.env` as `LINKEDIN_ACCESS_TOKEN`

4. **Old token is replaced** - no need to revoke old token

**Note:** LinkedIn access tokens typically last for 60 days. Set a reminder to refresh monthly.

---

## LinkedIn App Configuration Reference

### OAuth 2.0 Settings

| Setting | Value | Notes |
|---------|-------|-------|
| **Default Redirect URL** | `http://localhost:8000/callback` | Must match exactly |
| **Redirect URLs** | `http://localhost:8000/callback` | Add to list |
| **OAuth 2.0 Scopes** | See below | Required permissions |

### Required Scopes

| Scope | Purpose | Required For |
|-------|---------|--------------|
| `w_member_social` | Share content | ✅ Posting (required) |
| `openid` | Get user ID via OpenID | ✅ Getting Person URN |
| `profile` | Read profile data | ✅ User info |
| `email` | Get email address | Optional |

### Your App vs Production

**For Development/Hackathon:**
- Use Auth Code flow
- Localhost redirect URI
- Your personal LinkedIn account

**For Production:**
- Consider using a separate LinkedIn account
- Use environment-specific redirect URIs
- Implement token refresh logic
- Consider using LinkedIn's partner program for higher limits

---

## Security Best Practices

1. **Never commit `.env` file** - contains secrets
2. **Keep Client Secret safe** - treat it like a password
3. **Token storage** - `.env` is in `ai_employee_scripts/` (not in vault)
4. **Token rotation** - Refresh tokens periodically
5. **Scope minimization** - Only request permissions you need

---

## Quick Reference

### MCP Tools

| Tool | Purpose |
|------|---------|
| `post_to_linkedin()` | Post content to LinkedIn |
| `get_linkedin_profile()` | Get user profile info |

### Environment Variables

| Variable | Required? | Purpose |
|----------|-----------|---------|
| `LINKEDIN_CLIENT_ID` | Yes | OAuth client ID |
| `LINKEDIN_CLIENT_SECRET` | Yes | OAuth client secret |
| `LINKEDIN_ACCESS_TOKEN` | Yes | OAuth access token |

### LinkedIn Limits

| Limit | Value |
|-------|-------|
| Post character limit | 3000 characters (articles) |
| Access token lifespan | ~60 days |
| Rate limits | Dependent on app type |

---

**Last Updated:** February 28, 2026
**Part of:** Personal AI Employee Hackathon 0 - Silver/Gold Tier
