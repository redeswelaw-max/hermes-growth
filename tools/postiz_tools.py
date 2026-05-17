#!/usr/bin/env python3
"""
Postiz Social Media Scheduling Tools

Integrates Hermes Agent with Postiz (https://postiz.com) for social media
management: create scheduled posts, list connected accounts, view analytics,
and manage content across platforms (Twitter/X, LinkedIn, Instagram,
Facebook, TikTok, YouTube, Reddit, Pinterest, Threads, Bluesky, Mastodon,
Discord, Slack).

Environment variables:
    POSTIZ_API_KEY      API key from Postiz (Settings → API Keys)
    POSTIZ_BASE_URL     Postiz instance URL (default: https://api.postiz.com)

Usage:
    # These tools are auto-discovered by Hermes at startup.
    # The model calls them like any other tool.

    postiz_list_integrations() -> List connected social accounts
    postiz_create_post(...)    -> Schedule or publish a post
    postiz_list_posts(...)     -> View scheduled/published posts
    postiz_delete_post(...)    -> Remove a post
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx

from tools.registry import registry

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://api.postiz.com"


def _get_postiz_config():
    """Return (api_key, base_url) from environment."""
    api_key = os.environ.get("POSTIZ_API_KEY", "")
    base_url = os.environ.get("POSTIZ_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    return api_key, base_url


def _postiz_headers(api_key: str) -> Dict[str, str]:
    return {
        "Content-Type": "application/json",
        "Authorization": api_key,
    }


def check_postiz_config() -> tuple[bool, str]:
    """Check whether Postiz tools are available."""
    api_key, base_url = _get_postiz_config()
    if not api_key:
        return False, "POSTIZ_API_KEY not set. Add it to the Dockerfile or environment."
    return True, f"Postiz configured ({base_url})"


# ─────────────────────────────────────────────────────────────────────────────
# postiz_list_integrations
# ─────────────────────────────────────────────────────────────────────────────

def postiz_list_integrations_tool() -> str:
    """List all connected social media integrations."""
    api_key, base_url = _get_postiz_config()
    if not api_key:
        return "Error: POSTIZ_API_KEY not configured."

    url = f"{base_url}/public/v1/integrations"
    try:
        resp = httpx.get(url, headers=_postiz_headers(api_key), timeout=30)
        resp.raise_for_status()
        data = resp.json()

        integrations = data if isinstance(data, list) else data.get("data", [])
        if not integrations:
            return "No social media integrations connected. Connect accounts in Postiz first."

        lines = ["Connected social media integrations:", ""]
        for ig in integrations:
            name = ig.get("name", "Unknown")
            provider = ig.get("provider", "unknown")
            ig_id = ig.get("id", "N/A")
            status = "✅ active" if ig.get("isActive") else "⚠️ inactive"
            lines.append(f"- {name} ({provider}) [{ig_id}] — {status}")
        return "\n".join(lines)
    except httpx.HTTPStatusError as e:
        return f"Postiz API error: {e.response.status_code} — {e.response.text[:500]}"
    except Exception as e:
        return f"Error connecting to Postiz: {e}"


POSTIZ_LIST_INTEGRATIONS_SCHEMA = {
    "name": "postiz_list_integrations",
    "description": "List all connected social media accounts in Postiz (Twitter/X, LinkedIn, Instagram, Facebook, TikTok, etc.). Returns account names, providers, IDs, and active status. Use this before creating posts to know which accounts are available.",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# postiz_create_post
# ─────────────────────────────────────────────────────────────────────────────

def postiz_create_post_tool(
    content: str,
    integration_id: str,
    post_type: str = "schedule",
    date: Optional[str] = None,
    images: Optional[List[str]] = None,
) -> str:
    """Create a new social media post via Postiz."""
    api_key, base_url = _get_postiz_config()
    if not api_key:
        return "Error: POSTIZ_API_KEY not configured."

    if post_type not in ("draft", "schedule", "now", "update"):
        return f"Error: post_type must be one of draft, schedule, now, update. Got: {post_type}"

    # Default date to now if scheduling
    if post_type == "schedule" and not date:
        from datetime import datetime, timezone
        date = datetime.now(timezone.utc).isoformat()

    payload: Dict[str, Any] = {
        "type": post_type,
        "shortLink": False,
        "date": date or "",
        "tags": [],
        "posts": [
            {
                "integration": {"id": integration_id},
                "value": [
                    {
                        "content": content,
                        "image": [],
                    }
                ],
            }
        ],
    }

    # Attach image URLs if provided
    if images:
        for img_url in images:
            payload["posts"][0]["value"][0]["image"].append({"path": img_url})

    url = f"{base_url}/public/v1/posts"
    try:
        resp = httpx.post(
            url,
            headers=_postiz_headers(api_key),
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        post_id = data.get("id") if isinstance(data, dict) else None
        return (
            f"✅ Post created successfully!\n"
            f"Type: {post_type}\n"
            f"Integration: {integration_id}\n"
            f"Date: {date or 'immediate'}\n"
            f"Post ID: {post_id or 'N/A'}\n"
            f"Response: {json.dumps(data, indent=2)[:800]}"
        )
    except httpx.HTTPStatusError as e:
        return f"Postiz API error: {e.response.status_code} — {e.response.text[:1000]}"
    except Exception as e:
        return f"Error creating post: {e}"


POSTIZ_CREATE_POST_SCHEMA = {
    "name": "postiz_create_post",
    "description": "Create and schedule a social media post through Postiz. Supports Twitter/X, LinkedIn, Instagram, Facebook, TikTok, YouTube, Reddit, Pinterest, Threads, Bluesky, Mastodon, Discord, and Slack. Use postiz_list_integrations first to get the integration_id of the target account.",
    "parameters": {
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "The post text/content. Platform-specific limits apply (e.g., Twitter 280 chars).",
            },
            "integration_id": {
                "type": "string",
                "description": "The ID of the connected social account from postiz_list_integrations.",
            },
            "post_type": {
                "type": "string",
                "enum": ["draft", "schedule", "now", "update"],
                "description": "draft = save without publishing; schedule = publish at 'date'; now = publish immediately; update = modify existing.",
            },
            "date": {
                "type": "string",
                "description": "ISO 8601 datetime for scheduled posts (e.g., 2026-05-20T14:00:00Z). Required for 'schedule', ignored for 'now'.",
            },
            "images": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional list of image URLs to attach to the post.",
            },
        },
        "required": ["content", "integration_id", "post_type"],
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# postiz_list_posts
# ─────────────────────────────────────────────────────────────────────────────

def postiz_list_posts_tool(
    start_date: str,
    end_date: str,
) -> str:
    """List posts within a date range."""
    api_key, base_url = _get_postiz_config()
    if not api_key:
        return "Error: POSTIZ_API_KEY not configured."

    params = {"startDate": start_date, "endDate": end_date}
    url = f"{base_url}/public/v1/posts"
    try:
        resp = httpx.get(
            url,
            headers=_postiz_headers(api_key),
            params=params,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        posts = data if isinstance(data, list) else data.get("data", [])
        if not posts:
            return f"No posts found between {start_date} and {end_date}."

        lines = [f"Posts from {start_date} to {end_date}:", ""]
        for p in posts[:20]:  # Limit to 20
            post_id = p.get("id", "N/A")
            status = p.get("status", "unknown")
            date = p.get("date", "N/A")
            content = ""
            if p.get("posts") and len(p["posts"]) > 0:
                vals = p["posts"][0].get("value", [])
                if vals:
                    content = vals[0].get("content", "")[:100]
            lines.append(f"- [{post_id}] {status} @ {date}: {content}...")
        return "\n".join(lines)
    except httpx.HTTPStatusError as e:
        return f"Postiz API error: {e.response.status_code} — {e.response.text[:500]}"
    except Exception as e:
        return f"Error listing posts: {e}"


POSTIZ_LIST_POSTS_SCHEMA = {
    "name": "postiz_list_posts",
    "description": "List scheduled and published social media posts within a date range. Returns post IDs, status, dates, and preview content.",
    "parameters": {
        "type": "object",
        "properties": {
            "start_date": {
                "type": "string",
                "description": "Start date in ISO 8601 format (e.g., 2026-05-01).",
            },
            "end_date": {
                "type": "string",
                "description": "End date in ISO 8601 format (e.g., 2026-05-31).",
            },
        },
        "required": ["start_date", "end_date"],
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# postiz_delete_post
# ─────────────────────────────────────────────────────────────────────────────

def postiz_delete_post_tool(post_id: str) -> str:
    """Delete a post by ID."""
    api_key, base_url = _get_postiz_config()
    if not api_key:
        return "Error: POSTIZ_API_KEY not configured."

    url = f"{base_url}/public/v1/posts/{post_id}"
    try:
        resp = httpx.delete(url, headers=_postiz_headers(api_key), timeout=30)
        resp.raise_for_status()
        return f"✅ Post {post_id} deleted successfully."
    except httpx.HTTPStatusError as e:
        return f"Postiz API error: {e.response.status_code} — {e.response.text[:500]}"
    except Exception as e:
        return f"Error deleting post: {e}"


POSTIZ_DELETE_POST_SCHEMA = {
    "name": "postiz_delete_post",
    "description": "Delete a scheduled or draft post from Postiz by its ID. Use postiz_list_posts to find the ID.",
    "parameters": {
        "type": "object",
        "properties": {
            "post_id": {
                "type": "string",
                "description": "The ID of the post to delete.",
            },
        },
        "required": ["post_id"],
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Registry
# ─────────────────────────────────────────────────────────────────────────────

registry.register(
    name="postiz_list_integrations",
    toolset="postiz",
    schema=POSTIZ_LIST_INTEGRATIONS_SCHEMA,
    handler=lambda args, **kw: postiz_list_integrations_tool(),
    check_fn=check_postiz_config,
    requires_env=["POSTIZ_API_KEY"],
    emoji="📱",
)

registry.register(
    name="postiz_create_post",
    toolset="postiz",
    schema=POSTIZ_CREATE_POST_SCHEMA,
    handler=lambda args, **kw: postiz_create_post_tool(
        content=args.get("content", ""),
        integration_id=args.get("integration_id", ""),
        post_type=args.get("post_type", "schedule"),
        date=args.get("date"),
        images=args.get("images"),
    ),
    check_fn=check_postiz_config,
    requires_env=["POSTIZ_API_KEY"],
    emoji="📤",
)

registry.register(
    name="postiz_list_posts",
    toolset="postiz",
    schema=POSTIZ_LIST_POSTS_SCHEMA,
    handler=lambda args, **kw: postiz_list_posts_tool(
        start_date=args.get("start_date", ""),
        end_date=args.get("end_date", ""),
    ),
    check_fn=check_postiz_config,
    requires_env=["POSTIZ_API_KEY"],
    emoji="📋",
)

registry.register(
    name="postiz_delete_post",
    toolset="postiz",
    schema=POSTIZ_DELETE_POST_SCHEMA,
    handler=lambda args, **kw: postiz_delete_post_tool(
        post_id=args.get("post_id", ""),
    ),
    check_fn=check_postiz_config,
    requires_env=["POSTIZ_API_KEY"],
    emoji="🗑️",
)
