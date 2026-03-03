---
name: complete-task
description: Mark a task as completed and move it to the Done folder
---

# Complete Task

Mark a task as completed and move all related files to the Done folder.

## Usage

```
/complete-task TASK_filename
```

## What Gets Moved

When completing a task, move these files to `/Done/`:

1. The task file from `/Needs_Action/TASK_*.md`
2. The plan file from `/Plans/PLAN_*.md`
3. Create a completion summary in `/Done/`

## Completion Summary Template

Create a summary file in `/Done/`:

```markdown
---
type: completed_task
completed: YYYY-MM-DDTHH:MM:SS
original_task: TASK_filename
plan: PLAN_filename
---

# Completed: [Task Title]

## Summary
[Brief description of what was accomplished]

## Actions Taken
- [x] Action 1
- [x] Action 2
- [x] Action 3

## Result
[Final outcome]

---
*Processed by AI Employee v0.1*
```

## Workflow Update

After completing a task:

```
Needs_Action/  → (empty or remaining tasks)
Plans/         → (plan moved to Done/)
Done/          → (task, plan, and summary added)
```

## Notes

- Always create a completion summary
- Include what was done and the result
- Keep all related files together in Done/
