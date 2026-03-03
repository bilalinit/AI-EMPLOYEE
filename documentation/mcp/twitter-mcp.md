# Twitter/X API MCP Server Documentation

**Part of:** Personal AI Employee - Gold Tier
**File:** `ai_employee_scripts/mcp_servers/twitter_mcp.py`
**MCP Name:** `twitter-api`

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
- [API Limits](#api-limits)

---

## Overview

The Twitter/X API MCP Server enables the AI Employee to post tweets to Twitter/X using the Twitter API v2 via Tweepy. It uses OAuth 1.0a authentication (4-key method) for secure access.

### Features

| Feature | Description |
|---------|-------------|
| **Post Tweets** | Publish text content to Twitter/X profile |
| **Get Profile** | Fetch authenticated user's profile details |
| **Business Updates** | Pre-formatted business event tweets |
| **Auto-truncation** | Handles Twitter's 280 character limit |

### Key Files

| File | Location | Purpose |
|------|----------|---------|
| `twitter_mcp.py` | `ai_employee_scripts/mcp_servers/` | MCP server implementation |
| `.env` | `ai_employee_scripts/` | Stores API keys and access tokens |

---

## Architecture & Workflow

### System Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     TWITTER MCP WORKFLOW                        │
└─────────────────────────────────────────────────────────────────┘

     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
     │ Twitter Dev  │     │twitter_mcp   │     │  Tweepy      │
     │ Portal       │     │  .py         │     │  Client      │
     └──────┬───────┘     └──────┬───────┘     └──────┬───────┘
            │                    │                    │
            ▼                    ▼                    ▼
     API Key              FastMCP Server         OAuth 1.0a
     API Secret           (twitter-api)          Client
     Access Token              │                    │
     Access Token              │                    ▼
          Secret               │             Twitter API v2
            │                  │
            └──────────────────┴────────────────────┘
                                    │
                                    ▼
                         ┌─────────────────────────────────────┐
                         │    AI Employee System              │
                         │                                     │
                         │  1. Cron triggers /twitter-posting  │
                         │  2. Post created in Pending_Approval/ │
                         │  3. Human approves → Approved/      │
                         │  4. /execute-approved calls MCP      │
                         │  5. twitter_mcp posts to Twitter     │
                         └─────────────────────────────────────┘
```

### Authentication Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    TWITTER OAUTH 1.0a FLOW                      │
└─────────────────────────────────────────────────────────────────┘

STEP 1: CREATE TWITTER APP
┌──────────────────────────────────────────────────────────────┐
│ https://developer.x.com/en/portal/dashboard                  │
│                                                              │
│ 1. Create Project + App                                      │
│ 2. Go to App → Settings → User authentication settings      │
│ 3. Set permissions to "Read and Write" (IMPORTANT!)          │
│ 4. Generate API Key, API Secret                              │
│ 5. Generate Access Token, Access Token Secret               │
│ 6. Copy all 4 credentials to .env                            │
└──────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
STEP 2: SAVE CREDENTIALS TO .env
┌──────────────────────────────────────────────────────────────┐
│ X_API_KEY=your_api_key_here                                  │
│ X_API_SECRET=your_api_secret_here                            │
│ X_ACCESS_TOKEN=your_access_token_here                       │
│ X_ACCESS_TOKEN_SECRET=your_access_token_secret_here         │
└──────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
STEP 3: twitter_mcp.py USES CREDENTIALS
┌──────────────────────────────────────────────────────────────┐
│ All MCP calls use Tweepy Client with OAuth 1.0a:             │
│                                                              │
│ client = tweepy.Client(                                     │
│     consumer_key=X_API_KEY,                                 │
│     consumer_secret=X_API_SECRET,                           │
│     access_token=X_ACCESS_TOKEN,                            │
│     access_token_secret=X_ACCESS_TOKEN_SECRET               │
│ )                                                            │
└──────────────────────────────────────────────────────────────┘
```

---

## Setup Instructions

### Prerequisites

- Python 3.13+ with UV package manager
- Twitter/X account (any account can create apps)
- Twitter Developer account (free tier available)

### Step 1: Create Twitter/X Developer Account

1. **Go to Twitter Developer Portal:**
   ```
   https://developer.x.com/en/portal/dashboard
   ```

2. **Sign Up / Sign In** with your Twitter credentials

3. **Create a Free Account** if you don't have one:
   - Click "Sign up for Free Account"
   - Select "Free" tier (500 posts/month, 100 reads/month)
   - When asked what you're building, use this description:
     ```
     Personal automation tool that posts business updates, project completions,
     and service announcements to X. Built for a solo entrepreneur to schedule
     and publish content automatically as part of a local-first AI productivity system.
     ```
   - 💡 Free tier access is approved instantly
   - Agree to terms and submit

### Step 2: Create Project and App

1. **Create a New Project:**
   - Click **"+ Create Project"**
   - Enter **Project name**: `AI Employee`
   - Use case: **Automated posting** or **Exploring the API**

2. **Create an App:**
   - After project creation, click **"+ Create App"**
   - **App name**: `AI Employee Twitter Bot` (or similar)
   - Click **"Complete"**

3. **Go to App Settings:**
   - Find your app in the project dashboard
   - Click **App settings** or go to **"Keys and tokens"**

### Step 3: Configure User Authentication (Critical!)

This is the **most important step** - without proper permissions, posting will fail with a 403 Forbidden error.

1. **Go to "User authentication settings"** in your app

2. **Edit / Set up authentication:**
   - **Type**: `OAuth 1.0a`
   - **Type of App**: `Web App, Automated App or Bot`
   - **Callback URI**: `http://127.0.0.1`
     - ⚠️ Make sure there are no trailing spaces - type it fresh and press End to check
   - **Website URL**: `http://127.0.0.1`
   - **Organization URL**: (leave blank)
   - **Terms of Service**: (leave blank)
   - **Privacy Policy**: (leave blank)
   - **App permissions**: **Read and Write** ⚠️
     - **Default is "Read Only" — you MUST change this!**

3. **Save and Generate Tokens:**

4. **Copy your 4 credentials:**
   - **API Key** (Consumer Key)
   - **API Key Secret** (Consumer Secret)
   - **Access Token**
   - **Access Token Secret**

   **Important:** If you had previously generated tokens with "Read Only" permissions, you must **delete and regenerate** them after changing to "Read and Write"!

### Step 4: Configure .env File

Add your credentials to `ai_employee_scripts/.env`:

```bash
# Twitter/X OAuth 1.0a Credentials
X_API_KEY=your_api_key_here
X_API_SECRET=your_api_secret_here
X_ACCESS_TOKEN=your_access_token_here
X_ACCESS_TOKEN_SECRET=your_access_token_secret_here
```

**Example:**
```bash
X_API_KEY=your_api_key_here
X_API_SECRET=your_api_secret_here
X_ACCESS_TOKEN=your_access_token_here
X_ACCESS_TOKEN_SECRET=your_access_token_secret_here
```

**Never commit your `.env` file to GitHub. Ensure it's in `.gitignore`.**

### Step 5: Verify MCP Configuration

The Twitter API MCP is configured in `AI_Employee_Vault/.mcp.json`:

```json
{
  "mcpServers": {
    "twitter-api": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts",
        "run",
        "mcp_servers/twitter_mcp.py"
      ],
      "env": {
        "PYTHONPATH": "/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts"
      }
    }
  }
}
```

**Important:** Update the paths to match your project directory if different from the example above.

Restart Claude Code to load the MCP server.

### Step 6: Test the Connection

When the MCP server starts, it will display:

```
🐦 ╔════════════════════════════════════════════════════════╗
🤖 ║      Twitter/X API MCP Server for AI Employee          ║
🐦 ╚════════════════════════════════════════════════════════╝

🔑 All 4 credentials found in .env

🚀 Starting MCP server...
🛠️ Tools available:
  - post_tweet: Post any text as a tweet
  - get_twitter_profile: Get your account info
  - post_business_update: Post formatted business updates

⏳ Server is running. Press Ctrl+C to stop.
```

---

## Configuration

### Required Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `X_API_KEY` | OAuth consumer key (API Key) | `your_api_key_here` |
| `X_API_SECRET` | OAuth consumer secret (API Secret) | `your_api_secret_here` |
| `X_ACCESS_TOKEN` | OAuth access token | `your_access_token_here` |
| `X_ACCESS_TOKEN_SECRET` | OAuth access token secret | `your_access_token_secret_here` |

### File Locations

| File | Location | Purpose |
|------|----------|---------|
| `twitter_mcp.py` | `ai_employee_scripts/mcp_servers/` | MCP server implementation |
| `.env` | `ai_employee_scripts/.env` | Credentials storage |

### Twitter API Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `POST /2/tweets` | Create a tweet |
| `GET /2/users/me` | Get authenticated user profile |

### Configuration Constants

| Constant | Value | Purpose |
|----------|-------|---------|
| `TWEET_MAX_CHARS` | 280 | Twitter character limit |

---

## Available Tools

### 1. post_tweet

Post a tweet to Twitter/X on behalf of the authenticated account.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `text` | string | Yes | Tweet content (max 280 chars, auto-truncated) |

**Returns:** Success message with tweet ID and URL, or error details

**Example:**
```python
await mcp__twitter_api__post_tweet(
    text="Just shipped a new feature! 🚀 #AI #Automation"
)
```

**Return format:**
```
Tweet posted successfully!

Tweet ID: 1234567890123456789
URL: https://twitter.com/i/web/status/1234567890123456789
Content: Just shipped a new feature! 🚀 #AI #Automation
Posted at: 2026-02-28T12:34:56.789012
```

---

### 2. get_twitter_profile

Fetch the authenticated user's Twitter/X profile information.

**Parameters:** None

**Returns:** Profile information including username, name, metrics

**Example:**
```python
profile = await mcp__twitter_api__get_twitter_profile()
```

**Return format:**
```
Twitter/X Profile Information:

Name: John Doe
Username: @johndoe
User ID: 1234567890
Bio: AI automation enthusiast | Building the future

Public Metrics:
  Followers: 1234
  Following: 567
  Tweets: 890

Profile URL: https://twitter.com/johndoe
```

---

### 3. post_business_update

Post a formatted business update tweet for the AI Employee workflow. This tool automatically formats common business events into professional tweets.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `update_type` | string | Yes | Type of update (see options below) |
| `details` | string | Yes | Specific details of the update |
| `hashtags` | string | No | Hashtags to append (e.g., "#freelance #AI") |

**Update Type Options:**
| Type | Prefix | Example Use |
|------|--------|-------------|
| `invoice_sent` | ✅ Another project invoiced and delivered! | Client invoiced |
| `project_complete` | 🎉 Project complete! | Delivery confirmation |
| `new_service` | 🚀 Excited to announce: | Service launch |
| `milestone` | 🏆 Milestone reached: | Achievement unlocked |
| `general` | (none) | Custom message |

**Example:**
```python
await mcp__twitter_api__post_business_update(
    update_type="project_complete",
    details="Delivered AI automation system for local bakery",
    hashtags="#AI #Automation #SmallBusiness"
)
```

**Resulting Tweet:**
```
🎉 Project complete! Delivered AI automation system for local bakery

#AI #Automation #SmallBusiness
```

---

## Usage Examples

### Example 1: Simple Text Post

```python
await mcp__twitter_api__post_tweet(
    text="Just finished setting up my AI Employee! 🤖 It's already helping me manage emails and social media. #AI #Automation"
)
```

### Example 2: Project Completion Announcement

```python
await mcp__twitter_api__post_business_update(
    update_type="project_complete",
    details="Delivered custom CRM automation for startup client",
    hashtags="#freelance #automation #CRM"
)
```

### Example 3: Invoice Sent Notification

```python
await mcp__twitter_api__post_business_update(
    update_type="invoice_sent",
    details="Web development project for ABC Corp",
    hashtags="#webdev #freelance"
)
```

### Example 4: New Service Launch

```python
await mcp__twitter_api__post_business_update(
    update_type="new_service",
    details="Now offering AI-powered social media automation services!",
    hashtags="#AI #SMA #NewService"
)
```

### Example 5: Verify Profile Before Posting

```python
# First verify credentials work
profile = await mcp__twitter_api__get_twitter_profile()

# Then post content
await mcp__twitter_api__post_tweet(
    text="Great to be here! Building the future of AI automation."
)
```

---

## Integration with AI Employee

### Cron Automation

Daily at 3 AM, the Twitter cron trigger runs:

```bash
0 3 * * * cd "/path/to/ai_employee_scripts" && uv run python scripts/twitter_cron_trigger.py
```

**Workflow:**
1. Cron trigger executes `/twitter-posting` skill
2. Skill generates tweet content
3. Creates approval file in `Pending_Approval/`
4. Human reviews and moves to `Approved/`
5. `/execute-approved` skill posts via `twitter-api` MCP

### Skills That Use This MCP

| Skill | Purpose |
|-------|---------|
| `/twitter-posting` | Generate Twitter post content |
| `/execute-approved` | Post approved content to Twitter |

---

## Troubleshooting

### Problem: "Missing Twitter credentials"

**Error:**
```
❌ Missing credentials: X_API_KEY, X_ACCESS_TOKEN
📝 Add these to your .env file:
   X_API_KEY=your_value_here
   X_ACCESS_TOKEN=your_value_here
```

**Solution:**
1. Verify all 4 credentials are in `.env`:
   - `X_API_KEY`
   - `X_API_SECRET`
   - `X_ACCESS_TOKEN`
   - `X_ACCESS_TOKEN_SECRET`
2. Restart the MCP server

---

### Problem: "Forbidden (403): Twitter rejected the request"

**Error:**
```
Forbidden (403): Twitter rejected the request.
Most likely cause: Access Token is 'Read Only' — you need 'Read and Write'.
Fix: Go to developer.x.com → Your App → User authentication settings →
Set permissions to 'Read and Write' → Regenerate your Access Token.
```

**Solution:**
This is the **most common error**. Your access token has "Read Only" permissions.

1. Go to https://developer.x.com/en/portal/dashboard
2. Find your app → **Settings** → **User authentication settings**
3. **Edit** the authentication settings
4. Change **App permissions** from "Read" to **"Read and Write"**
5. **Save** the changes
6. **Delete** your old Access Token and Access Token Secret
7. **Regenerate** new tokens (they will have Read/Write permissions now)
8. **Update** `.env` with the new tokens
9. Restart the MCP server

---

### Problem: "Unauthorized (401): Invalid credentials"

**Error:**
```
Unauthorized (401): Invalid credentials.
Check that your X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET are all correct.
```

**Solution:**
1. Verify all 4 credentials in `.env` match exactly what's in the Twitter Developer Portal
2. Check for extra spaces or quotes around the values
3. Ensure you copied the entire token (they can be quite long)
4. Try regenerating tokens in the portal and updating `.env`

---

### Problem: "Rate limit exceeded (429)"

**Error:**
```
Rate limit exceeded (429): Too many requests.
Free tier allows 500 posts per month. Wait before trying again.
```

**Solution:**
1. The free tier allows **500 posts per month**
2. Wait before posting again
3. Consider upgrading to Basic tier if you need more posts
4. Check your usage at https://developer.x.com/en/portal/dashboard

---

### Problem: "Tweet truncated to 280 characters"

**Warning:**
```
⚠️ Tweet truncated to 280 characters
```

**Solution:**
- This is expected behavior - Twitter has a 280 character limit
- Important content is preserved with `...` at the end
- Edit content to be under 280 characters if full text needed

---

## API Limits

### Twitter API Free Tier Limits

| Resource | Limit | Period |
|----------|-------|--------|
| **Posts (tweets)** | 500 | Month |
| **User lookup** | 100 | 24 hours |
| **Rate limit reset** | Varies | Check API response headers |

### Best Practices

1. **Batch tweets** - Don't post more than a few per hour
2. **Monitor usage** - Check your API dashboard regularly
3. **Handle rate limits** - Implement backoff if posting frequently
4. **Test first** - Use `get_twitter_profile()` to verify credentials before posting

### Upgrading Tiers

If you need higher limits:

| Tier | Posts/Month | Cost |
|------|-------------|------|
| Free | 500 | $0 |
| Basic | 1,500 | $100/month |
| Pro | 10,000 | $5,000/month |

See https://developer.x.com/en/pricing for current pricing.

---

## Security Best Practices

1. **Never commit `.env` file** - contains secrets
2. **Keep API Secret safe** - treat it like a password
3. **Token storage** - `.env` is in `ai_employee_scripts/` (not in vault)
4. **Scope minimization** - Only use permissions you need
5. **Regenerate tokens** - If credentials are compromised, regenerate immediately

---

## Quick Reference

### MCP Tools

| Tool | Purpose |
|------|---------|
| `post_tweet()` | Post any text as a tweet |
| `get_twitter_profile()` | Get your account info |
| `post_business_update()` | Post formatted business updates |

### Environment Variables

| Variable | Required? | Purpose |
|----------|-----------|---------|
| `X_API_KEY` | Yes | OAuth consumer key |
| `X_API_SECRET` | Yes | OAuth consumer secret |
| `X_ACCESS_TOKEN` | Yes | OAuth access token |
| `X_ACCESS_TOKEN_SECRET` | Yes | OAuth access token secret |

### Twitter Limits

| Limit | Value |
|-------|-------|
| Tweet character limit | 280 characters |
| Free tier posts/month | 500 |
| Rate limit | Varies by endpoint |

### Business Update Types

| Type | Use Case |
|------|----------|
| `invoice_sent` | Client invoiced |
| `project_complete` | Project delivered |
| `new_service` | Service announcement |
| `milestone` | Achievement reached |
| `general` | Custom message |

---

**Last Updated:** February 28, 2026
**Part of:** Personal AI Employee Hackathon 0 - Gold Tier
