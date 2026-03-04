# Platinum Tier - Business Requirements

**Status:** Requirements Definition
**Stakeholder:** Business Owner / Hackathon Participant
**Goal:** Define business value and success criteria for Platinum tier

---

## Executive Summary

The Platinum tier transforms the AI Employee from a **local-only tool** to a **24/7 autonomous cloud service**. This enables continuous business operations even when the user's laptop is offline.

### Business Problem Solved

| Problem | Impact | Platinum Solution |
|---------|--------|-------------------|
| Missed emails when laptop off | Delayed responses, lost opportunities | Cloud processes emails 24/7 |
| Social media requires manual triggering | Inconsistent posting, missed engagement | Automatic drafting of replies and posts |
| No business monitoring while offline | Blind spots in operations | Continuous accounting and task monitoring |
| High Claude costs for simple drafting | Unnecessary expenses | Cheaper Xiaomi model for drafting |

### Business Value

- **Faster Response Time:** Email replies drafted within 2 minutes (24/7)
- **Never Miss Opportunities:** Social mentions processed even while sleeping
- **Cost Optimization:** Use cheaper AI for drafting (~80% cost reduction)
- **Peace of Mind:** Always-on monitoring of business operations

---

## Business Requirements

### BR-1: 24/7 Availability

**Requirement:** The system must process incoming tasks 24 hours a day, 7 days a week.

**Business Rationale:**
- Business opportunities arrive at all hours
- Competitors respond around the clock
- Customers expect quick responses regardless of timezone

**Success Criteria:**
- Cloud uptime > 99%
- Tasks processed within 2 minutes of arrival
- No service gaps during local machine downtime

**Acceptance:**
```
Given: An email arrives at 3 AM local time
When: Cloud agent processes the email
Then: Draft is ready in Updates/ folder by 3:02 AM
```

---

### BR-2: Cost Efficiency

**Requirement:** Monthly operational costs must not exceed $25 USD.

**Business Rationale:**
- AI Employee should be affordable for small businesses
- ROI must be positive compared to hiring human assistant
- Predictable monthly costs

**Success Criteria:**
| Component | Budget | Actual |
|-----------|--------|--------|
| Oracle Cloud VM | $0 (Free Tier) | $0 |
| Xiaomi API | $20/month | ≤ $20 |
| Git Hosting | $0 (GitHub Free) | $0 |
| **Total** | **$20/month** | **≤ $25** |

**Acceptance:**
```
Given: One month of operation
When: Total costs are calculated
Then: Total ≤ $25 USD
```

---

### BR-3: Response Time SLA

**Requirement:** End-to-end response time must meet service level agreements.

**Business Rationale:**
- Fast responses increase conversion rates
- Customer satisfaction depends on speed
- Competitive advantage in response time

**Success Criteria:**
| Metric | Target | Stretch |
|--------|--------|---------|
| Email → Draft | < 2 minutes | < 1 minute |
| Draft → Ready for Review | < 5 minutes | < 3 minutes |
| Review → Sent | < 10 minutes | < 5 minutes |
| **Total (Email → Sent)** | **< 10 minutes** | **< 5 minutes** |

**Acceptance:**
```
Given: An email arrives
When: Human approves the draft within 5 minutes
Then: Email is sent within 10 minutes of arrival
```

---

### BR-4: Human-in-the-Loop Execution

**Requirement:** All actions that affect external systems MUST require human approval.

**Business Rationale:**
- Prevents costly mistakes
- Maintains human control over business communications
- Reduces liability from AI errors

**Success Criteria:**
- No email sent without approval
- No social post published without approval
- No payment made without approval
- 100% of sensitive actions go through Pending_Approval/

**Acceptance:**
```
Given: Cloud agent generates an email draft
When: Draft is written to Updates/
Then: Draft must be reviewed by human before sending
And: Human must explicitly approve before execution
```

---

### BR-5: Data Security & Privacy

**Requirement:** Sensitive credentials must never be stored on cloud infrastructure.

**Business Rationale:**
- Protects business from cloud provider breaches
- Keeps financial credentials under local control
- Maintains compliance with data protection regulations

**Success Criteria:**
- No banking tokens on cloud
- No payment credentials on cloud
- No WhatsApp credentials on cloud (if applicable)
- No send permissions on cloud
- Annual security audit passes

**Acceptance:**
```
Given: Cloud infrastructure is compromised
When: Attacker attempts to access business systems
Then: Attacker cannot send emails, post content, or make payments
And: Attacker only sees incoming messages (read-only)
```

---

### BR-6: Brand Voice Consistency

**Requirement:** AI-generated drafts must maintain consistent brand voice.

**Business Rationale:**
- Inconsistent communication damages brand
- Professional appearance requires consistency
- Customers should recognize communication style

**Success Criteria:**
- 90%+ of drafts match brand voice (human-rated)
- All drafts reference EmailStyle.md or equivalent
- Tone appropriate for platform (LinkedIn vs Twitter)
- No generic AI-sounding language

**Acceptance:**
```
Given: Cloud agent generates a LinkedIn post draft
When: Human reviews the draft
Then: Draft matches the voice defined in EmailStyle.md
And: Human edits required < 20% of the time
```

---

### BR-7: Business Continuity

**Requirement:** System must function during local machine downtime.

**Business Rationale:**
- Laptop can be lost, stolen, or broken
- Internet can be unavailable
- User can be on vacation or offline

**Success Criteria:**
- Cloud processes 100% of incoming tasks when local is offline
- All drafts queued for review when local returns
- No data loss during offline period
- Sync resumes automatically when local returns

**Acceptance:**
```
Given: Local machine is offline for 24 hours
When: 50 emails arrive during this period
Then: All 50 drafts are generated and queued
And: All 50 drafts are available when local returns
```

---

### BR-8: Multi-Channel Consistency

**Requirement:** System must handle multiple communication channels consistently.

**Business Rationale:**
- Business operates across multiple platforms
- Customers reach out via different channels
- Consistent experience builds trust

**Success Criteria:**
- Email handled 24/7
- LinkedIn messages handled 24/7
- Twitter mentions handled 24/7
- Facebook/Instagram handled 24/7
- All channels use same approval workflow

**Acceptance:**
```
Given: Messages arrive across multiple channels simultaneously
When: Cloud agent processes all messages
Then: All channels receive drafts within SLA
And: No channel is prioritized over others
```

---

### BR-9: Financial Oversight

**Requirement:** Accounting and financial tasks must be monitored continuously.

**Business Rationale:**
- Cash flow visibility is critical
- Unusual transactions need attention
- Financial health monitoring prevents surprises

**Success Criteria:**
- Revenue tracked 24/7
- Expenses categorized automatically
- Unusual transactions flagged for review
- Daily financial summary available

**Acceptance:**
```
Given: An invoice payment arrives
When: Cloud agent detects the transaction
Then: Transaction is categorized and flagged for review
And: Financial summary is updated
```

---

### BR-10: Return on Investment (ROI)

**Requirement:** Platinum tier must deliver positive ROI within 3 months.

**Business Rationale:**
- Investment must justify cost
- Value must exceed expenses
- Payback period must be reasonable

**Success Criteria:**
| Benefit | Monthly Value | Cost |
|---------|---------------|------|
| Time saved (drafting) | 20 hours × $50/hr = $1,000 | $20 |
| Opportunity capture | 2 deals × $500 = $1,000 | - |
| Improved response time | Customer retention = $500 | - |
| **Total Benefit** | **$2,500** | **$20** |
| **ROI** | **12,400%** | - |

**Acceptance:**
```
Given: Platinum tier operational for 3 months
When: Costs and benefits are analyzed
Then: Total benefit > 5 × total cost
```

---

## User Stories

### US-1: Overnight Email Processing

**As a** business owner
**I want** emails received overnight to be processed by morning
**So that** I can quickly review and send responses when I start my day

**Acceptance:**
- Cloud processes all emails between 10 PM - 6 AM
- All drafts ready in Updates/ by 6 AM
- I only spend 30 minutes reviewing instead of 2 hours writing

---

### US-2: Social Media Engagement

**As a** content creator
**I want** social mentions to be processed immediately
**So that** I never miss engagement opportunities

**Acceptance:**
- Twitter mentions processed within 2 minutes
- LinkedIn messages processed within 2 minutes
- Drafts maintain my brand voice
- I can approve with one click

---

### US-3: Vacation Mode

**As a** business owner going on vacation
**I want** my business to continue operating
**So that** I don't lose opportunities while away

**Acceptance:**
- Cloud processes everything while I'm away
- I can review drafts when convenient
- Critical items can be flagged for immediate attention
- Nothing falls through the cracks

---

### US-4: Cost Optimization

**As a** cost-conscious business owner
**I want** to minimize AI expenses
**So that** my margins remain healthy

**Acceptance:**
- Drafting uses cheaper model (Xiaomi)
- Execution uses Claude (only when needed)
- Monthly AI cost < $25
- No surprise charges

---

## Non-Functional Requirements

### NFR-1: Reliability

- Cloud uptime: > 99%
- Data loss: 0%
- Recovery time: < 5 minutes

### NFR-2: Performance

- Draft generation: < 30 seconds
- Git sync: < 5 minutes
- End-to-end: < 10 minutes

### NFR-3: Scalability

- Handle 100+ tasks per day
- Support multiple communication channels
- Scale to multiple users (future)

### NFR-4: Maintainability

- Code is modular and documented
- Errors are logged and recoverable
- Updates can be deployed without downtime

---

## Risk Assessment

### Risk Matrix

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Cloud VM goes down | Low | High | Auto-restart, monitoring alerts |
| Xiaomi API rate limits | Medium | Medium | Caching, queuing, fallback |
| Git sync conflicts | Low | Low | Conflict resolution, manual override |
| Guardrails fail | Low | High | Human review, monitoring |
| Cost overruns | Low | Medium | Usage monitoring, alerts |

### Business Risks

| Risk | Mitigation |
|------|------------|
| Brand damage from bad AI drafts | Human approval required for all execution |
| Data breach on cloud | No sensitive credentials on cloud |
| Vendor lock-in (Xiaomi) | Use OpenAI-compatible API, can switch |
| Complexity increases | Modular design, clear documentation |

---

## Success Metrics

### Leading Indicators (Measure During Development)

- [ ] Number of agents implemented
- [ ] Test coverage percentage
- [ ] Number of guardrails deployed
- [ ] Uptime during testing

### Lagging Indicators (Measure After Launch)

- [ ] Monthly cost vs budget
- [ ] Average response time
- [ ] Draft approval rate (% approved without edits)
- [ ] Business opportunities captured
- [ ] Time saved per week
- [ ] ROI percentage

### Dashboard Metrics

**Real-time:**
- Tasks processed today
- Drafts awaiting review
- Cloud agent status
- API usage today

**Weekly:**
- Total cost this week
- Average response time
- Approval rate
- Errors encountered

**Monthly:**
- Total cost vs budget
- ROI calculation
- Uptime percentage
- Channel breakdown

---

## Dependencies

### Technical Dependencies

| Dependency | Owner | Status |
|------------|-------|--------|
| Oracle Cloud account | Business | Required |
| Xiaomi API key | Technical | Required |
| GitHub repository | Technical | Existing |
| Local infrastructure | Technical | Existing |

### Business Dependencies

| Dependency | Owner | Status |
|------------|-------|--------|
| Brand voice documentation | Business | Required (EmailStyle.md) |
| Approval workflow definition | Business | Required |
| Cost budget approval | Business | Required |
| Security policy review | Business | Required |

---

## Constraints

### Budget Constraints

- Monthly operational cost: ≤ $25
- One-time setup cost: ≤ $100
- Development time: ≤ 6 weeks

### Time Constraints

- Must be operational before [target date]
- Cannot exceed 6 weeks development
- Must not disrupt existing Gold tier operations

### Technical Constraints

- Must use Oracle Free Tier (no paid upgrades)
- Must use Xiaomi or OpenAI-compatible API
- Must maintain existing local infrastructure
- Cannot require proprietary hardware

### Business Constraints

- Must maintain human approval for all execution
- Cannot store sensitive credentials on cloud
- Must comply with data protection regulations
- Must maintain brand voice consistency

---

## Assumptions

1. Business has existing Gmail, LinkedIn, Twitter accounts
2. Business has existing Obsidian vault structure
3. Business is willing to approve cloud-based drafting
4. Business has budget for $20-25/month operational costs
5. Business has reliable internet connection for git sync
6. Business can provide brand voice documentation
7. Oracle Cloud Free Tier remains available
8. Xiaomi API pricing remains stable

---

## Open Questions

1. **Budget Approval:** Is $25/month approved for operational costs?
2. **Timeline:** What is the target launch date?
3. **Scope:** Start with Email Agent only, or all agents together?
4. **Model:** Use Xiaomi "mimo-v2-flash" or OpenAI GPT-4o-mini?
5. **Oracle Account:** Do we have an Oracle Cloud account set up?
6. **Brand Documentation:** Is EmailStyle.md complete and up to date?

---

## Approval Criteria

Platinum tier is considered complete when:

- [ ] All 10 business requirements are met
- [ ] All user stories are implemented
- [ ] All acceptance criteria pass
- [ ] Success metrics are being tracked
- [ ] ROI is positive after 3 months
- [ ] Security audit passes
- [ ] Documentation is complete

---

*Last Updated: 2026-03-04*
*Version: 1.0*
*Status: Requirements Definition*
