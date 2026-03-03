---
name: process-tasks
description: Process task files from the Needs_Action folder
---

# Process tasks

Process task files from the `AI_Employee_Vault/Needs_Action/` folder. This skill reads the file content, determines what action is needed, and either executes it or creates a plan for human review.

---

## PRIORITY 1: Invoice Request Detection (DO THIS FIRST!)

**Before ANY other processing**, check if the task is requesting an invoice to be created.

### Invoice Keywords to Look For:
- "send me an invoice", "can you invoice me", "need an invoice"
- "how do i pay", "payment request", "bill me", "invoice for"
- "create invoice", "generate invoice", "new invoice"
- "can you send invoice", "please invoice", "i need an invoice"

### How to Check:
1. Read the original file from `Inbox/` (use `inbox_ref` from task frontmatter)
2. Search the content for invoice keywords above
3. Check context: Is someone asking for billing/payment?

### If Invoice Request Detected:

**STOP! Do NOT continue with any other /process-tasks steps.**

**Your instructions:**

1. Extract available information from the message:
   - **Customer name**: From sender name or email
   - **Amount**: If mentioned ("$500", "5 hours", "3d animation", etc.)
   - **Description**: Service context from the message
   - **Sender email**: For customer lookup

2. **Delegate to /create-invoice skill** by reading and following:
   ```
   Read: .claude/skills/create-invoice/SKILL.md
   ```

3. Follow ALL steps in /create-invoice skill:
   - Read business context (Rates.md, business_goals.md)
   - Create draft invoice via Odoo MCP: `mcp__odoo__create_draft_invoice`
   - Create approval file in `Pending_Approval/INVOICE_{customer}_{date}.md`
   - Update Dashboard with invoice created

4. After /create-invoice completes:
   - Move the task file from `Needs_Action/` to `Done/`
   - Create completion summary with invoice details
   - Use the completed task template (see below)

5. **YOU ARE DONE - Skip all remaining /process-tasks steps**

### Example Invoice Detection:

```
Email: "Can you send me an invoice for the 5 hours of 3D animation work?"

Detection:
- Keywords: "send me an invoice" (MATCH)
- Context: Customer requesting billing
- Extracted: Customer=[sender], Amount=5 hours, Description=3D animation

Action:
- STOP /process-tasks
- Read /create-invoice skill
- Create draft invoice for 5 hours × $150 = $750
- Create approval file in Pending_Approval/
- Move task to Done/
```

### If NOT an Invoice Request:

Continue with normal /process-tasks processing below...

---

## What This Does

1. Lists available files in the Needs_Action folder
2. Reads the specified file content
3. Analyzes the content to determine appropriate action
4. Either executes simple actions or creates a plan for complex ones
5. Processes all files if requested without specifying a filename
6. Moves completed files to Done/ folder

**Note:** To send email replies, use the `gmail` MCP server.

## Usage

```
/process-tasks <filename> or /process-tasks
```

### Example

```
/process-tasks invoice.pdf
/process-tasks meeting_notes.txt
/process-tasks process all files
```

## Supported Actions

| File Type | Possible Actions |
|------------|-----------------|
| Images | Extract text, generate description, create summary |
| PDFs | Extract text, log invoices, create metadata |
| Text files | Parse content, extract tasks, summarize |
| Documents | Read content, determine next steps |

---

## Task Complexity Detection

**FIRST:** Decide if the task is SIMPLE or COMPLEX:

### SIMPLE (direct execution → Done/)
- Single action, no coordination needed
- Informational processing only (extract, summarize, log)
- No external system changes
- Examples: Extract text from PDF, summarize a document, log metadata

### COMPLEX (needs workflow → Plans/ → ...)
- Multiple steps required
- External API actions beyond simple reads
- Dependencies or timing constraints
- Affects other systems/people
- Examples: Send email, post to social media, coordinate multi-step process

---

## Workflow For Complex Tasks

For complex tasks, follow this flow:

1. **Needs_Action/** → Task detected by watcher
2. **Plans/** → Create Plan.md with step-by-step checklist
3. **Pending_Approval/** → Create approval request for sensitive actions (financial, new contacts, posting)
4. **Done/** → Complete task or log summary (do NOT wait - summarize and move on)

---

## Email Handling

When processing a file with `type: email` in frontmatter:

1. **Read full content** from the `Inbox/` reference (inbox_ref field)

2. **Check for GREETING first** (MUST reply - never skip):
   - Greeting keywords: "hi", "hello", "hey", "thanks", "thank you", "appreciate", "happy"
   - Short emails (< 100 words) with only greeting/small talk/thanks
   - **If greeting**:
     - Draft a warm, friendly reply (match the tone)
     - **USE gmail MCP to SEND the reply** (critical step - do not skip!)
     - Move original task to `Done/` with completed template
   - **NOTE:** Even if from yourself (test email) or same person - STILL REPLY! No exceptions.

3. **If NOT a greeting**, think through importance based on:
   - Sender (known vs unknown contact)
   - Subject keywords (urgent, deadline, invoice, payment)
   - Content type (informational vs actionable)
   - Priority level from watcher (high/medium/low)

4. **If NOT important**:
   - Draft a professional, brief reply
   - Use `gmail` MCP to send the reply
   - Move original task to `Done/`

5. **If important**:
   - Summarize the email and key points
   - Log the analysis to `Logs/` folder with timestamp
   - Move the task from `Needs_Action/` to `Pending_Approval/`
   - Add two sections at the end of the task file:
     - `## Claude Reasoning` - Explain WHY you decided human approval is needed
     - `## Human` - Empty section for human to write instructions if desired
   - DO NOT auto-reply - human will handle

---

## Completed Task Template

When moving a task to `Done/`, wrap the original content with this format:

```markdown
---
type: completed_task
completed: YYYY-MM-DDTHH:MM:SS
completed_by: ai
original_task: TASK_filename
plan: PLAN_filename (if applicable)
time_taken: X minutes (optional)
tags: [category, action-type]
---

# Completed: [Task Title]

[Original task content here]

## Summary
[Brief description of what was accomplished]

## Actions Taken
- [x] Action 1
- [x] Action 2
- [x] Action 3

## Result
[Final outcome]

## Next Steps (if any)
- [ ] Follow-up item 1
- [ ] Follow-up item 2

## Related Files
- Link to plan, invoices, or other references

---
*Processed by AI Employee v0.1 on YYYY-MM-DD HH:MM*
```

**Example for auto-replied email:**
```markdown
---
type: completed_task
completed: 2026-02-16T14:30:00
completed_by: ai
original_task: EMAIL_newsletter_20260216_143000.md
time_taken: 2 minutes
tags: [email, auto-reply, low-priority]
---

# Completed: Auto-reply to newsletter

[Original email task content...]

## Summary
Automatically replied to low-priority newsletter email.

## Actions Taken
- [x] Read full email from Inbox/
- [x] Determined not important (known sender, informational)
- [x] Drafted brief "thank you" reply
- [x] Sent reply via gmail MCP

## Result
Email replied successfully. Original task closed.

---
*Processed by AI Employee v0.1 on 2026-02-16 14:30*
```

## Safety Rules

### File Operations
- **Moving files between vault folders** = normal workflow, no approval needed
- **Deleting files for moving purposes** (e.g., Needs_Action to Done) = no approval needed
- **Permanently deleting files** (removing data entirely) = NEVER
- **Deleting files outside vault** = NEVER

### Task-Specific Rules
- Financial documents → Create approval request in Pending_Approval/
- Unknown file types → Ask human what to do

### Email-Specific Rules
- **Never auto-reply to:** new/unknown contacts, urgent/deadline matters, financial inquiries
- **Keywords requiring approval:** urgent, deadline, payment, invoice, asap
- **Important emails:** Summarize and log for human - DO NOT wait for approval
- **Always use:** gmail MCP for sending (not direct SMTP)
- **Reference:** `AI_Employee_Vault/Company_Handbook.md` for full communication guidelines

---

## LinkedIn Message Handling

When processing a file with `type: linkedin_message` or `LINKEDIN_MESSAGE_*` in frontmatter:

1. **Read full message** from the `Inbox/` reference (inbox_ref field)

2. **Analyze the message type:**

   **SIMPLE GREETING** (auto-reply):
   - Keywords: "hi", "hello", "hey", "thanks", "thank you", "appreciate", "great", "congrats"
   - Short messages (< 50 words) with only greeting/small talk
   - **If greeting**:
     - Draft a warm, friendly reply (match the tone - professional but approachable)
     - Use `linkedin-mcp__reply_message` to SEND the reply
     - Move original task to `Done/` with completed template

   **CONNECTION REQUEST** (auto-reply):
   - Keywords: "connect", "connection", "let's connect", "would love to connect"
   - Standard LinkedIn connection notes
   - **If connection request**:
     - Draft a professional, welcoming response
     - Use `linkedin-mcp__reply_message` to SEND the reply
     - Move original task to `Done/` with completed template

   **BUSINESS INQUIRY** (needs human review):
   - Keywords: "services", "pricing", "hire", "project", "work together", "proposal"
   - Questions about rates, availability, or specific services
   - **If business inquiry**:
     - Summarize the message and key points
     - Log the analysis to `Logs/` folder with timestamp
     - Move the task from `Needs_Action/` to `Pending_Approval/`
     - Add two sections at the end:
       - `## Claude Reasoning` - Explain WHY this needs human review (business opportunity)
       - `## Human` - Empty section for human to write instructions
     - DO NOT auto-reply - human will handle

   **COMPLEX/IMPORTANT** (needs human review):
   - Job offers, partnerships, media requests
   - Legal questions, NDAs, contracts
   - Urgent or high-stakes conversations
   - **If complex**:
     - Summarize the message
     - Move to `Pending_Approval/`
     - Add `## Claude Reasoning` and `## Human` sections
     - DO NOT auto-reply

3. **LinkedIn MCP Usage:**

   To send a reply, use:
   ```
   mcp__linkedin-mcp__reply_message
   Parameters:
     - conversation_url: [full LinkedIn conversation URL from inbox_ref]
     - message: [your drafted reply as plain text]
     - wait_before_send: 2 (default, 2 second delay)
   ```

4. **Conversation URL Format:**
   - Found in the `inbox_ref` field of the task
   - Example: `https://www.linkedin.com/messaging/thread/ABC123/`
   - OR sender name if URL not available (tool will search)

5. **Reply Tone Guidelines:**
   - **Greeting:** Warm, brief, "Thanks for connecting!" style
   - **Connection:** Professional, welcoming, open-ended question
   - **Keep it brief:** LinkedIn messages work best under 100 words
   - **Include CTA:** "Let me know if there's anything I can help with"

### LinkedIn-Specific Rules
- **Never auto-reply to:** obvious sales spam, suspicious links, account warnings
- **Always draft replies first** - review before sending via MCP
- **Business inquiries = human review** - these are potential clients
- **Use conversation_url from inbox_ref** - do not guess URLs
- **Reference:** `AI_Employee_Vault/Company_Handbook.md` for full communication guidelines

---

## Terminal Output Format

**IMPORTANT:** After completing any task, display a readable summary in the terminal WITHOUT markdown formatting.

The summary should be plain text, easy to read in a terminal:

```
==================================================
TASK COMPLETED
==================================================

Task: [Task name]
Status: [Completed / Moved to Pending_Approval / etc.]
Time Taken: [X minutes]

Summary:
[Brief description of what was done]

Actions Taken:
- Action 1
- Action 2
- Action 3

Result:
[Final outcome]

==================================================
```

**Rules:**
- NO markdown symbols (no **, ##, -, etc. in the terminal output)
- Use plain text formatting
- Keep it concise and readable
- Only show this AFTER the task is complete

---

## MCP Tools Available

- **mcp__odoo__create_draft_invoice** - Create draft invoice (via /create-invoice)
- **mcp__ai-gmail__send_email** - Send emails
- **mcp__linkedin-api__post_to_linkedin** - Post to LinkedIn
- **mcp__linkedin-mcp__reply_message** - Reply to LinkedIn messages
- **mcp__linkedin-mcp__get_messages** - Get LinkedIn messages
- **mcp__linkedin-mcp__verify_connection** - Verify LinkedIn connection

---

## Notes

- **Invoice detection is always first** - check before any other processing
- **Skills can delegate to other skills** - this is intentional design
- **Use human judgment** - if context suggests invoice request even without exact keywords, delegate to /create-invoice
- **Log everything** - all actions should be traceable in Done/ and Dashboard.md
- **For email replies, always use gmail MCP** - do not skip sending
- **LinkedIn invoice requests** should also be detected and routed to /create-invoice
