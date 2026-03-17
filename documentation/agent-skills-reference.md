# Agent Skills Reference

**Part of:** Personal AI Employee - Gold/Platinum Tier
**Last Updated:** March 2026

---

## Overview

Agent Skills are Claude Code agents that process tasks in the AI Employee system. Each skill is defined in a `SKILL.md` file and invoked via slash commands.

### Location

```
.claude/skills/
├── start-watcher/SKILL.md
├── stop-watcher/SKILL.md
├── process-tasks/SKILL.md
├── create-plan/SKILL.md
├── complete-task/SKILL.md
├── execute-approved/SKILL.md
├── linkedin-posting/SKILL.md
├── meta-posting/SKILL.md
├── twitter-posting/SKILL.md
├── create-invoice/SKILL.md
├── check-accounting/SKILL.md
├── weekly-audit/SKILL.md
├── mcp-integration/SKILL.md
└── openai-agents-sdk/SKILL.md
```

---

## Core Skills

### `/start-watcher`

**Purpose:** Start the FileSystemWatcher to monitor `drop_folder/` for new files.

**When to Use:**
- Beginning a work session
- After system restart
- When testing file processing

**What It Does:**
1. Checks if watcher is already running
2. Starts FileSystemWatcher as background process
3. Polls `drop_folder/` every 2 seconds
4. Copies new files to `Inbox/` with timestamp prefix
5. Creates task files in `Needs_Action/`

**Example Usage:**
```
/start-watcher
```

**Output:**
```
✅ FileSystemWatcher started
📁 Monitoring: /path/to/drop_folder
📝 Tasks will be created in: /path/to/AI_Employee_Vault/Needs_Action
```

---

### `/stop-watcher`

**Purpose:** Stop the FileSystemWatcher if running.

**When to Use:**
- Ending a work session
- Troubleshooting watcher issues
- Before making configuration changes

**Example Usage:**
```
/stop-watcher
```

**Output:**
```
✅ FileSystemWatcher stopped
```

---

### `/process-tasks`

**Purpose:** Process all pending tasks in `Needs_Action/`.

**When to Use:**
- When new tasks are detected
- After watcher creates tasks
- Manually processing backlog

**What It Does:**
1. Lists all `TASK_*.md` files in `Needs_Action/`
2. Reads each task's frontmatter and content
3. Analyzes task type and determines action
4. Creates plans for multi-step tasks
5. Drafts responses/approvals for single-step tasks
6. Moves completed tasks to `Done/`

**Task Types Handled:**
| Type | Action |
|------|--------|
| Email | Draft response in `Pending_Approval/` |
| Social | Generate post in `Pending_Approval/` |
| Invoice | Create draft in Odoo |
| File | Process based on content |
| Finance | Query Odoo, create summary |

**Example Usage:**
```
/process-tasks
```

**Output:**
```
📋 Found 3 tasks in Needs_Action/
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. TASK_EMAIL_client_inquiry_20260314.md
   → Drafted reply in Pending_Approval/

2. TASK_invoice_request_20260314.md
   → Created draft invoice in Odoo (ID: 15)

3. TASK_linkedin_post_20260314.md
   → Generated post in Pending_Approval/
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ All tasks processed
```

---

### `/create-plan`

**Purpose:** Create a structured execution plan for a specific task.

**When to Use:**
- Complex multi-step tasks
- Tasks requiring coordination
- Before executing sensitive operations

**What It Creates:**
- `Plans/PLAN_{timestamp}_{task_name}.md`

**Plan Structure:**
```markdown
# Plan: {Task Name}

## Objective
{What we're trying to accomplish}

## Analysis
{Current situation and requirements}

## Steps
1. {First step}
2. {Second step}
...

## Approval Required
{Whether human approval is needed}

## Expected Outcome
{What success looks like}
```

**Example Usage:**
```
/create-plan for TASK_migrate_database_20260314.md
```

---

### `/complete-task`

**Purpose:** Mark a task as completed and move to `Done/`.

**When to Use:**
- After successfully executing a task
- When task is no longer needed
- To archive completed work

**What It Does:**
1. Reads task file
2. Creates completion summary
3. Moves task to `Done/DONE_{task_name}_{timestamp}.md`
4. Updates any related files

**Example Usage:**
```
/complete-task TASK_EMAIL_client_20260314.md
```

**Output:**
```
✅ Task completed
📁 Moved to: Done/DONE_EMAIL_client_20260314_143022.md
```

---

### `/execute-approved`

**Purpose:** Execute all approved actions in `Approved/` folder.

**When to Use:**
- After human reviews and approves drafts
- Processing batch of approved items
- Final step in workflow

**What It Handles:**
| Action Type | MCP Tool | Result |
|-------------|----------|--------|
| LinkedIn Post | `mcp__linkedin-api__post_to_linkedin` | Posted to LinkedIn |
| Facebook Post | `mcp__meta__post_to_facebook` | Posted to Facebook |
| Instagram Post | `mcp__meta__post_to_instagram` | Posted to Instagram |
| Twitter Post | `mcp__twitter-api__post_tweet` | Tweeted |
| Email | `mcp__ai-gmail__send_email` | Email sent |
| Invoice | `mcp__odoo__post_invoice` | Invoice posted |

**Example Usage:**
```
/execute-approved
```

**Output:**
```
📋 Found 2 approved items
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. LINKEDIN_POST_ai_tips_20260314.md
   ✅ Posted to LinkedIn
   📝 Moved to: Content_To_Post/posted/

2. EMAIL_DRAFT_client_reply_20260314.md
   ✅ Email sent to: client@example.com
   📝 Moved to: Done/
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ All approved items executed
```

---

## Content Generation Skills

### `/linkedin-posting`

**Purpose:** Generate lead-generating LinkedIn post ideas.

**What It Creates:**
1. `Content_To_Post/queued/LINKEDIN_POST_{topic}_{date}.md` - Clean content backup
2. `Pending_Approval/LINKEDIN_POST_{topic}_{date}.md` - With human review section

**Post Structure:**
```markdown
---
platform: linkedin
created: 2026-03-14
status: pending_approval
topic: ai_productivity
---

# {Engaging Hook}

{Main content paragraph}

{Supporting points or tips}

{Call to action}

#hashtags

---

## Human Review Section
- [ ] Content accuracy
- [ ] Tone appropriateness
- [ ] Hashtag relevance
- [ ] CTA clarity

**Approve:** Move to `Approved/`
**Reject:** Move to `Content_To_Post/rejected/`
```

**Example Usage:**
```
/linkedin-posting topic: "AI productivity tips for small business"
```

---

### `/meta-posting`

**Purpose:** Generate Facebook/Instagram posts for business.

**Platform Options:**
- Facebook only (text + optional image URL)
- Instagram only (requires image URL)
- Both platforms

**What It Creates:**
1. `Content_To_Post/queued/META_POST_{topic}_{date}.md`
2. `Pending_Approval/META_POST_{topic}_{date}.md`

**Post Structure:**
```markdown
---
platform: meta
targets: [facebook, instagram]
created: 2026-03-14
status: pending_approval
image_url: (optional)
---

{Facebook text content}

---

{Instagram caption}

---

## Human Review Section
- [ ] Content appropriate for both platforms
- [ ] Image provided (required for Instagram)
- [ ] Target audience alignment
```

**Example Usage:**
```
/meta-posting topic: "New service announcement"
```

---

### `/twitter-posting`

**Purpose:** Generate engaging tweets for business growth.

**Constraints:**
- Max 280 characters (standard)
- Max 10,000 characters (Premium)

**What It Creates:**
1. `Content_To_Post/queued/TWITTER_POST_{topic}_{date}.md`
2. `Pending_Approval/TWITTER_POST_{topic}_{date}.md`

**Tweet Structure:**
```markdown
---
platform: twitter
created: 2026-03-14
status: pending_approval
character_count: 245
---

{Tweet content under 280 chars}

#hashtags

---

## Human Review Section
- [ ] Under 280 characters
- [ ] Hashtags relevant
- [ ] Engaging hook
```

**Example Usage:**
```
/twitter-posting topic: "Signs you need AI automation"
```

---

## Accounting Skills

### `/create-invoice`

**Purpose:** Create a draft invoice in Odoo accounting.

**What It Does:**
1. Uses Odoo MCP to create draft invoice
2. Auto-creates customer if not exists
3. Creates approval request in `Pending_Approval/`

**Parameters Gathered:**
- Customer name
- Invoice amount
- Description
- Currency (default: USD)

**Example Usage:**
```
/create-invoice
Customer: Acme Corporation
Amount: $2,500
Description: Web Development Services - March 2026
```

**Output:**
```
✅ Draft invoice created
📋 Invoice ID: 15
👤 Customer: Acme Corporation
💰 Amount: $2,500.00 USD
📝 Status: DRAFT

📄 Approval request created: Pending_Approval/FINANCE_DRAFT_20260314_143022.md
```

---

### `/check-accounting`

**Purpose:** Query Odoo for invoices, payments, revenue, and expenses.

**What It Returns:**
- Revenue totals (today, week, month, year)
- Expense totals
- Recent invoices
- Recent payments
- Outstanding balances

**Example Usage:**
```
/check-accounting period: this_month
```

**Output:**
```
📊 Financial Summary - March 2026
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 Revenue:    $12,500.00
💸 Expenses:   $2,300.00
📈 Profit:     $10,200.00

📋 Recent Invoices:
- INV/2026/0014: Acme Corp - $2,500 (Paid)
- INV/2026/0015: TechStart - $1,200 (Unpaid)

💵 Recent Payments:
- $2,500 from Acme Corp (Mar 10)
- $3,000 from DataFlow (Mar 8)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### `/weekly-audit`

**Purpose:** Generate comprehensive weekly CEO briefing.

**What It Includes:**
- Revenue and expenses for the week
- Invoice and payment activity
- Social media stats (posts, engagement)
- Email activity (processed, pending)
- Tasks completed
- Recommendations

**Output Location:** `Briefings/WEEKLY_{date}.md`

**Example Usage:**
```
/weekly-audit
```

**Output Structure:**
```markdown
# Weekly CEO Briefing - Week of March 8, 2026

## Financial Summary
{Revenue, expenses, profit}

## Invoice Activity
{New invoices, payments received}

## Social Media
{LinkedIn, Twitter, Meta posts}

## Email Activity
{Emails processed, pending}

## Tasks Completed
{Summary of completed work}

## Recommendations
{AI-suggested actions}

## Next Week Priorities
{Suggested focus areas}
```

**Automatic Delivery:**
The briefing can be automatically emailed to the CEO via Gmail MCP.

---

## Skill Workflow Summary

```
┌─────────────────────────────────────────────────────────────────────┐
│                     AGENT SKILL WORKFLOW                            │
└─────────────────────────────────────────────────────────────────────┘

PERCEPTION (Watchers)
FileSystemWatcher ──┐
GmailWatcher ───────┼──▶ Needs_Action/TASK_*.md
LinkedInWatcher ────┘
                                    │
                                    ▼
REASONING (Skills)
                          /process-tasks
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
             /create-plan    /linkedin-posting   /create-invoice
                    │               │               │
                    └───────────────┴───────────────┘
                                    │
                                    ▼
                          Pending_Approval/
                                    │
                                    │ Human reviews
                                    ▼
                            Approved/
                                    │
                                    ▼
ACTION (Skills + MCP)
                          /execute-approved
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            Gmail MCP       LinkedIn MCP      Odoo MCP
            (Send email)    (Post content)    (Post invoice)
                                    │
                                    ▼
                              Done/
```

---

## Quick Reference

| Skill | Purpose | Input | Output |
|-------|---------|-------|--------|
| `/start-watcher` | Start file monitoring | None | Watcher running |
| `/stop-watcher` | Stop file monitoring | None | Watcher stopped |
| `/process-tasks` | Process pending tasks | `Needs_Action/*.md` | Plans, approvals |
| `/create-plan` | Create execution plan | Task file | `Plans/PLAN_*.md` |
| `/complete-task` | Mark task complete | Task file | `Done/DONE_*.md` |
| `/execute-approved` | Execute approved actions | `Approved/*.md` | MCP calls |
| `/linkedin-posting` | Generate LinkedIn post | Topic | `Pending_Approval/` |
| `/meta-posting` | Generate FB/IG post | Topic | `Pending_Approval/` |
| `/twitter-posting` | Generate tweet | Topic | `Pending_Approval/` |
| `/create-invoice` | Create draft invoice | Customer, amount | Odoo draft |
| `/check-accounting` | Query financials | Period | Summary report |
| `/weekly-audit` | Generate CEO briefing | Week data | `Briefings/` |

---

**Related Documentation:**
- [Vault Structure Guide](vault-structure.md)
- [MCP Server Documentation](mcp/)
- [Getting Started Guide](getting-started.md)