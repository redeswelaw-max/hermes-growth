#!/usr/bin/env python3
"""Migrate skills from hermes-growth-backup format to Hermes Agent format."""

import os
import re
import shutil
from pathlib import Path

SRC = Path("/Users/pablomeneses/Documents/Kimi Code/Hermes Growth/hermes-growth-backup/skills")
DST = Path("/Users/pablomeneses/Documents/Kimi Code/Hermes Growth/hermes-growth/optional-skills/growth-marketing")


def parse_skill_md(path: Path) -> dict:
    """Parse a SKILL.md file into frontmatter + body + metadata."""
    text = path.read_text(encoding="utf-8")
    
    # Split frontmatter
    if text.startswith("---"):
        _, rest = text.split("---", 1)
        frontmatter_text, body = rest.split("---", 1)
    else:
        frontmatter_text = ""
        body = text
    
    # Parse frontmatter
    frontmatter = {}
    for line in frontmatter_text.strip().split("\n"):
        if ":" in line:
            key, val = line.split(":", 1)
            frontmatter[key.strip()] = val.strip().strip('"').strip("'")
    
    # Extract metadata.hermes block
    metadata = {}
    meta_match = re.search(r"---\nmetadata:\s*hermes:\s*(.*?)\n---", text, re.DOTALL)
    if meta_match:
        meta_text = meta_match.group(1)
        for line in meta_text.split("\n"):
            if ":" in line and not line.strip().startswith("-"):
                key, val = line.split(":", 1)
                key = key.strip()
                val = val.strip()
                if key in ("auto_load", "priority"):
                    try:
                        metadata[key] = eval(val)
                    except:
                        metadata[key] = val
                elif key == "tags":
                    metadata[key] = [t.strip().strip('"').strip("'") for t in val.strip("[]").split(",") if t.strip()]
                elif key == "related_skills":
                    metadata[key] = [t.strip().strip('"').strip("'") for t in val.strip("[]").split(",") if t.strip()]
                else:
                    metadata[key] = val
    
    return {
        "frontmatter": frontmatter,
        "body": body.strip(),
        "metadata": metadata,
    }


def convert_to_hermes_format(skill_dir: Path) -> str:
    """Convert a skill directory to Hermes SKILL.md format."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return None
    
    data = parse_skill_md(skill_md)
    fm = data["frontmatter"]
    meta = data["metadata"]
    
    name = skill_dir.name.lower().replace(" ", "-").replace("_", "-")
    description = fm.get("description", f"Growth/marketing skill: {name}")
    tags = meta.get("tags", ["growth", "marketing"])
    related = meta.get("related_skills", [])
    
    hermes_md = f"""---
name: {name}
description: {description}
version: 1.0.0
author: Hermes Growth
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: {tags}
    related_skills: {related if related else '[]'}
---

{data['body']}
"""
    return hermes_md


def main():
    DST.mkdir(parents=True, exist_ok=True)
    
    # Write DESCRIPTION.md
    (DST / "DESCRIPTION.md").write_text("""# Growth & Marketing Skills

Skills for growth marketing, content creation, analytics, and campaign management.
Integrated with Postiz for social publishing.
""")
    
    migrated = 0
    for skill_dir in sorted(SRC.iterdir()):
        if not skill_dir.is_dir():
            continue
        
        hermes_md = convert_to_hermes_format(skill_dir)
        if hermes_md is None:
            print(f"Skip {skill_dir.name}: no SKILL.md")
            continue
        
        # Create output directory
        out_dir = DST / skill_dir.name
        out_dir.mkdir(exist_ok=True)
        (out_dir / "SKILL.md").write_text(hermes_md, encoding="utf-8")
        
        # Copy references and scripts if they exist
        for subdir in ["references", "scripts", "evals", "templates"]:
            src_sub = skill_dir / subdir
            if src_sub.exists():
                dst_sub = out_dir / subdir
                if dst_sub.exists():
                    shutil.rmtree(dst_sub)
                shutil.copytree(src_sub, dst_sub)
        
        migrated += 1
        print(f"Migrated: {skill_dir.name}")
    
    print(f"\n✅ Migrated {migrated} skills to {DST}")


if __name__ == "__main__":
    main()
