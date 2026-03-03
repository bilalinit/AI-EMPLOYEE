---
description: Generate a Facebook/Instagram post for business. Creates clean file in Content_To_Post/queued/ and review copy with Human Section in Pending_Approval/.
---

# Meta Posting Skill (Facebook + Instagram)

Generate business-focused content for Facebook and Instagram designed to generate leads and engagement.

## How It Works

1. **Analyzes business context** from your vault
2. **Generates ONE post idea** (works for both platforms)
3. **Creates TWO files**:
   - `Content_To_Post/queued/META_POST_[timestamp].md` → Clean post content only
   - `Pending_Approval/META_POST_[timestamp].md` → Post content + Human Section for review

## Usage

```
/meta-posting
```

## What Each File Contains

### File 1: `Content_To_Post/queued/META_POST_[timestamp].md` (Clean - No Human Section)

```markdown
---
type: meta_post
status: queued
created: [timestamp]
post_type: lead_generation
topic: [generated topic]
target_audience: [who this is for]
platforms: facebook, instagram
---

# [Hook Headline]

[Post content - 2-3 paragraphs with value, emoji-friendly]

## Key Takeaways
- [Point 1]
- [Point 2]
- [Point 3]

[Call-to-action]

[Hashtags - 10-15 for Instagram]
```

### File 2: `Pending_Approval/META_POST_[timestamp].md` (With Human Section for Review)

```markdown
---
type: meta_post
status: pending_approval
created: [timestamp]
post_type: lead_generation
topic: [generated topic]
target_audience: [who this is for]
platforms: facebook, instagram
queued_copy: Content_To_Post/queued/META_POST_[timestamp].md
---

# [Hook Headline]

[Post content - 2-3 paragraphs with value]

## Key Takeaways
- [Point 1]
- [Point 2]
- [Point 3]

[Call-to-action]

[Hashtags]

---

## Human Section
**Status:** [ ] Approve for posting  [ ] Request changes  [ ] Reject

**Platform Selection:**
[ ] Facebook only (text post)
[ ] Instagram only (image required)
[ ] Both Facebook and Instagram (image required)

**Image URL for Instagram:**
(Required if posting to Instagram)
```
Paste your image URL here: https://...

```

**Your Instructions:**
<!-- Write your feedback, edits, or instructions here -->

**Action if Approved:** Move this file to Approved/ folder
**Action if Changes:** Edit content above, add image URL, then move to Approved/
**Action if Reject:** Move to Rejected/ folder (queued copy will be removed too)
```

## Instructions to Claude

When this skill is invoked:

1. **Read Business_Goals.md** first to understand business context, services, and target audience

2. **Check Content_To_Post/posted/** folder for previous posts - avoid creating the EXACT same post/angle

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

6. **Include strong call-to-action** from Business_Goals.md (default to engagement):
   - "What's your experience? Comment below..."
   - "Have you tried this? Let me know in the comments..."
   - "Double tap if you agree! 👆"
   - "Save this for later! 📌"

7. **Add 10-15 hashtags** for Instagram (mix of broad and niche)

8. **Use emojis** - Instagram audiences expect 2-4 emojis per post

9. **Create TWO files**:
   - `Content_To_Post/queued/` → Clean post content (no Human Section)
   - `Pending_Approval/` → Post content + Human Section with image URL request

10. **Use filename format**: `META_POST_[topic_slug]_[timestamp].md`

11. **Inform the user** where the files were created

## File Naming Convention

```
META_POST_[topic_slug]_[YYYYMMDD_HHMMSS].md

Example: META_POST_automation_tips_20260224_143000.md
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

## Platform Differences

| Platform | Requirements |
|----------|-------------|
| **Facebook** | Text + optional image, no limit on hashtags |
| **Instagram** | **Image REQUIRED** + caption (2200 char max), 10-30 hashtags |
| **Both** | Include image URL in Human Section for Instagram |

## Hashtags to Use

Mix of:
- **Broad**: #business #entrepreneur #growth #success #motivation
- **Niche**: #automation #AI #leadgen #sales #productivity #tech
- **Engagement**: #smallbusiness #businesstips #marketing #digitalmarketing

## Length Guidelines

- **Facebook**: Ideal 500-1500 characters
- **Instagram**: Max 2200 characters (caption limit)
- **Safe target**: 800-1200 characters (works for both)

## Example Output Format

```
✅ Created Meta post: "3 Automation Mistakes Costing You Sales"

Files created:
📁 Content_To_Post/queued/META_POST_automation_mistakes_20260224_143000.md
📁 Pending_Approval/META_POST_automation_mistakes_20260224_143000.md

Review in Pending_Approval/ and:
1. Add your Instagram image URL in the Human Section
2. Select platforms (Facebook / Instagram / Both)
3. Move to Approved/ when ready to post

---
POST PREVIEW:
Stop losing leads to these 3 automation mistakes... 🛑

[rest of content]
```

## Notes

- The queued file stays in `Content_To_Post/queued/` as backup
- The approval file in `Pending_Approval/` is for YOUR review
- **Instagram REQUIRES an image URL** - user must provide it in Human Section
- Use the Human Section to select platforms and add feedback
- Move to `Approved/` when ready → orchestrator will post via MCP
- Move to `Rejected/` if you don't want to post this
