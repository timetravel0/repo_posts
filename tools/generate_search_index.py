#!/usr/bin/env python3
"""
Builds a tiny client-side search index at docs/assets/search-index.json.
Fields per entry:
  t: title + source URL + description (lowercased, for substring search)
  u: post URL (permalink)
  d: yyyy-mm-dd
  title: original title (for rendering)
  s: short description
  x: external source URL (optional for legacy posts)
"""
from __future__ import annotations
from pathlib import Path
import json, re

ROOT = Path(__file__).resolve().parents[1]
POSTS = ROOT / "docs" / "_posts"
OUT = ROOT / "docs" / "assets" / "search-index.json"

def _url(stem: str) -> str:
    y,m,d,rest = stem.split('-', 3)
    return f"/{y}/{m}/{d}/{rest}.html"

def _extract(md: str) -> str:
    value = _frontmatter(md, "title")
    if value:
        return value
    m = re.search(r"^#\s+(.+)$", md, re.M)
    return m.group(1).strip() if m else ""

def _desc(md: str) -> str:
    value = _frontmatter(md, "description")
    if value:
        return value[:160]
    # First non-heading, non-empty line after the H1
    m = re.search(r"^#\s+.+$(?:\r?\n)+([^#\n][^\n]+)", md, re.M)
    return (m.group(1).strip() if m else "")[:160]

def _frontmatter(md: str, key: str) -> str:
    m = re.search(rf"(?m)^{re.escape(key)}:\s*(.+?)\s*$", md)
    if not m:
        return ""
    raw = m.group(1).strip()
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        value = raw.strip('"').strip("'")
    return value if isinstance(value, str) else ""

def _external_url(md: str) -> str:
    value = _frontmatter(md, "external_url")
    if value:
        return value
    m = re.search(r"\]\(\s*<?(https?://[^)\s>]+)>?\s*\)", md, re.I)
    return m.group(1) if m else ""

def main() -> None:
    rows = []
    for p in sorted(POSTS.glob('*.md')):
        stem = p.stem
        md = p.read_text(encoding='utf-8', errors='ignore')
        title = _extract(md) or stem
        desc = _desc(md)
        external_url = _external_url(md)
        row = {
            't': (title + ' ' + external_url + ' ' + desc).lower(),
            'u': _url(stem),
            'd': '-'.join(stem.split('-', 3)[:3]),
            'title': title,
            's': desc,
        }
        if external_url:
            row['x'] = external_url
        rows.append(row)
    OUT.write_text(json.dumps(rows, ensure_ascii=False, separators=(',',':')), encoding='utf-8')
    print(f"Wrote {OUT} with {len(rows)} entries")

if __name__ == '__main__':
    main()
