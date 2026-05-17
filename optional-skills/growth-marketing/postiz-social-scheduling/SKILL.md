---
name: postiz-social-scheduling
description: Schedule, publish, and manage social media posts across 13+ platforms via Postiz (Twitter/X, LinkedIn, Instagram, Facebook, TikTok, YouTube, Reddit, Pinterest, Threads, Bluesky, Mastodon, Discord, Slack).
version: 1.0.0
metadata:
  hermes:
    tags: [growth, marketing, social-media, scheduling]
---

# Postiz Social Media Scheduling

## Overview

This skill enables you to manage social media content through Postiz — a unified scheduling platform for 13+ social networks. You can create posts, schedule them for optimal times, list existing content, and delete posts — all without leaving the conversation.

## When to Use

- **Content calendar planning**: Schedule a week or month of posts in advance
- **Cross-platform publishing**: Publish the same message to multiple accounts
- **Campaign management**: Coordinate launch posts across Twitter, LinkedIn, and Instagram
- **Analytics review**: Check what content is scheduled and when
- **Crisis management**: Delete or update posts quickly

## Prerequisites

1. Postiz account with API key configured
2. Social media accounts connected in Postiz
3. The `postiz_*` tools are available when `POSTIZ_API_KEY` is set

## Available Tools

| Tool | Purpose |
|---|---|
| `postiz_list_integrations` | See which social accounts are connected |
| `postiz_create_post` | Create and schedule a post |
| `postiz_list_posts` | View scheduled/published posts in a date range |
| `postiz_delete_post` | Remove a scheduled or draft post |

## Workflow

### 1. Discover connected accounts

Always start by listing available integrations:

```
postiz_list_integrations()
```

Sample output:
```
Connected social media integrations:
- @MyBrand Twitter (twitter) [abc123] — ✅ active
- MyBrand LinkedIn (linkedin) [def456] — ✅ active
- MyBrand Instagram (instagram) [ghi789] — ✅ active
```

### 2. Create a post

Use the `integration_id` from step 1:

```
postiz_create_post(
  content="🚀 Excited to announce our new feature! Check it out at example.com",
  integration_id="abc123",
  post_type="schedule",
  date="2026-05-20T14:00:00Z"
)
```

**Post types:**
- `now` — Publish immediately
- `schedule` — Publish at the specified `date`
- `draft` — Save without publishing
- `update` — Modify an existing post

**Platform-specific tips:**
- **Twitter/X**: Keep under 280 characters
- **LinkedIn**: Professional tone, up to 3,000 characters
- **Instagram**: Visual-first; attach images when possible
- **Threads**: Casual, conversational tone

### 3. Review scheduled content

```
postiz_list_posts(start_date="2026-05-01", end_date="2026-05-31")
```

### 4. Delete if needed

```
postiz_delete_post(post_id="post-id-from-list")
```

## Multi-Platform Campaign Example

**Goal**: Launch a product across Twitter, LinkedIn, and Instagram simultaneously.

**Step 1**: List integrations to get IDs.

**Step 2**: Create posts for each platform with tailored messaging:

```
postiz_create_post(
  content="🚀 LAUNCH DAY! Our AI-powered growth tool is live. First 100 users get 50% off. Link in bio! #AITools #GrowthMarketing",
  integration_id="instagram-id",
  post_type="schedule",
  date="2026-05-20T09:00:00Z"
)

postiz_create_post(
  content="We're thrilled to announce the launch of our AI-powered growth marketing platform. After 18 months of development, it's finally here. Read the full announcement: [link]",
  integration_id="linkedin-id",
  post_type="schedule",
  date="2026-05-20T09:00:00Z"
)

postiz_create_post(
  content="🚀 It's here! Our AI growth tool just launched. Get 50% off for the first 100 users → example.com/launch #buildinpublic",
  integration_id="twitter-id",
  post_type="schedule",
  date="2026-05-20T09:00:00Z"
)
```

## Best Practices

- **Always check integrations first** — accounts may be disconnected
- **Use scheduling for consistency** — maintain a regular posting rhythm
- **Tailor content per platform** — don't copy-paste identical text everywhere
- **Respect platform limits** — Twitter 280 chars, Instagram visual-first
- **Use UTC for dates** — avoids timezone confusion
- **Attach images when relevant** — visual content performs better

## Troubleshooting

| Error | Solution |
|---|---|
| "POSTIZ_API_KEY not configured" | Add POSTIZ_API_KEY to the Dockerfile env vars |
| "No integrations connected" | Connect social accounts in Postiz dashboard first |
| "API error 401" | API key is invalid or expired — regenerate in Postiz settings |
| "API error 400" | Check post content format — may exceed platform limits |

## Related Skills

- `social` — Social media strategy and content planning
- `content-strategy` — Content calendar and editorial planning
- `analytics` — Review performance metrics
- `marketing-ideas` — Brainstorm campaign concepts
