# Vault Structure Guide

**Part of:** Personal AI Employee - Gold/Platinum Tier
**Last Updated:** March 2026

---

## Overview

The AI Employee Vault is an Obsidian workspace that serves as the system's memory and state management. It stores all tasks, plans, approvals, logs, and configuration in human-readable Markdown format.

### Location

```
AI_Employee_Vault/
```

---

## Directory Structure

```
AI_Employee_Vault/
├── Inbox/                    # Raw data from watchers
├── Needs_Action/             # Task queue (watchers create here)
├── Plans/                    # Execution strategies (Claude creates)
├── Pending_Approval/         # Awaiting human review
├── Approved/                 # Human-approved, ready to execute
├── Rejected/                 # Human-rejected actions
├── Done/                     # Completed tasks with summaries
├── Failed/                   # Dead letter queue (failed items)
├── In_Progress/              # Work-in-progress (Platinum tier)
├── Logs/                     # System logs and state files
├── Accounting/               # Financial records
├── Content_To_Post/          # Social media queue
│   ├── queued/               # Generated, not yet reviewed
│   ├── posted/               # Successfully posted
│   └── rejected/             # Rejected posts
├── Briefings/                # CEO weekly briefings
├── Updates/                  # Status updates and drafts
├── .claude/                  # Claude Code configuration
│   └── skills/               # Agent skill definitions
├── Company_Handbook.md       # Rules and approval thresholds
├── Dashboard.md              # System status overview
├── AGENTS.md                 # Agent behavior instructions
├── Business_Goals.md         # Business objectives
└── .mcp.json                 # MCP server configurations
```

---

## Core Directories

### Inbox/

**Purpose:** Raw data storage from watchers.

**Files:** `EMAIL_*.md`, `FILE_*.md`, etc.

**Naming Convention:** `{TYPE}_{subject}_{timestamp}.md`

**Example:**
```
Inbox/
├── EMAIL_client_inquiry_20260314_100530.md
├── EMAIL_project_update_20260314_103045.md
└── FILE_contract_20260314_111500.md
```

**File Format:**
```markdown
---
message_id: 1234567890abcdef
from: client@example.com
to: me@company.com
subject: Project Update Request
date: 2026-03-14T10:30:00
---

Email content here...
```

---

### Needs_Action/

**Purpose:** Task queue for Claude to process.

**Files:** `TASK_*.md`, `EMAIL_*.md`

**Naming Convention:** `TASK_{type}_{description}_{timestamp}.md`

**Example:**
```
Needs_Action/
├── TASK_EMAIL_client_inquiry_20260314_100530.md
├── TASK_invoice_request_20260314_103045.md
└── TASK_linkedin_post_20260314_111500.md
```

**Task File Format:**
```markdown
---
type: task
source: GmailWatcher
created: 2026-03-14T10:05:30
status: pending
priority: medium
original_file: EMAIL_client_inquiry_20260314_100530.md
---

# Task: Process Email

## Context
From: client@example.com
Subject: Project Update Request

## Instructions
1. Read the original email in Inbox/
2. Determine appropriate response
3. Draft reply for approval if needed
4. Update Dashboard.md with status
```

---

### Plans/

**Purpose:** Execution strategies for complex tasks.

**Files:** `PLAN_*.md`

**Naming Convention:** `PLAN_{task_name}_{timestamp}.md`

**Example:**
```
Plans/
├── PLAN_migrate_database_20260314_100000.md
└── PLAN_client_onboarding_20260314_120000.md
```

**Plan Format:**
```markdown
---
task: migrate_database
created: 2026-03-14T10:00:00
status: in_progress
steps_total: 5
steps_completed: 2
---

# Plan: Database Migration

## Objective
Migrate customer database from old system to Odoo.

## Analysis
- 500+ customer records
- Need to preserve all history
- Downtime window: 2 hours

## Steps
1. ✅ Export data from old system
2. ✅ Transform data to Odoo format
3. ⬜ Import to Odoo
4. ⬜ Verify data integrity
5. ⬜ Update documentation

## Approval Required
Yes - for final import step

## Expected Outcome
All customers migrated to Odoo with preserved history.
```

---

### Pending_Approval/

**Purpose:** Items awaiting human review before execution.

**Files:** Various draft types

**Types:**
| Prefix | Description |
|--------|-------------|
| `EMAIL_DRAFT_*` | Email drafts |
| `LINKEDIN_POST_*` | LinkedIn posts |
| `META_POST_*` | Facebook/Instagram posts |
| `TWITTER_POST_*` | Twitter tweets |
| `FINANCE_DRAFT_*` | Invoice drafts |

**Example:**
```
Pending_Approval/
├── EMAIL_DRAFT_client_reply_20260314_103000.md
├── LINKEDIN_POST_ai_tips_20260314_110000.md
└── FINANCE_DRAFT_acme_invoice_20260314_120000.md
```

**Approval File Format:**
```markdown
---
type: email_draft
created: 2026-03-14T10:30:00
status: pending_approval
original_task: TASK_EMAIL_client_20260314_100530.md
---

# Email Draft

**To:** client@example.com
**Subject:** Re: Project Update Request

Hi [Client],

Thank you for reaching out about the project status...

[Email body]

---

## Human Review Section
- [ ] Content accuracy
- [ ] Tone appropriate
- [ ] No sensitive information

**Approve:** Move to `Approved/`
**Reject:** Move to `Rejected/`
**Edit:** Make changes then approve
```

---

### Approved/

**Purpose:** Items approved by human, ready for execution.

**Files:** Same format as Pending_Approval

**Workflow:**
1. Human reviews item in Pending_Approval/
2. Human moves file to Approved/
3. Orchestrator detects change
4. `/execute-approved` skill executes via MCP
5. File moved to Done/

---

### Rejected/

**Purpose:** Items rejected by human.

**Files:** Same format as Pending_Approval with rejection reason

**Rejection Format:**
```markdown
---
type: email_draft
created: 2026-03-14T10:30:00
status: rejected
rejected_at: 2026-03-14T11:00:00
rejection_reason: "Tone too formal for this client"
---

[Original draft content]

---
## Rejection Notes
Tone too formal - client prefers casual communication.
```

---

### Done/

**Purpose:** Completed tasks with execution summaries.

**Files:** `DONE_*.md`

**Naming Convention:** `DONE_{task_type}_{description}_{completion_timestamp}.md`

**Example:**
```
Done/
├── DONE_EMAIL_client_20260314_103022.md
├── DONE_LINKEDIN_ai_tips_20260314_110530.md
└── DONE_invoice_acme_20260314_120145.md
```

**Completion Format:**
```markdown
---
type: completed_task
original_task: TASK_EMAIL_client_20260314_100530.md
completed_at: 2026-03-14T10:30:22
execution_time_seconds: 45
---

# Completed: Email Response

## Summary
Drafted and sent response to client inquiry.

## Actions Taken
1. Read original email
2. Checked customer history in Odoo
3. Drafted response
4. Human approved
5. Sent via Gmail MCP

## Result
Email sent successfully to client@example.com
Message ID: 18c4d5e6f7g8h9

## Files
- Original: Inbox/EMAIL_client_inquiry_20260314_100530.md
- Task: Needs_Action/TASK_EMAIL_client_20260314_100530.md
- Draft: Pending_Approval/EMAIL_DRAFT_client_20260314_103000.md
```

---

### Failed/

**Purpose:** Dead letter queue for failed watcher items.

**Structure:**
```
Failed/
├── GmailWatcher/
│   ├── item_12345.json
│   └── item_67890.json
├── LinkedInWatcher/
│   └── item_abcde.json
└── FileSystemWatcher/
    └── item_fghij.json
```

**Failed Item Format:**
```json
{
  "item_id": "12345",
  "failed_at": "2026-03-14T10:30:00",
  "error": "Connection timeout",
  "attempts": 3,
  "context": {
    "source": "GmailWatcher",
    "message_id": "12345"
  },
  "content": "Original item content..."
}
```

---

### In_Progress/

**Purpose:** Work-in-progress items (Platinum tier cloud zone).

**Structure:**
```
In_Progress/
├── cloud/
│   ├── TASK_email_drafting_20260314.md
│   └── TASK_social_content_20260314.md
└── local/
    └── TASK_manual_review_20260314.md
```

**Claim-by-Move Rule:**
- Cloud agent claims task by moving to `In_Progress/cloud/`
- Local agent claims by moving to `In_Progress/local/`
- Prevents duplicate work

---

### Logs/

**Purpose:** System logs and state files.

**Files:**
| File | Purpose |
|------|---------|
| `orchestrator_YYYYMMDD.log` | Daily orchestrator logs |
| `watchdog.log` | Watchdog events |
| `watcher.log` | Watcher errors |
| `circuit_breakers.json` | Circuit breaker states |
| `health_status.json` | Component health |
| `gmail_processed_ids.txt` | Processed email IDs |
| `process_events.jsonl` | Process lifecycle events |
| `vault_sync.log` | Git sync activity |

**Example Log Entry:**
```
2026-03-14 10:30:45 | GmailWatcher | INFO | Found 2 new emails
2026-03-14 10:30:46 | GmailWatcher | INFO | Created task: TASK_EMAIL_client_20260314_100530.md
```

---

### Accounting/

**Purpose:** Financial records and reference data.

**Files:**
| File | Purpose |
|------|---------|
| `Rates.md` | Service pricing |
| `invoices_*.md` | Invoice records |
| `payments_*.md` | Payment records |

**Rates.md Example:**
```markdown
# Service Rates

## Hourly Rates
| Service | Rate |
|---------|------|
| Consulting | $150/hr |
| Development | $125/hr |
| Design | $100/hr |
| Video Editing | $80/hr |

## Project Packages
| Package | Price |
|---------|-------|
| Website Basic | $3,000 |
| Website Premium | $7,500 |
| AI Integration | $5,000+ |
```

---

### Content_To_Post/

**Purpose:** Social media content queue.

**Structure:**
```
Content_To_Post/
├── queued/
│   ├── LINKEDIN_POST_ai_tips_20260314.md
│   ├── TWITTER_POST_signs_ai_20260314.md
│   └── META_POST_business_20260314.md
├── posted/
│   ├── LINKEDIN_POST_productivity_20260313.md
│   └── TWITTER_POST_automation_20260313.md
└── rejected/
    └── META_POST_offbrand_20260312.md
```

**Post File Format:**
```markdown
---
platform: linkedin
created: 2026-03-14
status: queued
scheduled: 2026-03-15T08:00:00
---

# Post Content

5 AI automation mistakes that are costing you hours:

1. Not documenting your workflows
2. Over-automating too fast
3. Skipping the testing phase
4. Ignoring error handling
5. Forgetting about maintenance

Which one resonates with you?

#AI #Automation #Productivity
```

---

### Briefings/

**Purpose:** CEO weekly briefings.

**Files:** `WEEKLY_{date_range}.md`

**Format:** See `/weekly-audit` skill documentation.

---

## Configuration Files

### Company_Handbook.md

Rules and approval thresholds for the AI Employee.

```markdown
# Company Handbook

## Auto-Approve Actions
- Reading data
- Creating drafts
- File organization within vault
- Logging and monitoring

## Require Human Approval
- Emails to new contacts
- Social media posts
- Invoice creation
- Payments > $50
- Deleting files

## Never Allowed
- Payments to new recipients without approval
- Sharing credentials
- Legal/medical advice
- Emotional contexts
```

### Dashboard.md

System status overview.

```markdown
# AI Employee Dashboard

## Status: 🟢 Operational

## Active Watchers
- FileSystemWatcher: Running
- GmailWatcher: Running
- LinkedInWatcher: Running

## Recent Activity
| Time | Action | Status |
|------|--------|--------|
| 10:30 | Email processed | ✅ Done |
| 10:15 | LinkedIn post drafted | ⏳ Pending |
| 10:00 | File processed | ✅ Done |

## Pending Items
- 2 items in Pending_Approval/
- 0 items in Needs_Action/
```

### Business_Goals.md

Business objectives for content generation.

```markdown
# Business Goals

## Services
- AI Automation Consulting
- Custom AI Development
- Workflow Design
- Digital FTE Implementation

## Target Audience
- Small business owners
- Solo entrepreneurs
- Agencies looking to scale

## Content Topics
- AI productivity tips
- Automation case studies
- Workflow optimization
- Digital FTE benefits
```

### .mcp.json

MCP server configurations.

```json
{
  "mcpServers": {
    "ai-gmail": {
      "type": "stdio",
      "command": "uv",
      "args": ["--directory", "/path/to/scripts", "run", "mcp_servers/gmail_mcp.py"]
    },
    "odoo": { ... },
    "linkedin-api": { ... },
    "linkedin-mcp": { ... },
    "twitter-api": { ... },
    "meta": { ... }
  }
}
```

---

## File Workflow Summary

```
┌─────────────────────────────────────────────────────────────────────┐
│                     FILE WORKFLOW                                    │
└─────────────────────────────────────────────────────────────────────┘

Watcher detects item
        │
        ▼
┌───────────────┐     ┌───────────────┐
│    Inbox/     │     │ Needs_Action/ │
│  (raw data)   │────▶│  (task file)  │
└───────────────┘     └───────┬───────┘
                              │
                              ▼
                      ┌───────────────┐
                      │ Claude Code   │
                      │ /process-tasks│
                      └───────┬───────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
      ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
      │    Plans/     │ │Pending_Approval│ │    Done/      │
      │(multi-step)   │ │ (needs review) │ │ (completed)   │
      └───────────────┘ └───────┬───────┘ └───────────────┘
                              │
                      Human reviews
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
      ┌───────────────┐               ┌───────────────┐
      │   Approved/   │               │   Rejected/   │
      └───────┬───────┘               └───────────────┘
              │
              ▼
      ┌───────────────┐
      │/execute-approved│
      │   (MCP calls)  │
      └───────┬───────┘
              │
              ▼
      ┌───────────────┐
      │    Done/      │
      └───────────────┘
```

---

**Related Documentation:**
- [Agent Skills Reference](agent-skills-reference.md)
- [Getting Started Guide](getting-started.md)
- [Configuration Reference](configuration-reference.md)