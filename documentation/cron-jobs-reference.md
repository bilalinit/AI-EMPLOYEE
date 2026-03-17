# Cron Jobs Reference

**Part of:** Personal AI Employee - Gold/Platinum Tier
**Last Updated:** March 2026

---

## Overview

Cron jobs automate scheduled tasks like social media content generation and weekly CEO briefings.

---

## Cron Jobs Overview

| Time | Script | Platform | Purpose |
|------|--------|----------|---------|
| **2:00 AM** | `linkedin_cron_trigger.py` | LinkedIn | Generate LinkedIn post |
| **3:00 AM** | `meta_cron_trigger.py` | Facebook/Instagram | Generate FB/IG post |
| **4:00 AM** | `twitter_cron_trigger.py` | Twitter/X | Generate tweet |
| **Sunday 5:00 AM** | `weekly_cron_trigger.py` | CEO Briefing | Weekly business report |

---

## Cron Configuration

### Setup

```bash
# Open crontab editor
crontab -e
```

### Crontab Entries

```bash
# AI Employee Cron Jobs
# Path setup (required for UV)
PATH=/home/bdev/.local/bin:/usr/bin:/bin

# LinkedIn posting (daily 2 AM)
0 2 * * * cd "/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts" && uv run python scripts/linkedin_cron_trigger.py >> ../AI_Employee_Vault/Logs/cron.log 2>&1

# Meta posting (daily 3 AM)
0 3 * * * cd "/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts" && uv run python scripts/meta_cron_trigger.py >> ../AI_Employee_Vault/Logs/meta_cron.log 2>&1

# Twitter posting (daily 4 AM)
0 4 * * * cd "/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts" && uv run python scripts/twitter_cron_trigger.py >> ../AI_Employee_Vault/Logs/twitter_cron.log 2>&1

# Weekly CEO briefing (Sunday 5 AM)
0 5 * * 0 cd "/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts" && uv run python scripts/weekly_cron_trigger.py >> ../AI_Employee_Vault/Logs/weekly_cron.log 2>&1

# Vault sync (every 5 minutes) - Platinum tier
*/5 * * * * cd "/mnt/d/coding Q4/hackathon-0/save-1" && uv run python ai_employee_scripts/vault_sync.py >> AI_Employee_Vault/Logs/vault_sync.log 2>&1
```

---

## Script Details

### LinkedIn Cron Trigger

**File:** `scripts/linkedin_cron_trigger.py`

**Purpose:** Generate LinkedIn post content daily.

**What It Does:**
1. Creates a task file in `Needs_Action/TASK_linkedin_post_{timestamp}.md`
2. Orchestrator detects and processes the task
3. Generates post content using `Business_Goals.md`
4. Creates draft in `Pending_Approval/LINKEDIN_POST_*.md`

**Workflow:**
```
Cron runs at 2:00 AM
       │
       ▼
Create TASK_linkedin_post_*.md in Needs_Action/
       │
       ▼
Orchestrator detects task
       │
       ▼
Claude processes with /process-tasks
       │
       ▼
Post draft in Pending_Approval/
       │
       ▼
Human reviews and approves
       │
       ▼
/execute-approved posts via LinkedIn MCP
```

---

### Meta Cron Trigger

**File:** `scripts/meta_cron_trigger.py`

**Purpose:** Generate Facebook/Instagram post content daily.

**What It Does:**
1. Creates task for social content generation
2. Generates platform-specific content
3. Creates draft for approval

**Output Files:**
- `Content_To_Post/queued/META_POST_*.md`
- `Pending_Approval/META_POST_*.md`

---

### Twitter Cron Trigger

**File:** `scripts/twitter_cron_trigger.py`

**Purpose:** Generate tweet content daily.

**What It Does:**
1. Creates task for tweet generation
2. Generates content under 280 characters
3. Creates draft for approval

**Output Files:**
- `Content_To_Post/queued/TWITTER_POST_*.md`
- `Pending_Approval/TWITTER_POST_*.md`

---

### Weekly Cron Trigger

**File:** `scripts/weekly_cron_trigger.py`

**Purpose:** Generate CEO briefing every Sunday.

**What It Does:**
1. Creates task for weekly audit
2. Queries Odoo for financial data
3. Analyzes email and social activity
4. Generates comprehensive report

**Output File:** `Briefings/WEEKLY_{date_range}.md`

**Report Contents:**
- Revenue and expenses
- Invoice activity
- Payment summary
- Social media stats
- Email activity
- Tasks completed
- Recommendations

---

### Vault Sync

**File:** `vault_sync.py`

**Purpose:** Sync vault between local and cloud via Git.

**Schedule:** Every 5 minutes

**Workflow:**
```
Pull latest changes
       │
       ▼
Check for local modifications
       │
       ├── No changes → Done
       │
       └── Has changes → Commit and push
```

---

## Cron Log Files

| Log File | Purpose |
|----------|---------|
| `Logs/cron.log` | LinkedIn cron output |
| `Logs/meta_cron.log` | Meta cron output |
| `Logs/twitter_cron.log` | Twitter cron output |
| `Logs/weekly_cron.log` | Weekly briefing output |
| `Logs/vault_sync.log` | Git sync activity |

---

## WSL-Specific Setup

WSL requires special handling for cron jobs:

### Install Cron

```bash
sudo apt update
sudo apt install cron
```

### Start Cron Service

```bash
# Start cron
sudo service cron start

# Check status
sudo service cron status
```

### Fix PATH Issues

```bash
# Add to crontab
PATH=/home/bdev/.local/bin:/usr/bin:/bin

# Or use full path to UV
0 2 * * * /home/bdev/.local/bin/uv run python ...
```

### Use `script` Command for TTY

Some scripts need a TTY:

```bash
0 2 * * * script -q -c "uv run python scripts/linkedin_cron_trigger.py" /dev/null >> ../AI_Employee_Vault/Logs/cron.log 2>&1
```

---

## Environment Variables in Cron

Cron jobs don't inherit shell environment. Set them explicitly:

```bash
# In crontab
ODOO_URL=http://localhost:8069
ODOO_DB=odoo
ODOO_USER=admin@example.com
ODOO_PASSWORD=your_password

0 2 * * * cd "/path/to/scripts" && uv run python scripts/linkedin_cron_trigger.py
```

Or use a wrapper script:

```bash
#!/bin/bash
# run_linkedin_cron.sh
export $(cat /path/to/ai_employee_scripts/.env | xargs)
cd /path/to/ai_employee_scripts
uv run python scripts/linkedin_cron_trigger.py
```

---

## Troubleshooting

### Cron Not Running

```bash
# Check cron service
sudo service cron status

# Check cron logs
grep CRON /var/log/syslog

# Check user's crontab
crontab -l
```

### Script Works Manually but Not in Cron

1. **PATH issue:** Use full paths
2. **Environment variables:** Set in crontab
3. **Working directory:** Use `cd` before command
4. **Permissions:** Check script is executable

### Check Cron Logs

```bash
# View cron execution logs
grep "linkedin_cron" /var/log/syslog

# View script output
cat AI_Employee_Vault/Logs/cron.log
```

### Debug Cron Job

```bash
# Run cron command manually
cd "/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts"
uv run python scripts/linkedin_cron_trigger.py

# Check for errors
echo $?  # Exit code
```

---

## Time Zones

Cron uses the system's local time zone.

```bash
# Check time zone
timedatectl

# Set time zone
sudo timedatectl set-timezone America/New_York
```

**Important:** Schedule cron jobs considering your time zone.

---

## Cron Schedule Reference

| Expression | Meaning |
|------------|---------|
| `0 2 * * *` | Every day at 2:00 AM |
| `0 3 * * *` | Every day at 3:00 AM |
| `0 4 * * *` | Every day at 4:00 AM |
| `0 5 * * 0` | Every Sunday at 5:00 AM |
| `*/5 * * * *` | Every 5 minutes |
| `0 */2 * * *` | Every 2 hours |
| `0 9 * * 1-5` | Weekdays at 9:00 AM |

---

**Related Documentation:**
- [Getting Started Guide](getting-started.md)
- [Agent Skills Reference](agent-skills-reference.md)
- [Cloud Deployment Guide](cloud-deployment.md)