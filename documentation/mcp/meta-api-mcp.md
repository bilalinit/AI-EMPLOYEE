# Meta Graph API MCP Server Documentation

## Overview

The Meta Graph API MCP Server provides Facebook Page and Instagram Business posting functionality via the Meta Graph API v21.0. It enables posting content to both platforms simultaneously using a long-lived access token.

**Location:** `ai_employee_scripts/mcp_servers/meta_mcp.py`

**MCP Name:** `meta-api`

---

## Features

### Available Tools

| Tool | Description | Async |
|------|-------------|-------|
| `post_to_facebook` | Post text update to Facebook Page | No |
| `post_to_instagram` | Post image with caption to Instagram Business | No |
| `post_to_both` | Post to both Facebook and Instagram simultaneously | No |
| `get_meta_profile` | Get Facebook Page and Instagram account info | No |
| `get_page_id_helper` | Find your Facebook Page IDs | No |

### Tool Parameters

#### `post_to_facebook`

```python
mcp__meta-api__post_to_facebook(
    text: str    # Post content for Facebook
)
```

**Returns:** Success message with post ID and Facebook URL

**Note:** Facebook supports text-only posts. Images can be included via URL in the text.

#### `post_to_instagram`

```python
mcp__meta-api__post_to_instagram(
    caption: str,    # Caption for Instagram post (max 2200 characters)
    image_url: str   # Publicly accessible image URL (JPEG/PNG)
)
```

**Returns:** Success message with media ID and caption preview

**Important:** Instagram **requires** a publicly accessible image URL. The image must be hosted on a public server (not localhost or file://).

#### `post_to_both`

```python
mcp__meta-api__post_to_both(
    text: str,                      # Text content for Facebook
    image_url: str = "",            # Public image URL (required for Instagram)
    instagram_caption: str = ""     # Custom Instagram caption (uses text if not provided)
)
```

**Returns:** Combined results for both platforms

**Behavior:**
- **Facebook:** Posts text content (image optional via URL in text)
- **Instagram:** Posts only if `image_url` is provided

#### `get_meta_profile`

```python
mcp__meta-api__get_meta_profile()
```

**Returns:** Profile information including:
- Facebook Page: name, followers, likes
- Instagram Business: username, followers, media count, bio (if linked)

#### `get_page_id_helper`

```python
mcp__meta-api__get_page_id_helper()
```

**Returns:** List of all Facebook Pages you manage with their IDs

**Use this if:** You don't know your `META_PAGE_ID`

---

## Setup Guide

### Prerequisites

- **Python 3.13+** with UV package manager
- **Facebook Account**
- **Instagram Business or Creator account**
- **Claude Code installed and working**

### Step 1: Convert Instagram to Professional Account

On your phone in the Instagram app:

1. Go to your **Profile** → Tap the three lines (☰) (top right)
2. Tap **Settings and privacy**
3. Tap **Account type and tools**
4. Tap **Switch to Professional account**
5. Choose **Business**

### Step 2: Create a Facebook Page

1. Go to [facebook.com/pages/create](https://www.facebook.com/pages/create)
2. Enter a page name and category
3. Click **Create Page**

**Then link your Instagram to the Page:**

1. Open your Facebook Page
2. Go to **Settings** → **Instagram**
3. Click **Connect account** and log in to Instagram

### Step 3: Create Meta Developer App

1. Go to [developers.facebook.com](https://developers.facebook.com)
2. Click **My Apps** → **Create App**
3. Select **Other** → **Business**
4. Fill in app name (e.g., "digital-FTEs") and your email
5. Click **Create App**

### Step 4: Add Use Cases

Inside your app dashboard:

1. Click **Add use cases**
2. Select:
   - ✅ **Manage messaging & content on Instagram**
   - ✅ **Manage everything on your Page** (for Facebook posting)
3. Click **Save**

### Step 5: Get Your Access Token

#### 5a: Generate Short-Lived Token

1. Go to [Graph API Explorer](https://developers.facebook.com/tools/explorer)
2. Select your app in the **Meta App** dropdown (top right)
3. In the **User or Page** dropdown, select your **Facebook Page** (NOT "User Token")
4. Add these permissions:
   - ✅ `pages_show_list`
   - ✅ `pages_manage_posts`
   - ✅ `pages_manage_metadata`
   - ✅ `instagram_basic`
   - ✅ `instagram_content_publish`
   - ✅ `pages_read_engagement`
5. Click **Generate Access Token**
6. Select your Facebook Page in the popup and click **Continue**
7. Copy the token using the copy icon

#### 5b: Exchange for Long-Lived Token (60 Days)

**Find your App ID and App Secret:**
- Your app dashboard → **App settings** → **Basic**

**Run in terminal:**
```bash
curl "https://graph.facebook.com/v25.0/oauth/access_token?grant_type=fb_exchange_token&client_id=YOUR_APP_ID&client_secret=YOUR_APP_SECRET&fb_exchange_token=PASTE_SHORT_TOKEN_HERE"
```

**Response:**
```json
{
  "access_token": "your_long_lived_token_here...",
  "token_type": "bearer",
  "expires_in": 5183538
}
```

Copy the `access_token` — this lasts **60 days**.

### Step 6: Get Your Page ID

**Run in terminal:**
```bash
curl "https://graph.facebook.com/v25.0/me/accounts?access_token=YOUR_LONG_LIVED_TOKEN"
```

**Response:**
```json
{
  "data": [
    {
      "id": "1234567890",
      "name": "Your Page Name",
      ...
    }
  ]
}
```

The `id` field is your **Page ID**.

### Step 7: Add Credentials to .env

Add to `ai_employee_scripts/.env`:

```bash
META_ACCESS_TOKEN=your_long_lived_token_here
META_PAGE_ID=your_facebook_page_id_here
```

### Step 8: Install Dependencies

```bash
cd ai_employee_scripts
uv sync
```

Required packages:
- `httpx>=0.28.1`
- `mcp>=0.1.0`

---

## Configuration

### MCP Server Configuration

The Meta API MCP is configured in `AI_Employee_Vault/.mcp.json`:

```json
{
  "mcpServers": {
    "meta-api": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/ai-employee/ai_employee_scripts",
        "run",
        "mcp_servers/meta_mcp.py"
      ],
      "env": {
        "PYTHONPATH": "/path/to/ai-employee/ai_employee_scripts"
      }
    }
  }
}
```

**Replace:** `/path/to/ai-employee` with your actual project path

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `META_ACCESS_TOKEN` | Long-lived Meta access token (60 days) | Yes |
| `META_PAGE_ID` | Your Facebook Page ID | Yes |

---

## Authentication

### Long-Lived Access Token Flow

```
┌─────────────────────────────────────┐
│  Step 1: Convert Instagram          │
│  (Phone app → Professional account) │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Step 2: Create Facebook Page       │
│  Link Instagram to Page             │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Step 3: Create Meta Developer App  │
│  (developers.facebook.com)          │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Step 4: Add Use Cases              │
│  - Manage messaging on Instagram    │
│  - Manage everything on Page        │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Step 5a: Generate Short Token      │
│  Graph API Explorer                 │
│  (Select Page, add permissions)     │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Step 5b: Exchange for Long Token   │
│  curl -fb_exchange_token            │
│  (Returns 60-day token)             │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Step 6: Get Page ID                │
│  curl /me/accounts                  │
│  (Returns page info with ID)        │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Add to .env:                       │
│  META_ACCESS_TOKEN=xxx              │
│  META_PAGE_ID=xxx                   │
└─────────────────────────────────────┘
```

### Token Refresh

Long-lived tokens expire after **60 days**. To refresh:

1. Use the **Access Token Tool** in Meta Developer Portal
2. Or regenerate via Graph API Explorer
3. Update `META_ACCESS_TOKEN` in `.env`

---

## Usage Examples

### In Agent Skills

#### Posting to Facebook (execute-approved skill)

```python
# Post to Facebook only
result = mcp__meta-api__post_to_facebook(
    text="Just launched our new AI automation feature! Check it out at our-website.com #AI #automation"
)
```

#### Posting to Instagram (execute-approved skill)

```python
# Post to Instagram with image
result = mcp__meta-api__post_to_instagram(
    caption="New feature launch! 🚀 Automate your workflows with our AI Employee. #AI #automation",
    image_url="https://example.com/images/launch-photo.jpg"
)
```

#### Posting to Both Platforms

```python
# Post to both Facebook and Instagram
result = mcp__meta-api__post_to_both(
    text="Excited to announce our new AI Employee feature! #automation",
    image_url="https://example.com/images/feature.jpg",
    instagram_caption="Automate everything with AI Employee 🚀 #AI #automation"
)
```

#### Finding Your Page ID

```python
# If you don't know your Page ID
pages = mcp__meta-api__get_page_id_helper()
print(pages)
# Output shows all your Pages with their IDs
```

---

## Files and Paths

| File | Location | Purpose |
|------|----------|---------|
| MCP Server | `ai_employee_scripts/mcp_servers/meta_mcp.py` | Main MCP server code |
| Credentials | `ai_employee_scripts/.env` | Meta access token and Page ID |
| MCP Config | `AI_Employee_Vault/.mcp.json` | MCP server configuration |

---

## Troubleshooting

### Issue: "Missing credentials"

**Error Message:**
```
❌ Missing credentials: META_ACCESS_TOKEN, META_PAGE_ID
```

**Solution:**
Add both to `ai_employee_scripts/.env`:
```bash
META_ACCESS_TOKEN=your_token_here
META_PAGE_ID=your_page_id_here
```

---

### Issue: "No Page access token returned"

**Error Message:**
```
Error: No Page access token returned. Make sure pages_manage_posts permission is granted.
```

**Solution:**
1. Regenerate access token with correct permissions:
   - `pages_manage_posts`
   - `pages_read_engagement`
2. Make sure token is a **Page access token**, not a User access token

---

### Issue: "No Instagram Business account found"

**Error Message:**
```
Error: No Instagram Business account found linked to your Facebook Page.
Fix: Go to your Facebook Page Settings → Instagram → Connect account
```

**Solution:**
1. Go to your Facebook Page
2. **Settings** → **Instagram**
3. Click **"Connect account"**
4. Log in with your Instagram Business account
5. Ensure it's a **Business** account, not personal

---

### Issue: Instagram "Media processing failed"

**Error Message:**
```
Error: Media processing failed with status ERROR
```

**Solution:**
1. Verify image URL is **publicly accessible**
2. Try opening the image URL in incognito mode
3. Ensure image is **JPEG or PNG** format
4. Image should be under 30MB
5. URL must be HTTPS with valid SSL certificate

---

### Issue: "Request timed out"

**Error Message:**
```
Error: Request timed out. Meta API took too long to respond.
```

**Solution:**
1. Check internet connection
2. Instagram media processing can take 30+ seconds
3. Try again - may be temporary API slowdown

---

## Instagram Posting Flow

### Container → Publish Flow

```
┌─────────────────────────────────────┐
│  1. Create Media Container          │
│  POST /{ig_account_id}/media        │
│  {image_url, caption}               │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  2. Poll Media Status              │
│  GET /{ig_account_id}/media         │
│  Wait for status_code=FINISHED      │
│  (Up to 30 seconds, 3s intervals)   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  3. Publish Container               │
│  POST /{ig_account_id}/media_publish│
│  {creation_id}                      │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  4. Post Published                  │
│  Returns media_id                   │
└─────────────────────────────────────┘
```

---

## Skills Using Meta API MCP

| Skill | Tools Used | Description |
|-------|------------|-------------|
| `execute-approved` | All posting tools | Posts approved Meta content |
| `meta-posting` | Content generation | Creates Meta posts (uses execute-approved to post) |

---

## Dependencies

```
httpx>=0.28.1
mcp>=0.1.0
```

Install via:
```bash
cd ai_employee_scripts
uv sync
```

---

## API Reference

### Facebook Page Feed Endpoint

```
POST https://graph.facebook.com/v21.0/{page_id}/feed
```

**Parameters:**
- `message`: Post content
- `access_token`: Page access token

### Instagram Media Endpoints

```
POST https://graph.facebook.com/v21.0/{ig_account_id}/media
```
**Parameters:**
- `image_url`: Public image URL
- `caption`: Post caption (max 2200)

```
POST https://graph.facebook.com/v21.0/{ig_account_id}/media_publish
```
**Parameters:**
- `creation_id`: ID from media container response

---

## Security Notes

1. **Never commit** `.env` file with access token to git
2. **Never share** your long-lived access token
3. **Token expires** after 60 days - refresh periodically
4. **Use Page access token** - not User access token
5. **App Secret** should never be in client-side code

---

## Related Documentation

- [Meta Graph API Documentation](https://developers.facebook.com/docs/graph-api)
- [Instagram Graph API](https://developers.facebook.com/docs/instagram-api)
- [Meta for Developers](https://developers.facebook.com/)
- [Execute Approved Skill](../../.claude/skills/execute-approved/SKILL.md)
- [Meta Posting Skill](../../.claude/skills/meta-posting/SKILL.md)

---

*Generated: 2026-02-28*
*AI Employee Project - Gold Tier Documentation*
