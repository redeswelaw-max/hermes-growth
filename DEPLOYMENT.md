# Hermes Growth — Deployment & Maintenance Guide

> This document covers everything needed to maintain, update, and troubleshoot the Hermes Growth deployment on Railway. It supplements the upstream [Hermes Agent documentation](https://hermes-agent.nousresearch.com/docs/).

---

## Architecture Overview

```
┌─────────────────────────────────────────┐
│  Railway (disciplined-eagerness)        │
│  Service: hermes-growth                 │
│  Region: us-east4 (iad)                 │
│                                          │
│  ┌─────────────────────────────────┐    │
│  │  Container: ghcr.io/astral-sh/  │    │
│  │  uv:python3.12-bookworm-slim    │    │
│  │                                 │    │
│  │  Hermes Agent v0.14.0           │    │
│  │  ├─ Telegram Bot (polling)      │    │
│  │  ├─ 42 growth-marketing skills  │    │
│  │  ├─ Kimi K2.6 provider          │    │
│  │  └─ Pre-built web dashboard     │    │
│  └─────────────────────────────────┘    │
│                                          │
│  Env vars (baked in Dockerfile):        │
│  ├─ KIMI_API_KEY                        │
│  ├─ TELEGRAM_BOT_TOKEN                  │
│  ├─ GATEWAY_ALLOW_ALL_USERS=true        │
│  └─ HERMES_ALLOW_ROOT_GATEWAY=1         │
└─────────────────────────────────────────┘
           │
           ▼
    Telegram API (long-polling)
           │
           ▼
    Kimi/Moonshot API (api.moonshot.ai)
```

---

## Repository Structure

```
hermes-growth/
├── Dockerfile                          # Optimized build (see below)
├── railway.toml                        # Railway service configuration
├── DEPLOYMENT.md                       # This file
├── README.md                           # Upstream Hermes README (keep intact)
├── pyproject.toml                      # Hermes v0.14.0 dependencies
├── uv.lock                             # Exact dependency lock
│
├── hermes_cli/web_dist/                # ← Pre-built web dashboard assets
│   ├── index.html                      #    (do NOT delete)
│   └── assets/                         #
│
├── ui-tui/dist/                        # ← Pre-built TUI bundle
│   └── entry.js                        #    (do NOT delete)
│
├── optional-skills/growth-marketing/   # 42 growth marketing skills
│   ├── DESCRIPTION.md
│   ├── ab-testing/
│   ├── ai-seo/
│   ├── copywriting/
│   └── ... (see full list below)
│
└── plugins/model-providers/kimi-coding/# Kimi K2.6 provider profile
    ├── plugin.yaml
    └── __init__.py
```

**Pre-built assets** (`hermes_cli/web_dist/`, `ui-tui/dist/`) are committed to the repo so Railway does not need Node.js at build time. This is critical — removing them will break the build.

---

## The Dockerfile Strategy

The Dockerfile is intentionally minimal compared to upstream:

| What we SKIP | Why |
|---|---|
| `git clone` from GitHub | Repo already contains Hermes source |
| Node.js installation | Frontends pre-built locally and committed |
| `npm install && npm run build` | Already done locally, output is in repo |
| Complex entrypoint.sh | Railway runs as root, we use `tini` directly |

### Build flow

```dockerfile
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
RUN apt-get install tini              # Only system dep needed
WORKDIR /opt/hermes
COPY . .                              # Copy entire repo
RUN uv venv .venv && \
    VIRTUAL_ENV=/opt/hermes/.venv uv sync --frozen --extra cli,mcp,messaging,web
ENV PATH="/opt/hermes/.venv/bin:$PATH"
ENV ...                               # All env vars baked here
ENTRYPOINT ["/usr/bin/tini", "-g", "--"]
CMD ["hermes", "gateway"]
```

**`uv sync --frozen`** is the key: it uses the committed `uv.lock` without re-resolving dependencies, making the build fast and reproducible.

---

## Environment Variables

All critical variables are **baked into the Dockerfile** (`ENV` directives). Railway's `[deploy.env]` is NOT injected when using `builder = "dockerfile"` — this is a known Railway behavior.

### Current variables (in Dockerfile)

| Variable | Value | Purpose |
|---|---|---|
| `KIMI_API_KEY` | `sk-kimi-dLLtefCcIELCsaejYCwJD5zd66vNOQhawc1rna5wKm4I5ALI2fYhnasRMlCtfWxC` | Kimi/Moonshot API key |
| `KIMI_BASE_URL` | `https://api.moonshot.ai/v1` | Kimi API endpoint |
| `TELEGRAM_BOT_TOKEN` | `8603805979:AAH_qWK_eIrBRfX9SnBrveVI4FgH-UHA3fk` | Telegram BotFather token |
| `GATEWAY_ALLOW_ALL_USERS` | `true` | Allow any Telegram user to chat |
| `HERMES_ALLOW_ROOT_GATEWAY` | `1` | Required — Railway containers run as root |
| `HERMES_HOME` | `/data/.hermes` | Runtime data directory |
| `PYTHONUNBUFFERED` | `1` | Force Python stdout/stderr flush |
| `POSTIZ_API_KEY` | *(empty)* | Postiz API key (optional — enables social media tools) |
| `POSTIZ_BASE_URL` | `https://api.postiz.com` | Postiz instance URL |

### Changing environment variables

1. Edit `Dockerfile`
2. `git add Dockerfile && git commit -m "..." && git push origin main`
3. `RAILWAY_API_TOKEN=... railway up`

⚠️ **Never commit plain secrets to a public repo.** This repo is private, but rotate keys if you ever make it public.

---

## How to Deploy

### Prerequisites

```bash
# Railway CLI with API token
export RAILWAY_API_TOKEN="5a1a97bf-4f29-4d02-9dbd-f5b349ecf35f"

# Verify auth
railway status
```

### Deploy command

```bash
cd hermes-growth/
railway up
```

This uploads the repo, triggers a Docker build, and deploys the new container.

### Monitor deploy

```bash
# Get deployment ID from railway up output, then:
railway logs <DEPLOYMENT_ID> -d --lines 100

# Or check service status
railway status
```

### Rollback

Railway keeps previous deployments. To rollback via the Railway dashboard:
1. Go to https://railway.com/project/e992b311-7c00-47ba-97ed-46ba0e8e16d4
2. Find the previous deployment
3. Click "Redeploy"

---

## Pre-building Frontends (Local)

If you modify the web dashboard (`web/`) or TUI (`ui-tui/`), you **must** rebuild them locally before pushing:

```bash
# Web dashboard
cd web/
npm install
npm run build
# Output goes to ../hermes_cli/web_dist/

cd ../ui-tui/
npm install
npm run build
# Output goes to dist/entry.js

git add hermes_cli/web_dist/ ui-tui/dist/
git commit -m "Rebuild frontends"
git push origin main
```

⚠️ If you forget to rebuild, the deployed app will serve stale assets or crash.

---

## Working with Skills

### Directory structure

```
optional-skills/growth-marketing/
├── DESCRIPTION.md              # Catalog description
├── <skill-name>/
│   └── SKILL.md               # Skill definition + YAML frontmatter
└── ...
```

### Adding a new skill

1. Create directory: `optional-skills/growth-marketing/my-new-skill/`
2. Add `SKILL.md` with YAML frontmatter:

```markdown
---
name: my-new-skill
description: What this skill does
version: 1.0.0
metadata:
  hermes:
    tags: [growth, marketing]
---

# My New Skill

Instructions for the agent...
```

3. Commit and push — skills are discovered automatically at runtime.

### Modifying existing skills

Edit the `SKILL.md` file directly. Changes take effect on next deploy (Hermes reads skills at startup).

### Full skill list (42)

| # | Skill | Tags |
|---|---|---|
| 1 | ab-testing | growth, marketing |
| 2 | ad-creative | growth, marketing |
| 3 | ads | growth, marketing |
| 4 | ai-seo | growth, marketing |
| 5 | analytics | growth, marketing |
| 6 | aso | growth, marketing |
| 7 | churn-prevention | growth, marketing |
| 8 | co-marketing | growth, marketing |
| 9 | cold-email | growth, marketing |
| 10 | community-marketing | growth, marketing |
| 11 | competitor-profiling | growth, marketing |
| 12 | competitors | growth, marketing |
| 13 | content-strategy | growth, marketing |
| 14 | copy-editing | growth, marketing |
| 15 | copywriting | growth, marketing |
| 16 | cro | growth, marketing |
| 17 | customer-research | growth, marketing |
| 18 | directory-submissions | growth, marketing |
| 19 | emails | growth, marketing |
| 20 | free-tools | growth, marketing |
| 21 | hermes-growth-core | growth, marketing |
| 22 | image | growth, marketing |
| 23 | launch | growth, marketing |
| 24 | lead-magnets | growth, marketing |
| 25 | marketing-ideas | growth, marketing |
| 26 | marketing-psychology | growth, marketing |
| 27 | onboarding | growth, marketing |
| 28 | paywalls | growth, marketing |
| 29 | popups | growth, marketing |
| 30 | pricing | growth, marketing |
| 31 | product-marketing | growth, marketing |
| 32 | programmatic-seo | growth, marketing |
| 33 | referrals | growth, marketing |
| 34 | revops | growth, marketing |
| 35 | sales-enablement | growth, marketing |
| 36 | schema | growth, marketing |
| 37 | seo-audit | growth, marketing |
| 38 | signup | growth, marketing |
| 39 | site-architecture | growth, marketing |
| 40 | social | growth, marketing |
| 41 | video | growth, marketing |

---

## Provider: Kimi K2.6

### Files

- `plugins/model-providers/kimi-coding/plugin.yaml` — Declares the provider
- `plugins/model-providers/kimi-coding/__init__.py` — `KimiProfile` class

### Configuration

The provider is **auto-detected** by Hermes. To use it:

```bash
# In Telegram (or CLI)
hermes model set kimi-coding
# or
hermes model set kimi
```

The profile sets:
- Base URL: `https://api.moonshot.ai/v1`
- Default max tokens: 32,000
- Default aux model: `kimi-k2-turbo-preview`
- Reasoning effort: `medium`

### Changing model parameters

Edit `plugins/model-providers/kimi-coding/__init__.py`:

```python
kimi = KimiProfile(
    name="kimi-coding",
    aliases=("kimi", "moonshot", "kimi-for-coding"),
    env_vars=("KIMI_API_KEY", "KIMI_CODING_API_KEY"),
    base_url="https://api.moonshot.ai/v1",
    fixed_temperature=OMIT_TEMPERATURE,
    default_max_tokens=32000,      # ← Change this
    default_aux_model="kimi-k2-turbo-preview",
)
```

Then commit, push, and `railway up`.

---

## Troubleshooting

### "Refusing to run the Hermes gateway as root"

**Cause:** `HERMES_ALLOW_ROOT_GATEWAY=1` is missing.

**Fix:** Add it to the Dockerfile (`ENV HERMES_ALLOW_ROOT_GATEWAY=1`), commit, push, redeploy.

---

### "No user allowlists configured. All unauthorized users will be denied"

**Cause:** `GATEWAY_ALLOW_ALL_USERS` is not set.

**Fix:** Add `ENV GATEWAY_ALLOW_ALL_USERS=true` to Dockerfile. Or set `TELEGRAM_ALLOWED_USERS=<your_user_id>` for restricted access.

---

### "Telegram polling conflict"

**Cause:** Two instances of the bot are running simultaneously (old + new deployment).

**Fix:** Wait 30–60 seconds. Railway tears down the old container automatically.

---

### Build fails with "out of memory" or timeout

**Cause:** Railway's builder has limited resources.

**Fix:** The Dockerfile is already optimized. If it still fails:
- Ensure `uv.lock` is up-to-date (`uv lock` locally)
- Remove unnecessary extras from `uv sync` line in Dockerfile
- Consider using fewer extras (e.g., drop `--extra web` if dashboard is not needed)

---

### Deploy marks SUCCESS but bot doesn't respond

**Cause:** `TELEGRAM_BOT_TOKEN` may be invalid or missing.

**Fix:**
1. Verify token with: `curl "https://api.telegram.org/bot<TOKEN>/getMe"`
2. Check that token is in Dockerfile
3. Check Railway logs for startup errors

---

### "Application not found" on /health

**Expected.** Hermes gateway does not expose an HTTP server — it uses Telegram long-polling. The `healthcheckPath` was removed from `railway.toml` for this reason. Railway marks SUCCESS based on process liveness, not HTTP health.

---

## Railway Project Details

| Property | Value |
|---|---|
| Project name | `disciplined-eagerness` |
| Project ID | `e992b311-7c00-47ba-97ed-46ba0e8e16d4` |
| Service name | `hermes-growth` |
| Service ID | `97ad8865-bcb7-4253-b2e3-687598271e12` |
| Environment | `production` |
| Environment ID | `4570a2f4-40e6-4789-8e5c-4381f4cae55a` |
| Region | `us-east4` (iad) |
| GitHub repo | `redeswelaw-max/hermes-growth` |

### Railway CLI auth

```bash
export RAILWAY_API_TOKEN="5a1a97bf-4f29-4d02-9dbd-f5b349ecf35f"
railway status
```

If token expires, get a new one at https://railway.com/account/tokens

---

## Future Roadmap

- [x] Postiz integration (social media scheduling tools + skill)
- [ ] Add `TELEGRAM_ALLOWED_USERS` for restricted access
- [ ] Web dashboard access (requires exposing port + HTTPS)
- [ ] Add more providers (OpenRouter fallback)
- [ ] Cron jobs for automated growth tasks

---

*Last updated: 2026-05-16*
*Hermes Agent version: 0.14.0*
*Deployment: Railway (Docker)*
