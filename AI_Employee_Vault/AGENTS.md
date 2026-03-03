# AGENTS.md

**Version:** 1.0
**Last Updated:** 2026-02-16

---

## Purpose

This file defines **technical agent behavior rules** for the AI Employee system. It complements `Company_Handbook.md` (business rules) by focusing on **HOW agents should operate**, coordinate, and interact with the system.

---

## ⚠️ CRITICAL CONSTRAINT

### All Agent Actions MUST Stay Inside AI_Employee_Vault/

| Rule | Details |
|------|---------|
| **ONLY** | Agents may only take actions **inside** `/AI_Employee_Vault/` |
| **FORBIDDEN** | Any action outside `/AI_Employee_Vault/` is strictly prohibited |
| **External Actions** | Use **MCP tools** for actions outside the vault |

### Allowed Actions Inside Vault

- Read, write, move files within `/AI_Employee_Vault/`
- Create task files in `/Needs_Action/`
- Create plans in `/Plans/`
- Log to `/Logs/`
- Move completed items to `/Done/`

### External Actions Require MCP Tools

For any action outside the vault, agents MUST use MCP tools:

| External Action | MCP Tool |
|-----------------|----------|
| Sending emails | Gmail MCP (`mcp__ai-gmail__send_email`) |
| Posting to LinkedIn | LinkedIn MCP (`mcp__linkedin-mcp__post_content`) |
| Replying to LinkedIn messages | LinkedIn MCP (`mcp__linkedin-mcp__reply_message`) |
| Fetching LinkedIn messages | LinkedIn MCP (`mcp__linkedin-mcp__get_messages`) |
| Sending WhatsApp | WhatsApp MCP |
| Social media posts | LinkedIn/Twitter MCP |
| Financial transactions | Banking/Odoo MCP |
| Other external APIs | Appropriate MCP server |

### Important

- **NEVER** attempt to modify files outside `/AI_Employee_Vault/`
- **NEVER** access `ai_employee_scripts/` (contains secrets)
- **ALWAYS** use MCP tools for external actions
- **ALL** planning and coordination happens inside the vault

---

## 1. Agent Identity & Scope

### What is an AI Employee Agent?

An AI Employee agent is an autonomous component in the **Perception → Reasoning → Action** pipeline:

| Layer | Purpose | Agent Type |
|-------|---------|------------|
| **Perception** | Detect external changes | Watcher Agents (Python scripts) |
| **Reasoning** | Analyze and plan | Claude Code (via Agent Skills) |
| **Action** | Execute approved actions | MCP Servers, Skills |

### Agent Types

1. **Watcher Agents** (`ai_employee_scripts/watchers/*.py`)
   - Monitor external sources (filesystem, Gmail, WhatsApp)
   - Create task files in `/Needs_Action/`
   - Run 24/7 in background

2. **Reasoning Agents** (Claude Code via Agent Skills)
   - Process tasks from `/Needs_Action/`
   - Create plans in `/Plans/`
   - Request approval via `/Pending_Approval/`

3. **Action Agents** (MCP Servers, Skills)
   - Execute human-approved actions
   - Log results to `/Done/`

---

## 2. Autonomy Rules

### Act Autonomously When

- Task is clearly spam, test, or automated notification
- File organization within the vault only
- Reading and analyzing content (no external action)
- Logging transactions

### Request Approval When

- See `Company_Handbook.md` → Approval Thresholds
- Any action outside the vault
- Communication to external parties
- Financial transactions
- Deleting files

### Decision-Making

- **High confidence (>90%)** → Act autonomously if safe
- **Medium confidence (50-90%)** → Create plan, may require approval
- **Low confidence (<50%)** → Always request human input

---

## 3. Task Processing Rules (CRITICAL)

### /process-tasks Automatic Mode

The `/process-tasks` skill runs in **AUTOMATIC MODE**:
- **DO NOT ASK** for confirmation
- **DO NOT WAIT** — TAKE ACTION directly
- **ALWAYS** move processed tasks to `/Done/`

### Task Categorization

| Category | Action | Examples |
|----------|--------|----------|
| **Spam/Test** | Move to `/Done/` immediately | Automated notifications, test messages |
| **Real Action** | Create plan + approval request | Invoice requests, client messages |
| **Already Processed** | Move to `/Done/` | Duplicate tasks, completed items |

### File Reading Order

1. Read task file from `/Needs_Action/TASK_*.md`
2. Read original file from `/Inbox/` (reference in task frontmatter)
3. Analyze content and determine action
4. Create plan OR move to `/Done/`

### Task File Format Reference

See task files in `/Needs_Action/TASK_*.md` for frontmatter format.

---

## 4. File Operations Rules

### ⚠️ VAULT BOUNDARY (CRITICAL)

| Rule | Details |
|------|---------|
| **BOUNDARY** | `/AI_Employee_Vault/` is the ONLY allowed workspace |
| **EXTERNAL** | All external actions MUST use MCP tools |
| **SECRETS** | NEVER access `ai_employee_scripts/` (contains secrets) |

### Safe Operations (Always Allowed)

| Operation | Scope |
|-----------|-------|
| **Read** | Any file in `/AI_Employee_Vault/` |
| **Write** | Within `/AI_Employee_Vault/` only |
| **Move** | Between vault folders (Inbox, Needs_Action, Plans, Pending_Approval, Done) |
| **Copy** | From `drop_folder/` to `/Inbox/` (Watcher only) |

### Prohibited Operations (Never Allowed)

| Operation | Restriction |
|-----------|-------------|
| **Delete** | Without approval, or outside vault |
| **Modify** | ANY file outside `/AI_Employee_Vault/` |
| **Access** | `ai_employee_scripts/` (contains secrets) |
| **Execute** | Any command that affects files outside vault |

### File Movement Workflow

```
drop_folder/ → /Inbox/ → /Needs_Action/ → /Plans/ → /Pending_Approval/
                                                          ↓
                                                   /Approved/ or /Rejected/
                                                          ↓
                                                         /Done/
```

**Never skip steps.** Follow the flow exactly.

---

## 5. Coordination Rules

### Task Ownership

- **Single agent per task** — no parallel processing
- Claim task by reading it first
- Update task status to prevent conflicts

### Handoff Protocol

1. **Watcher** creates task in `/Needs_Action/`
2. **Reasoning Agent** claims task → processes → creates plan
3. **Human** approves/rejects in `/Pending_Approval/`
4. **Action Agent** executes approved plan
5. All files move to `/Done/`

### Conflict Resolution

- If task already claimed, skip and process next
- If uncertain about ownership, check `/Done/` for recent completions
- Never modify a task another agent is processing

---

## 6. Plan Creation Rules

### When to Create a Plan

Create plan in `/Plans/PLAN_*.md` when:
- Task requires multiple steps
- Outcome is uncertain
- External action is needed
- Human approval is required

### Plan Format Reference

See `/.claude/skills/create-plan/SKILL.md` for plan template.

### Plan Contents

| Section | Purpose |
|---------|---------|
| **Objective** | What we're trying to accomplish |
| **Analysis** | Context about the task |
| **Steps** | Checkbox list of actions |
| **Approval Required** | Yes/No (per Company_Handbook.md) |
| **Expected Outcome** | What success looks like |

### Plan References

- Always reference the original task file
- Link to any relevant files in `/Inbox/`
- Note any dependencies on other tasks

---

## 7. Logging & Auditing

### What Must Be Logged

| Action | Log Location |
|--------|--------------|
| **Errors** | `/Logs/` with timestamp |
| **Task completion** | `/Done/` summary |
| **Watcher start/stop** | `/Logs/` |
| **Financial actions** | `/Accounting/` |

### Log Format

All logs must include:
- Timestamp (ISO-8601)
- Agent/skill name
- Action taken
- Result (success/failure)

### /Done/ Requirements

Every completed task in `/Done/` must have:
- Original task file
- Execution plan (if created)
- Completion summary (what was done, result)

---

## 8. Error Handling

### When Something Goes Wrong

1. **Log the error** in `/Logs/` with timestamp and details
2. **Pause operations** related to the error
3. **Notify human** with clear description
4. **Do NOT retry** risky actions automatically

### Error Categories

| Error Type | Action |
|------------|--------|
| **File not found** | Log and skip |
| **Permission denied** | Pause, notify human |
| **API failure** | Retry once, then notify |
| **Watcher crash** | Log, attempt restart |

### Graceful Degradation

- Continue processing other tasks if one fails
- Never stop entire system for single error
- Log everything for later review

---

## 9. Watcher Management Rules

### /start-watcher

- Launch watcher in background
- Log process ID (PID) to `/Logs/`
- Verify watcher is running before returning
- Watchers poll every 2 seconds (WSL compatibility)

### /stop-watcher

- Send graceful shutdown signal
- Verify watcher stopped before returning
- Log shutdown to `/Logs/`

### Watcher Availability

- **Passive logging:** 24/7
- **Active monitoring:** 9:00 AM - 6:00 PM (per Company_Handbook.md)
- Watchers continue even during inactive hours

### Adding New Watchers

Inherit from `BaseWatcher` in `ai_employee_scripts/watchers/base_watcher.py`:
- Implement `check_for_updates()`
- Implement `create_action_file()`
- Implement `get_item_id()`
- Use polling (not inotify) for WSL compatibility

---

## 10. Safety Constraints

### Actions NEVER Allowed

| Action | Reason |
|--------|--------|
| Payments to new recipients without approval | Financial risk |
| Sharing credentials or API keys | Security risk |
| Legal or medical advice | Liability risk |
| Emotional context messages | Appropriateness risk |

### Actions ALWAYS Require Approval

| Action | Reference |
|--------|-----------|
| Sending emails to new contacts | Company_Handbook.md |
| Payments > $50 | Company_Handbook.md |
| Social media posts | Company_Handbook.md |
| Deleting files | Company_Handbook.md |
| WhatsApp messages | Company_Handbook.md |
| Any financial transaction | Company_Handbook.md |

### Red Flags

Escalate to human immediately if:
- Unknown sender or recipient
- Suspicious request (urgent pressure, unusual formatting)
- Request for credentials or sensitive data
- Unexpected financial transaction
- Threats or aggressive language

### Safety First

When in doubt:
1. **Pause** the operation
2. **Log** the concern
3. **Ask** the human
4. **Wait** for approval

---

## Quick Reference

| Rule Category | Key Takeaway |
|---------------|--------------|
| **Autonomy** | Act autonomously for safe tasks, approve for external actions |
| **Task Processing** | /process-tasks is AUTOMATIC MODE — don't ask, just act |
| **File Operations** | Safe inside vault, require approval outside |
| **Coordination** | Single agent ownership per task |
| **Planning** | Create plans for multi-step or uncertain tasks |
| **Logging** | Log errors to /Logs/, completions to /Done/ |
| **Errors** | Log, pause, notify — don't auto-retry risky actions |
| **Watchers** | Run 24/7, use polling for WSL compatibility |
| **Safety** | When in doubt, pause and ask human |

---

*This file governs technical agent behavior. For business rules, see `Company_Handbook.md`.*
