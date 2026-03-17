# Security & Credentials Guide

**Part of:** Personal AI Employee - Gold/Platinum Tier
**Last Updated:** March 2026

---

## Overview

This guide covers credential management, OAuth setup, and security best practices for the AI Employee system.

---

## Credential Types

| Type | Storage | Example |
|------|---------|---------|
| **OAuth Client Secrets** | JSON file | Gmail `credentials.json` |
| **OAuth Tokens** | JSON file (auto-generated) | `token_gmail.json` |
| **API Keys** | Environment variables | `X_API_KEY` |
| **API Secrets** | Environment variables | `X_API_SECRET` |
| **Access Tokens** | Environment variables | `META_ACCESS_TOKEN` |
| **Database Credentials** | Environment variables | `ODOO_PASSWORD` |

---

## Gmail OAuth Setup

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click **Create Project** or select existing
3. Name it: `AI Employee Gmail`

### Step 2: Enable Gmail API

1. Navigate to **APIs & Services** → **Library**
2. Search for **"Gmail API"**
3. Click **Enable**

### Step 3: Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Choose **External** user type
3. Fill in required fields:
   - App name: `AI Employee Gmail`
   - User support email: your email
   - Developer contact: your email
4. Click **Save and Continue**
5. Add scopes:
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/gmail.send`
   - `https://www.googleapis.com/auth/gmail.modify`
6. Click **Save and Continue**
7. Add test users (your email)
8. Click **Save and Continue**

### Step 4: Create OAuth Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **+ Create Credentials** → **OAuth client ID**
3. Application type: **Desktop app**
4. Name: `AI Employee Gmail`
5. Click **Create**
6. **Download** the JSON file

### Step 5: Install Credentials

```bash
# Move downloaded file to scripts directory
mv ~/Downloads/client_secret_*.json ai_employee_scripts/credentials.json
```

### Step 6: First Authentication

```bash
cd ai_employee_scripts
uv run python mcp_servers/gmail_mcp.py
```

This will:
1. Display an authorization URL
2. Start local server on port 8080
3. Wait for you to authorize in browser
4. Save token to `token_gmail.json`

---

## LinkedIn API Setup

### Step 1: Create LinkedIn App

1. Go to [LinkedIn Developer Portal](https://www.linkedin.com/developers/)
2. Click **Create App**
3. Fill in:
   - App name: `AI Employee`
   - LinkedIn Page: Your company page
   - Privacy policy URL: Your privacy policy
4. Click **Create app**

### Step 2: Request API Products

1. Go to **Products** tab
2. Request access to:
   - **Share on LinkedIn** (for posting)
   - **Sign In with LinkedIn** (for profile access)
3. Wait for approval (usually instant for basic products)

### Step 3: Get Credentials

1. Go to **Auth** tab
2. Note your **Client ID** and **Client Secret**
3. Add to `.env`:
   ```bash
   LINKEDIN_CLIENT_ID=your_client_id
   LINKEDIN_CLIENT_SECRET=your_client_secret
   ```

### Step 4: Generate Access Token

**Option A: Use OAuth Flow**

```bash
cd /path/to/project
uv run python get_token.py
```

**Option B: Manual Token Generation**

1. Construct authorization URL:
   ```
   https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id=YOUR_CLIENT_ID&redirect_uri=http://localhost:8080&scope=w_member_social
   ```
2. Open in browser and authorize
3. Exchange code for token via API

### Step 5: Get User URN

```bash
# Using the LinkedIn API
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" https://api.linkedin.com/v2/userinfo
```

Add to `.env`:
```bash
LINKEDIN_URN=urn:li:person:YOUR_URN
```

---

## Twitter/X API Setup

### Prerequisites

⚠️ **Note:** Twitter API requires a paid subscription for posting (Basic tier: $100/month).

### Step 1: Apply for Developer Access

1. Go to [Twitter Developer Portal](https://developer.twitter.com/)
2. Sign up for **Basic** tier or higher
3. Create a project and app

### Step 2: Get API Keys

1. Go to your app's **Keys and Tokens** tab
2. Generate and copy:
   - **API Key** (Consumer Key)
   - **API Key Secret** (Consumer Secret)
   - **Access Token**
   - **Access Token Secret**

### Step 3: Configure Environment

Add to `.env`:
```bash
X_API_KEY=your_api_key
X_API_SECRET=your_api_secret
X_ACCESS_TOKEN=your_access_token
X_ACCESS_TOKEN_SECRET=your_access_token_secret
```

---

## Meta (Facebook/Instagram) API Setup

### Step 1: Create Facebook App

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Click **Create App**
3. Select **Business** type
4. Fill in app details

### Step 2: Add Products

1. Go to **Add Products**
2. Add **Facebook Login** and **Instagram Basic Display**

### Step 3: Get Page Access Token

1. Go to **Graph API Explorer**
2. Select your app
3. Add permissions:
   - `pages_manage_posts`
   - `pages_read_engagement`
   - `instagram_basic`
   - `instagram_content_publish`
4. Generate token

### Step 4: Get Long-Lived Token

```bash
curl -X GET "https://graph.facebook.com/v19.0/oauth/access_token?grant_type=fb_exchange_token&client_id=YOUR_APP_ID&client_secret=YOUR_APP_SECRET&fb_exchange_token=YOUR_SHORT_TOKEN"
```

### Step 5: Get Page ID

1. Go to your Facebook Page
2. Click **About** → **Page ID**
3. Or use Graph API:
   ```bash
   curl "https://graph.facebook.com/v19.0/me/accounts?access_token=YOUR_TOKEN"
   ```

### Step 6: Configure Environment

```bash
META_ACCESS_TOKEN=your_long_lived_token
META_PAGE_ID=your_page_id
META_IG_ACCOUNT_ID=your_instagram_id  # Optional
```

---

## Odoo Setup

### Step 1: Start Odoo

```bash
docker-compose up -d
```

### Step 2: Create Database

1. Open http://localhost:8069
2. Create database with:
   - Database name: `odoo`
   - Email: your admin email
   - Password: strong password
   - Demo data: No

### Step 3: Install Accounting Module

1. Go to **Apps**
2. Search for **Accounting**
3. Click **Install**

### Step 4: Configure Environment

```bash
ODOO_URL=http://localhost:8069
ODOO_DB=odoo
ODOO_USER=admin@example.com
ODOO_PASSWORD=your_password
```

---

## Cloud Agent Setup (Platinum)

### OpenAI API Key

1. Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Create new secret key
3. Add to `.env`:
   ```bash
   OPENAI_API_KEY=sk-...
   ```

### Xiaomi/GLM API Key

1. Go to [Xiaomi AI Platform](https://ai.xiaomi.com/)
2. Get API key for GLM models
3. Add to `.env`:
   ```bash
   XIAOMI_API_KEY=your_key
   MODEL_NAME=glm-4.7-flash
   ```

---

## Security Best Practices

### Credential Storage

```
✅ DO:
- Store credentials in .env file
- Use environment variables
- Keep .env in .gitignore
- Use OAuth when available
- Rotate tokens regularly

❌ DON'T:
- Commit credentials to git
- Share credentials in chat
- Hardcode secrets in code
- Use personal accounts for production
- Store tokens in vault (syncs to git)
```

### .gitignore Configuration

```gitignore
# Credentials
.env
credentials.json
token_*.json
*.pem
*.key

# Sessions
sessions/
.cache/

# Logs with sensitive data
Logs/gmail_processed_ids.txt
Logs/circuit_breakers.json
```

### Token Refresh

Most OAuth tokens expire and need refresh:

| Service | Token Lifetime | Auto-Refresh |
|---------|---------------|--------------|
| Gmail | 1 hour | ✅ Yes (refresh token) |
| LinkedIn | 60 days | ❌ Manual |
| Meta | 60 days | ❌ Manual |
| Twitter | Never | N/A |

### Access Control

**Local Environment:**
- Full access to all features
- Human-in-the-loop for approvals
- Direct MCP server access

**Cloud Environment:**
- Limited to drafting/reading
- Cannot execute approved actions
- Uses separate credentials

---

## Troubleshooting

### Gmail Token Expired

```bash
# Delete old token
rm ai_employee_scripts/token_gmail.json

# Re-authenticate
cd ai_employee_scripts
uv run python mcp_servers/gmail_mcp.py
```

### LinkedIn Token Invalid

```bash
# Generate new token
uv run python get_token.py

# Update .env
nano .env
# Update LINKEDIN_ACCESS_TOKEN
```

### Meta Token Expired

1. Go to Graph API Explorer
2. Generate new token
3. Exchange for long-lived token
4. Update `.env`

### Odoo Connection Failed

```bash
# Check Odoo is running
docker ps | grep odoo

# Check connection
curl http://localhost:8069

# Verify credentials in .env
cat ai_employee_scripts/.env | grep ODOO
```

---

## Credential Checklist

| Service | Required Files/Env Vars | Status |
|---------|------------------------|--------|
| Gmail | `credentials.json`, `token_gmail.json` | ⬜ |
| LinkedIn API | `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET`, `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_URN` | ⬜ |
| Twitter | `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET` | ⬜ |
| Meta | `META_ACCESS_TOKEN`, `META_PAGE_ID` | ⬜ |
| Odoo | `ODOO_URL`, `ODOO_DB`, `ODOO_USER`, `ODOO_PASSWORD` | ⬜ |
| Cloud | `OPENAI_API_KEY`, `XIAOMI_API_KEY` | ⬜ |

---

**Related Documentation:**
- [Configuration Reference](configuration-reference.md)
- [Getting Started Guide](getting-started.md)
- [Cloud Deployment Guide](cloud-deployment.md)