---
description: Generate engaging tweets for business growth and audience engagement. Creates clean file in Content_To_Post/queued/ and review copy with Human Section in Pending_Approval/.
---

# Twitter/X Posting Skill

Generate business-focused tweets designed to generate engagement and drive traffic.

## How It Works

1. **Analyzes business context** from your vault
2. **Generates ONE tweet idea**
3. **Creates TWO files**:
   - `Content_To_Post/queued/TWITTER_POST_[timestamp].md` → Clean post content only
   - `Pending_Approval/TWITTER_POST_[timestamp].md` → Post content + Human Section for review

## Usage

```
/twitter-posting
```

## What Each File Contains

### File 1: `Content_To_Post/queued/TWITTER_POST_[timestamp].md` (Clean - No Human Section)

```markdown
---
type: twitter_post
status: queued
created: [timestamp]
post_type: engagement
topic: [generated topic]
target_audience: [who this is for]
---

[Tweet content - max 280 characters for Twitter, 10000 for Premium]

[Hashtags]
```

### File 2: `Pending_Approval/TWITTER_POST_[timestamp].md` (With Human Section for Review)

```markdown
---
type: twitter_post
status: pending_approval
created: [timestamp]
post_type: engagement
topic: [generated topic]
target_audience: [who this is for]
queued_copy: Content_To_Post/queued/TWITTER_POST_[timestamp].md
---

[Tweet content]

[Hashtags]

---

## Human Section
**Status:** [ ] Approve for posting  [ ] Request changes  [ ] Reject

**Your Instructions:**
<!-- Write your feedback, edits, or instructions here -->

**Action if Approved:** Move this file to Approved/ folder
**Action if Changes:** Edit content above, then move to Approved/
**Action if Reject:** Move to Rejected/ folder (queued copy will be removed too)
```

## Instructions to Claude

When this skill is invoked:

1. **Read Business_Goals.md** first to understand business context, services, and target audience

2. **Check Content_To_Post/posted/** folder for previous posts - avoid creating the EXACT same post/angle

3. **Generate ONE engaging tweet** focused on:
   - Business value propositions
   - Problem/solution frameworks
   - Quick tips
   - Industry insights
   - Questions to drive engagement
   - Calls-to-action

4. **Vary the content types** between calls:
   - Quick tips (thread starters)
   - Hot takes/controversial opinions
   - How-to threads
   - Behind-the-scenes insights
   - Client success stories (genericized)
   - Industry predictions
   - Common mistakes

5. **Use engaging hooks**:
   - "Stop doing X if you want Y"
   - "The #1 mistake I see..."
   - "How we helped a client achieve..."
   - "Unpopular opinion: ..."
   - "3 things I wish I knew earlier..."
   - "Here's what nobody tells you about..."

6. **Include strong call-to-action** from Business_Goals.md:
   - "Follow for more"
   - "RT if you agree"
   - "What's your take?"
   - "Comment below"
   - Link to relevant content

7. **Add 2-4 hashtags** (Twitter recommends 1-3, don't overdo it)

8. **Keep it under 280 characters** (standard Twitter limit) unless targeting Premium users

9. **Create TWO files**:
   - `Content_To_Post/queued/` → Clean post content (no Human Section)
   - `Pending_Approval/` → Post content + Human Section for your review

10. **Use filename format**: `TWITTER_POST_[topic_slug]_[timestamp].md`

11. **Inform the user** where the files were created

## File Naming Convention

```
TWITTER_POST_[topic_slug]_[YYYYMMDD_HHMMSS].md

Example: TWITTER_POST_automation_tips_20260225_143000.md
```

## Topic Ideas (Draw from these)

**Primary Source**: Read topics from `Business_Goals.md` "Topics to Post About" section

**Backup ideas** if Business_Goals.md not found:
- Automation/efficiency: Time-saving tips, tool recommendations
- Business growth: Scaling strategies, common bottlenecks
- Client results: Success stories (without specific names)
- Industry trends: What's coming, how to prepare
- Mistakes: What to avoid, lessons learned
- Behind the scenes: How you work, your process
- Quick wins: Small changes with big impact
- Tools/tech: What you use, why it matters
- AI & automation: Digital FTEs, future of work

## Hashtags to Use

Mix of:
- **Broad**: #business #entrepreneur #growth #success
- **Niche**: #automation #AI #leadgen #sales #productivity #tech
- **Engagement**: #smallbusiness #businesstips #marketing

## Length Guidelines

- **Standard Twitter**: Max 280 characters
- **Twitter Premium**: Up to 10,000 characters (but shorter is usually better)
- **Safe target**: 200-270 characters for maximum engagement

## Twitter Best Practices

- **Threads**: For longer content, create thread starters (end with "🧵")
- **Visuals**: Twitter posts with images get 150% more retweets (note: user must add image URL separately)
- **Timing**: Best times: 9-11 AM, 12-3 PM (weekdays)
- **Engagement**: Ask questions, use polls, reply to others
- **Tagging**: Tag relevant accounts (ask user first)

## Example Output Format

```
✅ Created Twitter post: "3 Automation Mistakes Costing You Sales"

Files created:
📁 Content_To_Post/queued/TWITTER_POST_automation_mistakes_20260224_143000.md
📁 Pending_Approval/TWITTER_POST_automation_mistakes_20260224_143000.md

Review in Pending_Approval/ and move to Approved/ when ready to post.

---
TWEET PREVIEW:
Stop losing leads to these 3 automation mistakes... 🛑

[rest of content]
```

## Notes

- The queued file stays in `Content_To_Post/queued/` as backup
- The approval file in `Pending_Approval/` is for YOUR review
- Use the Human Section to write your feedback or edits
- Move to `Approved/` when ready → orchestrator will post via MCP
- Move to `Rejected/` if you don't want to post this
