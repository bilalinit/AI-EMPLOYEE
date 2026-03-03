---
name: create-plan
description: Create a structured plan for a task in the Needs_Action folder
---

# Create Plan

Create a structured execution plan for a specific task.

## Usage

```
/create-plan TASK_filename
```

Or when invoked during task processing, automatically create a plan for the current task.

## Plan Template

Create a plan file in `/Plans/` with this structure:

```markdown
---
type: plan
created: YYYY-MM-DDTHH:MM:SS
status: pending
task: TASK_filename
---

# Plan: [Brief Title]

## Objective
[What we're trying to accomplish]

## Analysis
[Context about the task]

## Steps
- [ ] Step 1
- [ ] Step 2
- [ ] Step 3

## Approval Required
[Yes/No based on Company_Handbook.md rules]

## Expected Outcome
[What success looks like]
```

## Approval Rules (from Company_Handbook.md)

**Auto-Approve:**
- Reading emails and messages
- Creating draft responses
- File organization within vault

**Requires Approval:**
- Sending emails to new contacts
- Payments > $50
- Social media posts
- Deleting files

## Notes

- Plan filename format: `PLAN_{timestamp}_{task_name}.md`
- Reference the original task file
- Include any external file paths needed
