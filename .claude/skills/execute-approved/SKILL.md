---
name: execute-approved
description: Execute approved LinkedIn posts, Meta posts (Facebook/Instagram), Twitter/X posts, Odoo invoices, and emails. Posts content via MCP tools, then moves and updates all related files.
---

# Execute Approved Actions - AUTOMATIC MODE

You are running in **automatic execution mode**. Human has already approved these actions - EXECUTE THEM NOW.

## YOUR MISSION:

Execute all approved actions in the `/Approved/` folder. These have been **pre-approved by the human** - no additional permission needed.

## MANDATORY STEPS - Do This For Each Approved Action:

1. **Read** the approved action file from `/Approved/`
2. **Parse** what action needs to be executed (check the `type:` field in frontmatter)
3. **EXECUTE** the action using available tools (MCP servers, file operations, etc.)
4. **Log** the result to `/Logs/`
5. **Move** the approved file to `/Done/`

---

## ACTION TYPES - How to Execute Each:

| Action Type | Frontmatter `type:` | How to Execute |
|-------------|-------------------|----------------|
| **Send Email** | `type: email` or `EMAIL_*` | Use Gmail MCP `mcp__ai-gmail__send_email` |
| **LinkedIn Post** | `type: linkedin_post` or `LINKEDIN_POST_*` | Use LinkedIn API MCP `mcp__linkedin-api__post_to_linkedin` |
| **Meta Post** | `type: meta_post` or `META_POST_*` | Use Meta MCP `mcp__meta__post_to_facebook`, `mcp__meta__post_to_instagram`, or `mcp__meta__post_to_both` |
| **Twitter Post** | `type: twitter_post` or `TWITTER_POST_*` | Use Twitter MCP `mcp__twitter-api__post_tweet` |
| **Reply to LinkedIn Message** | `type: linkedin_reply` | Use LinkedIn MCP `mcp__linkedin-mcp__reply_message` |
| **Post Odoo Invoice** | `type: approval_request` with `action: post_invoice` | Use Odoo MCP `mcp__odoo__post_invoice` |
| **File Operations** | `type: file_*` | Use Edit/Write tools directly |

---

## MCP Tools Available:

You have direct access to these MCP servers:
- **Odoo MCP** - `mcp__odoo__post_invoice`, `mcp__odoo__create_draft_invoice`, `mcp__odoo__get_invoices`, `mcp__odoo__get_payments`, `mcp__odoo__get_revenue`, `mcp__odoo__get_expenses`, `mcp__odoo__get_odoo_status`
- **Gmail MCP** - `mcp__ai-gmail__send_email`, `mcp__ai-gmail__read_email`, `mcp__ai-gmail__search_emails`, `mcp__ai-gmail__list_emails`
- **LinkedIn API MCP** - `mcp__linkedin-api__post_to_linkedin`, `mcp__linkedin-api__get_linkedin_profile`
- **LinkedIn MCP (Playwright)** - `mcp__linkedin-mcp__post_content`, `mcp__linkedin-mcp__reply_message`, `mcp__linkedin-mcp__get_messages`, `mcp__linkedin-mcp__verify_connection`
- **Meta MCP** - `mcp__meta__post_to_facebook`, `mcp__meta__post_to_instagram`, `mcp__meta__post_to_both`, `mcp__meta__get_meta_profile`, `mcp__meta__get_page_id_helper`
- **Twitter MCP** - `mcp__twitter-api__post_tweet`, `mcp__twitter-api__post_business_update`, `mcp__twitter-api__get_twitter_profile`

---

## TWITTER/X POST EXECUTION (Detailed)

When the approved file has `type: twitter_post` in frontmatter:

### Step 1: Read the Approved File
```
Read: /Approved/TWITTER_POST_*.md
```

### Step 2: Extract Post Content
Extract ONLY the actual tweet content (everything between the frontmatter `---` and the `## Human Section` or end of file).

**DO NOT INCLUDE:**
- YAML frontmatter (`---` sections)
- `## Human Section` and everything after it

### Step 3: Post Using Twitter API MCP
```
Use: mcp__twitter-api__post_tweet
Parameters:
  - text: [extracted tweet content as plain text]
```

### Step 4: Log the Result
Create log entry: `/Logs/TWITTER_POSTED_[timestamp].md`

### Step 5: Move and Update Files
1. Move approved file to `/Done/`
2. Move queued copy to `Content_To_Post/posted/`
3. Update frontmatter with `status: posted`, `posted: [timestamp]`, `posted_via: twitter_api_mcp`

---

## LINKEDIN POST EXECUTION (Detailed)

When the approved file has `type: linkedin_post`:

### Step 1: Read the Approved File
```
Read: /Approved/LINKEDIN_POST_*.md
```

### Step 2: Extract Post Content
Extract everything from the first `#` heading down to (but NOT including) `## Human Section`

### Step 3: Post Using LinkedIn API MCP
```
Use: mcp__linkedin-api__post_to_linkedin
Parameters:
  - text: [extracted post content]
```

### Step 4: Log and Move Files
1. Create log in `/Logs/LINKEDIN_POSTED_[timestamp].md`
2. Move approved file to `/Done/`
3. Move queued copy to `Content_To_Post/posted/`
4. Update frontmatter with posting metadata

---

## META POST EXECUTION (Detailed)

When the approved file has `type: meta_post` in frontmatter:

### Step 1: Read Human Section
Check platform selection:
- [ ] Facebook only
- [ ] Instagram only (requires image URL)
- [ ] Both Facebook and Instagram

### Step 2: Post Using Meta MCP
```
For Facebook only: mcp__meta__post_to_facebook(text="[content]")
For Instagram only: mcp__meta__post_to_instagram(caption="[content]", image_url="[URL]")
For both: mcp__meta__post_to_both(text="[FB content]", image_url="[URL]", instagram_caption="[IG content]")
```

### Step 3: Log and Move Files
1. Create log in `/Logs/META_POSTED_[timestamp].md`
2. Move approved file to `/Done/`
3. Move queued copy to `Content_To_Post/posted/`
4. Update frontmatter with platform and post IDs

---

## EMAIL EXECUTION (Detailed)

When the approved file has `type: email` or starts with `EMAIL_`:

1. **Extract email details:** `to:`, `subject:`, `body:`
2. **Send using Gmail MCP:** `mcp__ai-gmail__send_email`
3. **Log and move to Done**

---

## ODOO INVOICE POSTING (Detailed)

When the approved file has `type: approval_request` with `action: post_invoice`:

1. **Read** the approved file
2. **Extract** `invoice_id`, `customer`, `amount` from frontmatter
3. **Post** using `mcp__odoo__post_invoice(invoice_id=[id])`
4. **Log** the result to `/Logs/INVOICE_POSTED_[timestamp].md`
5. **Move** to `/Done/`

---

## CRITICAL RULES:

- **DO NOT ASK** for approval - already approved!
- **EXECUTE IMMEDIATELY** - don't delay
- **USE MCP TOOLS** - Odoo, Gmail, LinkedIn, Meta, Twitter are available
- **LOG EVERYTHING** - create log entries for all actions
- **MOVE TO DONE** - after execution, move the file

---

**START EXECUTING NOW - DON'T WAIT FOR PERMISSION**
