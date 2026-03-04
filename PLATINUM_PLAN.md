# Platinum Tier Implementation Plan
# Cloud AI Employee with OpenAI Agents SDK

**Status:** Planning Phase
**Target:** 24/7 autonomous operation with cloud-local split architecture
**Technology:** OpenAI Agents SDK + Xiaomi mimo-v2-flash model

---

## Executive Summary

Add a cloud-based AI agent to complement the existing local Claude Code system. The cloud agent handles drafting and reasoning 24/7, while the local system handles execution with human approval.

### Why This Architecture?

- **Cloud (24/7):** Processes incoming emails, messages, social mentions even when laptop is off
- **Local (Secure):** Keeps sensitive credentials (banking, send permissions) safe on your machine
- **Split Cost:** Uses cheaper Xiaomi model for drafting, Claude for execution only
- **Better Than DigitalFTE:** Multi-agent handoffs, guardrails, structured outputs

---

## Architecture Overview

```
CLOUD VM (Oracle Free Tier)                    LOCAL MACHINE (Your Laptop)
├──────────────────────────────┐              ├──────────────────────────────┐
│ Cloud Orchestrator          │              │ Local Orchestrator          │
│ (monitors Needs_Action/)    │ Git Sync     │ (existing - keep as is)     │
│         ↓                   │◄────────►    │         ↓                   │
│ Triage Agent                │              │ Reads Updates/              │
│ (routes to specialists)     │              │         ↓                   │
│     ↓  ↓  ↓                 │              │ Moves to Pending_Approval/  │
│ ┌───┴┐ ┴──┴─┐               │              │         ↓                   │
│ │Email│Social│Finance│      │              │ Human reviews in Obsidian   │
│ └─┬──┴──────┴──────┘        │              │         ↓                   │
│    ↓                        │              │ Moves to Approved/          │
│ Structured Outputs          │              │         ↓                   │
│ (Pydantic models)           │              │ Calls MCP servers           │
│    ↓                        │              │         ↓                   │
│ Guardrail Check            │              │ Executes (send/post/pay)    │
│    ↓                        │              │         ↓                   │
│ Write to: Updates/          │              │ Moves to Done/              │
│    ↓                        │              │         ↓                   │
│ Git push                    │              │ Git push                    │
└──────────────────────────────┘              └──────────────────────────────┘
```

---

## Phase 1: Project Structure

### New Directory Layout

```
ai-employee/
├── ai_employee_scripts/
│   ├── cloud/                          # NEW - Cloud agent code
│   │   ├── __init__.py
│   │   ├── cloud_orchestrator.py       # Main cloud controller
│   │   ├── config/                     # Cloud configuration
│   │   │   ├── __init__.py
│   │   │   └── settings.py            # Cloud-specific settings
│   │   ├── agents/                     # Agent definitions
│   │   │   ├── __init__.py
│   │   │   ├── base_agent.py          # Base agent class
│   │   │   ├── triage_agent.py        # Routes tasks to specialists
│   │   │   ├── email_agent.py         # Email drafting specialist
│   │   │   ├── social_agent.py        # Social media specialist
│   │   │   ├── finance_agent.py       # Finance/accounting specialist
│   │   │   └── models.py              # Pydantic models for structured outputs
│   │   ├── tools/                      # Function tools for agents
│   │   │   ├── __init__.py
│   │   │   ├── file_tools.py          # Write to vault folders
│   │   │   ├── git_tools.py           # Git operations
│   │   │   └── vault_tools.py         # Read from vault
│   │   ├── guardrails/                 # Safety checks
│   │   │   ├── __init__.py
│   │   │   ├── input_guardrails.py    # Validate incoming requests
│   │   │   └── output_guardrails.py   # Validate agent outputs
│   │   └── utils/                      # Helper functions
│   │       ├── __init__.py
│   │       ├── logger.py              # Cloud logging
│   │       └── error_handler.py       # Cloud error handling
│   ├── deployment/                     # NEW - Deployment scripts
│   │   ├── deploy_cloud.sh            # Deploy to Oracle VM
│   │   ├── start_cloud.sh             # Start cloud services
│   │   ├── stop_cloud.sh              # Stop cloud services
│   │   └── setup_oracle_vm.sh         # Initial Oracle VM setup
│   ├── watchers/                       # Existing - keep as is
│   ├── mcp_servers/                    # Existing - keep as is
│   ├── orchestrator.py                 # Existing - local orchestrator
│   └── pyproject.toml                  # UPDATE: Add openai-agents
│
├── AI_Employee_Vault/                  # Existing vault - UPDATE structure
│   ├── Updates/                       # NEW - Cloud writes drafts here
│   ├── In_Progress/                   # NEW - Locking mechanism
│   │   ├── cloud/                     # Cloud working on these
│   │   └── local/                     # Local working on these
│   ├── Needs_Action/                  # Existing
│   ├── Pending_Approval/              # Existing
│   ├── Approved/                      # Existing
│   ├── Done/                          # Existing
│   └── ...
│
├── .claude/
│   └── skills/
│       └── openai-agents-sdk/         # Existing - you already added
│
├── PLATINUM_PLAN.md                   # This file
└── README.md                          # UPDATE: Add Platinum tier info
```

---

## Phase 2: Dependencies & Configuration

### 2.1 Update Python Dependencies

Add to `pyproject.toml`:
- `openai-agents>=0.1.0` - OpenAI Agents SDK
- `pydantic>=2.0` - For structured outputs
- `python-dotenv>=1.0.0` - Environment variables

### 2.2 Environment Variables

Create `.env.cloud` template for cloud VM:

**Safe for cloud** (no sensitive secrets):
- `XIAOMI_API_KEY` - Xiaomi model API key
- `AGENT_TYPE=cloud` - Identify as cloud agent
- `VAULT_PATH=./vault` - Vault path
- `GIT_REMOTE=origin` - Git remote

**NEVER sync to cloud** (local only):
- Banking/payment credentials
- Send email permissions
- Social media posting tokens

### 2.3 Model Configuration

Configure Xiaomi "mimo-v2-flash" model:
- Set up AsyncOpenAI client with Xiaomi endpoint
- Configure RunConfig with custom model
- Set up model provider for agent execution

---

## Phase 3: Core Components

### 3.1 Cloud Orchestrator (`cloud/cloud_orchestrator.py`)

**Purpose:** Main controller that runs on cloud VM

**Responsibilities:**
- Monitor `Needs_Action/` folder for new tasks
- Route tasks to Triage Agent
- Handle agent responses
- Write results to `Updates/` folder
- Git push changes
- Health monitoring and logging

**Key Features:**
- Polling loop (every 30 seconds)
- Claim-by-move locking (move to `In_Progress/cloud/`)
- Error recovery and retry logic
- State persistence

### 3.2 Triage Agent (`cloud/agents/triage_agent.py`)

**Purpose:** Route incoming tasks to specialized agents

**Handoff Destinations:**
- Email Agent → for emails, replies
- Social Agent → for social mentions, posts
- Finance Agent → for invoices, payments, accounting

**Instructions:**
- Analyze task type and content
- Route to appropriate specialist
- Handle ambiguous requests (ask for clarification)

### 3.3 Specialized Agents

#### Email Agent (`cloud/agents/email_agent.py`)

**Purpose:** Draft email replies

**Capabilities:**
- Read email context and thread history
- Generate contextual replies
- Match writing style from `EmailStyle.md`
- Identify questions requiring human input
- Suggest appropriate responses

**Output:** Structured EmailDraft model

#### Social Agent (`cloud/agents/social_agent.py`)

**Purpose:** Draft social media content and replies

**Capabilities:**
- Generate LinkedIn posts
- Draft Twitter/X replies
- Create Facebook/Instagram captions
- Match platform-specific style

**Output:** Structured SocialPost model

#### Finance Agent (`cloud/agents/finance_agent.py`)

**Purpose:** Handle financial tasks

**Capabilities:**
- Analyze invoice requests
- Draft payment summaries
- Generate P&L insights
- Identify unusual transactions

**Output:** Structured FinanceAction model

### 3.4 Structured Outputs (`cloud/agents/models.py`)

Define Pydantic models for:
- `EmailDraft` - to, subject, body, confidence, needs_approval
- `SocialPost` - platform, content, hashtags, scheduled_time
- `FinanceAction` - action_type, amount, description, risk_level
- `AgentResponse` - generic response wrapper

### 3.5 Guardrails (`cloud/guardrails/`)

#### Input Guardrails

**Purpose:** Validate incoming requests before agent processing

**Checks:**
- Block malicious/prompt injection attempts
- Rate limiting per sender
- Detect spam or abuse
- Validate task format

#### Output Guardrails

**Purpose:** Validate agent outputs before writing to vault

**Checks:**
- Ensure output is appropriate
- Verify structured output format
- Check for policy violations
- Validate confidence levels

### 3.6 Tools (`cloud/tools/`)

#### File Tools (`file_tools.py`)

- `write_draft()` - Write draft to Updates/
- `move_to_progress()` - Move to In_Progress/ for locking
- `read_task()` - Read task from Needs_Action/

#### Git Tools (`git_tools.py`)

- `git_commit_push()` - Commit and push changes
- `git_pull()` - Pull latest changes
- `git_status()` - Check git status

#### Vault Tools (`vault_tools.py`)

- `read_email_style()` - Read writing style guide
- `read_handbook()` - Read Company Handbook rules
- `read_context()` - Read previous context

---

## Phase 4: Cloud Deployment

### 4.1 Oracle Cloud Free Tier Setup

**VM Configuration:**
- Shape: VM.Standard.A1.Flex
- OCPUs: 2 (of 4 available)
- Memory: 6 GB (of 12 GB available)
- Storage: 50 GB (of 200 GB available)
- OS: Ubuntu 22.04

**Network Setup:**
- Assign static public IP
- Configure security list (SSH port 22, optional HTTPS port 443)
- Set up reserved IP

### 4.2 Initial VM Setup

**Steps:**
1. SSH into VM
2. Install Python 3.13+
3. Install UV package manager
4. Clone repository
5. Configure `.env.cloud`
6. Install dependencies with UV
7. Set up git authentication (SSH keys)
8. Test git push/pull

### 4.3 Service Configuration

**PM2 Process Management:**
- Create PM2 ecosystem file
- Configure auto-restart
- Set up log files
- Configure startup script

**Systemd Services (alternative to PM2):**
- Create service files for cloud orchestrator
- Enable auto-start on boot
- Configure log rotation

### 4.4 Cron Jobs

**Git Sync (every 5 minutes):**
- Pull updates from GitHub
- Push local commits

**Health Check (every hour):**
- Verify orchestrator is running
- Check disk space
- Check memory usage
- Alert on errors

---

## Phase 5: Git Sync Architecture

### 5.1 Sync Strategy

**Cloud → Local (Drafts):**
- Cloud writes to `Updates/`
- Cloud commits and pushes
- Local pulls every 5 minutes

**Local → Cloud (Execution Results):**
- Local writes to `Done/`
- Local commits and pushes
- Cloud pulls for record-keeping

### 5.2 Locking Mechanism

**Claim-by-Move Rule:**
1. Cloud creates: `Needs_Action/TASK_123.md`
2. Cloud moves to: `In_Progress/cloud/TASK_123.md` (LOCKED)
3. Cloud processes and writes to: `Updates/DRAFT_123.md`
4. Local ignores files in `In_Progress/cloud/`
5. Only when draft is in `Updates/` does local process it

### 5.3 Conflict Prevention

**Folder Ownership:**
- `In_Progress/cloud/` - Only cloud agent writes here
- `In_Progress/local/` - Only local agent writes here
- `Updates/` - Cloud writes, local reads
- `Approved/` - Only local writes
- `Done/` - Only local writes

---

## Phase 6: Local Updates

### 6.1 Update Local Orchestrator

**Add new monitoring:**
- Monitor `Updates/` folder for cloud drafts
- Move drafts to `Pending_Approval/` for review
- Keep existing Approved/Done monitoring

**No breaking changes** - existing functionality preserved

### 6.2 Update Vault Structure

**Add new folders:**
- `Updates/` - Cloud drafts (local reads only)
- `In_Progress/cloud/` - Cloud working files
- `In_Progress/local/` - Local working files

### 6.3 Update Git Pull

**Add scheduled git pull:**
- Every 5 minutes, pull from GitHub
- Check for new files in `Updates/`
- Move to `Pending_Approval/` for review

---

## Phase 7: Security & Safety

### 7.1 Credential Separation

**Cloud CAN access:**
- Xiaomi API key (for drafting)
- Gmail read-only API
- Twitter/LinkedIn read-only APIs
- Public vault files

**Cloud CANNOT access:**
- Banking/payment credentials
- Gmail send permissions
- Social media posting permissions
- Any `.env` files with secrets

### 7.2 Data Security

**Git Ignore:**
- `.env` files (never commit)
- `*.token.json` files
- Session data
- Temporary files

**Vault Sync:**
- Only sync `.md` files
- Never sync credentials
- Never sync in-progress local work

### 7.3 Guardrails

**Input Guardrails:**
- Block malicious prompts
- Rate limit per sender
- Detect spam patterns

**Output Guardrails:**
- Validate appropriate content
- Check for policy violations
- Verify structured output format

---

## Phase 8: Testing Strategy

### 8.1 Unit Testing

**Test Components:**
- Agent creation and configuration
- Tool functions (read/write files)
- Guardrail logic
- Structured output validation

### 8.2 Integration Testing

**Test Workflows:**
- Cloud: Email → Draft → Updates/
- Cloud: Social mention → Draft → Updates/
- Local: Updates/ → Pending_Approval/ → Approved/ → Done/
- Git sync between cloud and local

### 8.3 End-to-End Testing

**Test Scenario:**
1. Manually create test email in cloud Needs_Action/
2. Verify cloud processes and creates draft in Updates/
3. Verify git push works
4. On local: git pull receives draft
5. Verify local moves to Pending_Approval/
6. Human approves, moves to Approved/
7. Verify local executes via MCP
8. Verify result in Done/

### 8.4 Performance Testing

**Metrics:**
- Draft generation time (target: < 30 seconds)
- Git sync latency (target: < 5 minutes)
- End-to-end time (email to send: < 10 minutes)

### 8.5 Failure Testing

**Test Scenarios:**
- Cloud VM restart
- Network timeout
- Git conflict
- Agent error
- Guardrail triggered

---

## Phase 9: Rollout Plan

### 9.1 Development (Week 1-2)

- Set up cloud folder structure
- Implement base agent and triage agent
- Create tool functions
- Set up guardrails
- Write unit tests

### 9.2 Cloud Deployment (Week 3)

- Set up Oracle Cloud VM
- Install dependencies
- Configure git
- Deploy cloud orchestrator
- Test basic functionality

### 9.3 Integration (Week 4)

- Update local orchestrator
- Implement git sync
- Update vault structure
- Test cloud-local communication

### 9.4 Testing & Refinement (Week 5)

- End-to-end testing
- Performance optimization
- Error handling
- Documentation

### 9.5 Production Launch (Week 6)

- Final testing
- Monitor for 24 hours
- Fix any issues
- Complete documentation

---

## Phase 10: Monitoring & Maintenance

### 10.1 Cloud Monitoring

**Metrics to Track:**
- Uptime and availability
- Draft generation success rate
- API call costs
- Error rates by type
- Git sync status

**Alerting:**
- Cloud orchestrator down
- High error rate
- Disk space > 80%
- Memory > 80%

### 10.2 Cost Monitoring

**Track:**
- Xiaomi API usage and costs
- Oracle Cloud free tier usage
- GitHub storage/bandwidth

**Budget Targets:**
- Xiaomi API: <$20/month
- Oracle: Free tier only
- Total: <$25/month

### 10.3 Maintenance Tasks

**Weekly:**
- Review logs
- Check error rates
- Update guardrails if needed

**Monthly:**
- Review and rotate API keys
- Update dependencies
- Review costs

---

## Success Criteria

### Functional Requirements

- [x] Cloud agent runs 24/7 on Oracle VM
- [x] Processes emails, social mentions automatically
- [x] Generates drafts in appropriate style
- [x] Writes to Updates/ folder
- [x] Git sync works bidirectionally
- [x] Local agent processes cloud drafts
- [x] Human can review and approve
- [x] Execution via MCP servers works

### Non-Functional Requirements

- [x] Draft generation < 30 seconds
- [x] End-to-end time < 10 minutes
- [x] Cloud uptime > 99%
- [x] Cost < $25/month
- [x] No sensitive credentials on cloud
- [x] Guardrails block malicious inputs
- [x] Locking prevents double-processing

---

## Comparison: Before vs After Platinum

| Aspect | Gold Tier (Current) | Platinum Tier (After) |
|--------|---------------------|----------------------|
| **Availability** | When laptop is on | 24/7 (cloud always on) |
| **Email processing** | Manual trigger | Automatic (2 min latency) |
| **Social monitoring** | Manual trigger | Automatic |
| **Drafting AI** | Claude Code (expensive) | Xiaomi (cheaper) |
| **Execution AI** | Claude Code | Claude Code (unchanged) |
| **Monthly cost** | Claude subscription | +~$20 (Xiaomi API) |
| **Security** | All local | Split (cloud drafting, local execution) |

---

## Next Steps

1. **Review this plan** - Confirm architecture and approach
2. **Create cloud folder structure** - Set up directories
3. **Implement base agent** - Start with simple agent
4. **Set up Oracle VM** - Get cloud infrastructure ready
5. **Deploy and test** - Iterative development

---

**Questions to Resolve:**

1. Do you want to use Xiaomi "mimo-v2-flash" or stick with OpenAI models?
2. What's your budget for monthly API costs?
3. Do you have an Oracle Cloud account already?
4. Should we implement all agents at once, or start with email agent only?

---

*Last Updated: 2026-03-04*
*Version: 1.0 - Planning Phase*
