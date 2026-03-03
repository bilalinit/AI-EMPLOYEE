---
description: Generate a lead-generating LinkedIn post idea. Creates clean file in Content_To_Post/queued/ and review copy with Human Section in Pending_Approval/.
---

# LinkedIn Posting Skill

Generate business-focused LinkedIn content ideas designed to generate leads and sales.

## How It Works

1. **Analyzes business context** from your vault
2. **Generates ONE lead-generating post idea**
3. **Creates TWO files**:
   - `Content_To_Post/queued/LINKEDIN_POST_[timestamp].md` → Clean post content only
   - `Pending_Approval/LINKEDIN_POST_[timestamp].md` → Post content + Human Section for review

## Usage

```
/linkedin-posting
```

## What Each File Contains

### File 1: `Content_To_Post/queued/LINKEDIN_POST_[timestamp].md` (Clean - No Human Section)

```markdown
---
type: linkedin_post
status: queued
created: [timestamp]
post_type: lead_generation
topic: [generated topic]
target_audience: [who this is for]
---

# [Hook Headline]

[Post content - 2-3 paragraphs with value]

## Key Takeaways
- [Point 1]
- [Point 2]
- [Point 3]

[Hashtags]
```

### File 2: `Pending_Approval/LINKEDIN_POST_[timestamp].md` (With Human Section for Review)

```markdown
---
type: linkedin_post
status: pending_approval
created: [timestamp]
post_type: lead_generation
topic: [generated topic]
target_audience: [who this is for]
queued_copy: Content_To_Post/queued/LINKEDIN_POST_[timestamp].md
---

# [Hook Headline]

[Post content - 2-3 paragraphs with value]

## Key Takeaways
- [Point 1]
- [Point 2]
- [Point 3]

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

1. **Read Business_Goals.md** first to understand business context

2. **Check Content_To_Post/posted/* folder for previous posts** - avoid creating the EXACT same post/angle (you CAN post about the same topics with different perspectives)

3. **Generate ONE lead-generating post idea** focused on:
   - Business value propositions
   - Problem/solution frameworks
   - Social proof or case studies
   - Industry insights
   - Tips that demonstrate expertise

4. **Vary the content types** between calls:
   - How-to guides
   - Listicles (3-5 tips)
   - Behind-the-scenes insights
   - Client success stories (genericized)
   - Industry predictions
   - Common mistakes to avoid

5. **Use engaging hooks**:
   - "Stop doing X if you want Y"
   - "The #1 mistake I see..."
   - "How we helped a client achieve..."
   - "Unpopular opinion: ..."
   - "3 things I wish I knew earlier..."

6. **Include strong call-to-action**: Read preferred CTA from Business_Goals.md (default to comments):
   - "DM me 'LEAD' for..."
   - "Comment below if..."
   - "Link in bio for..."
   - "What's your experience? Share below..."

7. **Add 3-5 relevant hashtags** for business/lead generation

8. **Create TWO files**:
   - `Content_To_Post/queued/` → Clean post content (no Human Section)
   - `Pending_Approval/` → Post content + Human Section for your review

9. **Use filename format**: `LINKEDIN_POST_[topic_slug]_[timestamp].md`

10. **Inform the user** where the files were created

## File Naming Convention

```
LINKEDIN_POST_[topic_slug]_[YYYYMMDD_HHMMSS].md

Example: LINKEDIN_POST_automation_tips_20260218_143000.md
```

## Topic Ideas

**Primary Source**: Read topics from Business_Goals.md "Topics to Post About" section

**Backup ideas** if Business_Goals.md not found:
- **Automation/efficiency**: Time-saving tips, tool recommendations
- **Business growth**: Scaling strategies, common bottlenecks
- **Client results**: Success stories (without specific names)
- **Industry trends**: What's coming, how to prepare
- **Mistakes**: What to avoid, lessons learned
- **Behind the scenes**: How you work, your process
- **Quick wins**: Small changes with big impact
- **Tools/tech**: What you use, why it matters

## Hashtags to Use

Mix of:
- **Broad**: #business #entrepreneur #growth
- **Niche**: #automation #AI #leadgen #sales
- **Engagement**: #smallbusiness #businesstips

## Length Guidelines

- **Ideal**: 700-1200 characters
- **Minimum**: 300 characters
- **Maximum**: 1300 characters (LinkedIn limit)

## Example Output Format

```
✅ Created LinkedIn post: "3 Automation Mistakes Costing You Sales"

Files created:
📁 Content_To_Post/queued/LINKEDIN_POST_automation_mistakes_20260218_143000.md
📁 Pending_Approval/LINKEDIN_POST_automation_mistakes_20260218_143000.md

Review in Pending_Approval/ and move to Approved/ when ready to post.

---
POST PREVIEW:
Stop losing leads to these 3 automation mistakes...

[rest of content]
```

## Notes

- The queued file stays in `Content_To_Post/queued/` as backup
- The approval file in `Pending_Approval/` is for YOUR review
- Use the Human Section to write your feedback or edits
- Move to `Approved/` when ready → orchestrator will post via MCP
- Move to `Rejected/` if you don't want to post this