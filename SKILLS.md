# Growth Marketing Skills — Developer Guide

> This document describes the 42 growth marketing skills packaged for Hermes Agent. These skills live in `optional-skills/growth-marketing/` and are discovered automatically at runtime.

---

## What is a Skill?

In Hermes Agent, a **skill** is a directory containing a `SKILL.md` file with:
- YAML frontmatter (name, description, version, tags)
- Markdown body with instructions for the agent

At startup, Hermes reads all `SKILL.md` files and makes them available to the model as contextual tools.

---

## Skill Format

```markdown
---
name: skill-name
description: What this skill helps the agent do
version: 1.0.0
metadata:
  hermes:
    tags: [growth, marketing]
---

# Skill Name

## Overview
Brief description of the skill's purpose.

## When to Use
- Situation 1
- Situation 2

## Process
1. Step one
2. Step two
3. Step three

## Output
What the agent should produce.

## Examples
### Example 1
Input: ...
Output: ...
```

---

## The 42 Growth Marketing Skills

### Acquisition
| Skill | Purpose |
|---|---|
| `ads` | Paid advertising strategy (Google Ads, Meta, LinkedIn) |
| `ad-creative` | Design and copy for ad creatives |
| `cold-email` | Outreach campaigns and sequences |
| `directory-submissions` | Submit product to directories and listings |
| `free-tools` | Build free tools as lead magnets |
| `lead-magnets` | Create ebooks, checklists, templates |
| `programmatic-seo` | Scale SEO with programmatic pages |
| `referrals` | Design referral programs |
| `signup` | Optimize signup flows and onboarding |
| `social` | Social media strategy and content |
| `video` | Video marketing and YouTube strategy |

### SEO & Content
| Skill | Purpose |
|---|---|
| `ai-seo` | AI-powered SEO optimization |
| `content-strategy` | Plan and execute content calendars |
| `copywriting` | Write persuasive copy |
| `copy-editing` | Refine and polish existing copy |
| `image` | Visual content strategy |
| `programmatic-seo` | Automated SEO at scale |
| `schema` | Implement structured data |
| `seo-audit` | Technical SEO audits |
| `site-architecture` | URL structure and internal linking |

### Conversion & Retention
| Skill | Purpose |
|---|---|
| `ab-testing` | Design and analyze A/B tests |
| `churn-prevention` | Reduce customer churn |
| `cro` | Conversion rate optimization |
| `onboarding` | User onboarding flows |
| `paywalls` | Pricing page and paywall optimization |
| `popups` | Modal and popup strategy |
| `pricing` | Pricing strategy and experiments |

### Analytics & Research
| Skill | Purpose |
|---|---|
| `analytics` | Set up and interpret analytics |
| `competitor-profiling` | Deep-dive competitor analysis |
| `competitors` | Competitive landscape monitoring |
| `customer-research` | Interviews, surveys, and insights |
| `marketing-psychology` | Behavioral economics for growth |

### Operations & Strategy
| Skill | Purpose |
|---|---|
| `aso` | App Store Optimization |
| `co-marketing` | Partnership and co-marketing campaigns |
| `community-marketing` | Build and nurture communities |
| `emails` | Email marketing campaigns |
| `hermes-growth-core` | Core growth framework and playbooks |
| `launch` | Product launch strategy |
| `marketing-ideas` | Ideation and brainstorming |
| `product-marketing` | Positioning, messaging, and GTM |
| `revops` | Revenue operations |
| `sales-enablement` | Equip sales teams with collateral |

---

## How Skills Are Loaded

Hermes Agent discovers skills from multiple sources:

1. **Built-in skills** (`skills/` directory)
2. **Optional skills** (`optional-skills/` directory) ← Our growth skills live here
3. **User skills** (`~/.hermes/skills/` at runtime)

The `optional-skills/growth-marketing/` directory is copied into the Docker image at build time:

```dockerfile
COPY . .
```

Since the entire repo is copied, `optional-skills/growth-marketing/` is included automatically.

---

## Adding a New Skill

### Step 1: Create the directory

```bash
mkdir optional-skills/growth-marketing/my-skill-name
touch optional-skills/growth-marketing/my-skill-name/SKILL.md
```

### Step 2: Write the SKILL.md

Follow the format above. Key rules:
- **Frontmatter is required** — Hermes parses it for discovery
- **Be specific** — The agent needs concrete instructions, not vague advice
- **Include examples** — Few-shot examples dramatically improve output quality
- **Tag correctly** — Use `tags: [growth, marketing]` for consistency

### Step 3: Test locally (optional)

```bash
# Run Hermes CLI with the skill
hermes chat -s "Test my new skill"
```

### Step 4: Commit and deploy

```bash
git add optional-skills/growth-marketing/my-skill-name/
git commit -m "Add skill: my-skill-name"
git push origin main
RAILWAY_API_TOKEN=... railway up
```

---

## Modifying an Existing Skill

1. Edit the `SKILL.md`
2. Bump the version in frontmatter if it's a significant change
3. Commit, push, and deploy

No restart needed — Hermes reads skills at startup, so a new deploy loads the changes.

---

## Removing a Skill

```bash
rm -rf optional-skills/growth-marketing/unwanted-skill/
git add -A
git commit -m "Remove skill: unwanted-skill"
git push origin main
RAILWAY_API_TOKEN=... railway up
```

---

## Skill Quality Checklist

Before adding a skill, verify:

- [ ] YAML frontmatter is valid (use a YAML linter)
- [ ] `name` is unique and kebab-case
- [ ] `description` is clear and under 200 characters
- [ ] Tags include `[growth, marketing]`
- [ ] Body has clear structure (Overview, When to Use, Process, Output)
- [ ] At least one concrete example
- [ ] No external dependencies (skills are pure text instructions)
- [ ] No secrets or API keys in the skill file

---

## Merging Upstream Hermes Changes

When Hermes releases a new version:

1. Check upstream release notes for skill system changes
2. Update `pyproject.toml` version if needed
3. Regenerate `uv.lock`: `uv lock`
4. Rebuild frontends if web/TUI changed
5. Test skills still load correctly
6. Deploy

---

*For deployment instructions, see `DEPLOYMENT.md`.*
