"""
Postiz Lite — Minimal social media scheduling API for Hermes Agent.

A lightweight, self-hosted replacement for Postiz Cloud.
Runs on Railway free tier with SQLite (no PostgreSQL/Redis/Temporal needed).

Compatible with the Postiz Node SDK and Hermes postiz_tools.py.
"""

import os
import uuid
import json
import sqlite3
from datetime import datetime, timezone
from typing import List, Optional
from contextlib import contextmanager

from fastapi import FastAPI, Header, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

DB_PATH = os.environ.get("DB_PATH", "/data/postiz_lite.db")
API_KEY = os.environ.get("API_KEY", "change-me-in-production")

app = FastAPI(title="Postiz Lite", version="1.0.0")

# ── Database ────────────────────────────────────────────────────────────────

@contextmanager
def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS integrations (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                provider TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS posts (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                integration_id TEXT NOT NULL,
                integration_name TEXT,
                provider TEXT,
                status TEXT DEFAULT 'scheduled',
                scheduled_date TEXT,
                images TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                published_at TEXT
            );
        """)
        conn.commit()


# Seed demo integrations if table is empty
def seed_integrations():
    with get_db() as conn:
        cur = conn.execute("SELECT COUNT(*) FROM integrations")
        if cur.fetchone()[0] == 0:
            demo = [
                ("twitter-demo", "Twitter / X", "twitter", 1),
                ("linkedin-demo", "LinkedIn", "linkedin", 1),
                ("instagram-demo", "Instagram", "instagram", 1),
                ("facebook-demo", "Facebook", "facebook", 0),
            ]
            conn.executemany(
                "INSERT INTO integrations (id, name, provider, is_active) VALUES (?,?,?,?)",
                demo
            )
            conn.commit()


# ── Auth ────────────────────────────────────────────────────────────────────

def verify_key(auth: Optional[str] = Header(None, alias="Authorization")):
    if not auth or auth != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


# ── Models ──────────────────────────────────────────────────────────────────

class CreatePostRequest(BaseModel):
    type: str = Field(..., pattern="^(draft|schedule|now|update)$")
    shortLink: bool = False
    date: Optional[str] = None
    tags: List[dict] = Field(default_factory=list)
    posts: List[dict] = Field(..., min_length=1)


class PostContent(BaseModel):
    content: str
    image: Optional[List[dict]] = None


# ── Endpoints ───────────────────────────────────────────────────────────────

@app.get("/public/v1/integrations")
def list_integrations(auth: Optional[str] = Header(None, alias="Authorization")):
    verify_key(auth)
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, name, provider, is_active as isActive FROM integrations ORDER BY name"
        ).fetchall()
    return [{"id": r["id"], "name": r["name"], "provider": r["provider"], "isActive": bool(r["isActive"])} for r in rows]


@app.get("/public/v1/is-connected")
def is_connected(auth: Optional[str] = Header(None, alias="Authorization")):
    verify_key(auth)
    with get_db() as conn:
        cur = conn.execute("SELECT COUNT(*) FROM integrations WHERE is_active = 1")
        count = cur.fetchone()[0]
    return {"connected": count > 0, "count": count}


@app.post("/public/v1/posts")
def create_post(body: CreatePostRequest, auth: Optional[str] = Header(None, alias="Authorization")):
    verify_key(auth)
    post_id = str(uuid.uuid4())

    # Extract first post content
    first_post = body.posts[0]
    integration_id = first_post.get("integration", {}).get("id", "unknown")
    values = first_post.get("value", [{}])
    content = values[0].get("content", "") if values else ""
    images = json.dumps([i.get("path", "") for i in (values[0].get("image") or [])])

    # Determine status
    status = "draft"
    if body.type == "now":
        status = "published"
    elif body.type == "schedule":
        status = "scheduled"

    # Get integration name
    with get_db() as conn:
        row = conn.execute(
            "SELECT name, provider FROM integrations WHERE id = ?", (integration_id,)
        ).fetchone()
        integration_name = row["name"] if row else integration_id
        provider = row["provider"] if row else "unknown"

        conn.execute("""
            INSERT INTO posts (id, type, content, integration_id, integration_name, provider, status, scheduled_date, images)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (post_id, body.type, content, integration_id, integration_name, provider, status, body.date, images))
        conn.commit()

    return {
        "id": post_id,
        "type": body.type,
        "status": status,
        "content": content,
        "integration": integration_name,
        "date": body.date,
        "message": "Post saved to Postiz Lite. Schedule: " + (body.date or "immediate")
    }


@app.get("/public/v1/posts")
def list_posts(
    startDate: str,
    endDate: str,
    auth: Optional[str] = Header(None, alias="Authorization")
):
    verify_key(auth)
    with get_db() as conn:
        rows = conn.execute("""
            SELECT id, type, content, integration_name, provider, status, scheduled_date, images, created_at
            FROM posts
            WHERE scheduled_date BETWEEN ? AND ?
            ORDER BY scheduled_date DESC
        """, (startDate, endDate)).fetchall()

    result = []
    for r in rows:
        result.append({
            "id": r["id"],
            "type": r["type"],
            "status": r["status"],
            "date": r["scheduled_date"],
            "content": r["content"][:200],
            "integration": r["integration_name"],
            "provider": r["provider"],
            "createdAt": r["created_at"],
        })
    return result


@app.delete("/public/v1/posts/{post_id}")
def delete_post(post_id: str, auth: Optional[str] = Header(None, alias="Authorization")):
    verify_key(auth)
    with get_db() as conn:
        conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        conn.commit()
    return {"success": True, "id": post_id}


@app.post("/public/v1/upload")
def upload_file(
    file: UploadFile = File(...),
    auth: Optional[str] = Header(None, alias="Authorization")
):
    verify_key(auth)
    # In lite mode, we just return the filename as a pseudo-URL
    return {"url": f"/uploads/{file.filename}"}


@app.get("/health")
def health():
    return {"status": "ok", "service": "postiz-lite", "timestamp": datetime.now(timezone.utc).isoformat()}


# ── Startup ─────────────────────────────────────────────────────────────────

@app.on_event("startup")
def on_startup():
    init_db()
    seed_integrations()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
