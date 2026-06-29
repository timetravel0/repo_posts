#!/usr/bin/env python3
"""Create Jekyll posts from arbitrary public web links.

Examples:
  python tools/add_links.py https://example.com/article
  LINKS=$'https://example.com/one\nhttps://example.com/two' \
    python tools/add_links.py --urls-env LINKS

The generated Markdown is an implementation detail: callers only provide URLs.
Page metadata is fetched from Open Graph or standard HTML tags when available.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import ipaddress
import json
import os
import re
import socket
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
POSTS = ROOT / "docs" / "_posts"
MAX_HTML_BYTES = 2 * 1024 * 1024
USER_AGENT = "repo-posts-link-importer/1.0"


class LinkError(ValueError):
    """Raised when a link cannot be safely imported."""


@dataclass(frozen=True)
class LinkSpec:
    url: str
    title: str = ""
    description: str = ""


@dataclass(frozen=True)
class PageMetadata:
    title: str
    description: str


class MetadataParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.meta: dict[str, str] = {}
        self._in_title = False
        self._title_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {str(k).lower(): (v or "") for k, v in attrs}
        if tag.lower() == "title":
            self._in_title = True
        if tag.lower() != "meta":
            return
        key = (attrs_dict.get("property") or attrs_dict.get("name") or "").lower()
        value = attrs_dict.get("content", "").strip()
        if key and value and key not in self.meta:
            self.meta[key] = value

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title_parts.append(data)

    @property
    def document_title(self) -> str:
        return " ".join(self._title_parts)


def _clean_text(value: str, limit: int) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"\s+", " ", value).strip()
    return value[:limit].rstrip()


def normalize_url(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        raise LinkError("empty URL")
    if "://" not in raw:
        raw = "https://" + raw
    parts = urlsplit(raw)
    if parts.scheme.lower() not in {"http", "https"}:
        raise LinkError(f"unsupported URL scheme: {parts.scheme or '(missing)'}")
    if not parts.hostname or parts.username or parts.password:
        raise LinkError("URL must contain a public host and no credentials")
    try:
        host = parts.hostname.encode("idna").decode("ascii").lower()
        port = parts.port
    except (UnicodeError, ValueError) as exc:
        raise LinkError(f"invalid host or port: {exc}") from exc
    netloc = host
    if ":" in host and not host.startswith("["):
        netloc = f"[{host}]"
    if port is not None:
        netloc += f":{port}"
    path = parts.path or "/"
    if path != "/":
        path = path.rstrip("/")
    return urlunsplit((parts.scheme.lower(), netloc, path, parts.query, ""))


def ensure_public_url(url: str) -> None:
    parts = urlsplit(url)
    host = parts.hostname or ""
    if host == "localhost" or host.endswith(".localhost"):
        raise LinkError("local hosts are not allowed")
    port = parts.port or (443 if parts.scheme == "https" else 80)
    try:
        addresses = {
            item[4][0]
            for item in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        }
    except socket.gaierror as exc:
        raise LinkError(f"cannot resolve {host}: {exc}") from exc
    if not addresses:
        raise LinkError(f"cannot resolve {host}")
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if not ip.is_global:
            raise LinkError(f"non-public destination is not allowed: {address}")


class SafeRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        normalized = normalize_url(newurl)
        ensure_public_url(normalized)
        return super().redirect_request(req, fp, code, msg, headers, normalized)


def fetch_metadata(url: str, timeout: float = 15.0) -> PageMetadata:
    ensure_public_url(url)
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.1",
        },
    )
    opener = build_opener(SafeRedirectHandler())
    try:
        with opener.open(request, timeout=timeout) as response:
            content_type = response.headers.get_content_type()
            charset = response.headers.get_content_charset() or "utf-8"
            body = response.read(MAX_HTML_BYTES + 1)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        print(f"warning: metadata fetch failed for {url}: {exc}", file=sys.stderr)
        return PageMetadata("", "")
    if len(body) > MAX_HTML_BYTES:
        print(f"warning: metadata response exceeded {MAX_HTML_BYTES} bytes: {url}", file=sys.stderr)
        body = body[:MAX_HTML_BYTES]
    if content_type not in {"text/html", "application/xhtml+xml"}:
        return PageMetadata("", "")
    parser = MetadataParser()
    try:
        parser.feed(body.decode(charset, errors="replace"))
    except (LookupError, UnicodeError):
        parser.feed(body.decode("utf-8", errors="replace"))
    title = (
        parser.meta.get("og:title")
        or parser.meta.get("twitter:title")
        or parser.document_title
    )
    description = (
        parser.meta.get("og:description")
        or parser.meta.get("description")
        or parser.meta.get("twitter:description")
        or ""
    )
    return PageMetadata(_clean_text(title, 180), _clean_text(description, 500))


def parse_specs(lines: list[str]) -> list[LinkSpec]:
    specs: list[LinkSpec] = []
    expanded: list[tuple[int, str]] = []
    for line_number, raw in enumerate(lines, 1):
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        if "|" not in raw and len(raw.split()) > 1:
            expanded.extend((line_number, item) for item in raw.split())
        else:
            expanded.append((line_number, raw))
    for line_number, raw in expanded:
        parts = [part.strip() for part in raw.split("|", 2)]
        try:
            url = normalize_url(parts[0])
        except LinkError as exc:
            raise LinkError(f"line {line_number}: {exc}") from exc
        title = _clean_text(parts[1], 180) if len(parts) > 1 else ""
        description = _clean_text(parts[2], 500) if len(parts) > 2 else ""
        specs.append(LinkSpec(url, title, description))
    return specs


def _fallback_title(url: str) -> str:
    parts = urlsplit(url)
    path_name = parts.path.rstrip("/").rsplit("/", 1)[-1]
    return _clean_text(path_name.replace("-", " ").replace("_", " "), 180) or parts.hostname or url


def _slug_for_url(url: str) -> str:
    parts = urlsplit(url)
    raw = f"{parts.hostname or ''}-{parts.path.strip('/')}"
    slug = re.sub(r"[^A-Za-z0-9]+", "-", raw).strip("-").lower()
    slug = slug[:90].rstrip("-") or "link"
    if parts.query:
        slug += "-" + hashlib.sha256(url.encode("utf-8")).hexdigest()[:8]
    return slug


def _yaml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _markdown_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")


def build_post(spec: LinkSpec, metadata: PageMetadata, published_at: datetime) -> str:
    title = spec.title or metadata.title or _fallback_title(spec.url)
    description = spec.description or metadata.description
    source_type = "github" if urlsplit(spec.url).hostname == "github.com" else "web"
    lines = [
        "---",
        "layout: default",
        f"date: {published_at.isoformat(timespec='seconds')}",
        f"title: {_yaml_string(title)}",
        f"external_url: {_yaml_string(spec.url)}",
        f"source_type: {source_type}",
        f"description: {_yaml_string(description)}",
        "---",
        "",
        f"# [{_markdown_text(title)}](<{spec.url}>)",
    ]
    if description:
        lines.extend(["", description])
    return "\n".join(lines) + "\n"


def _frontmatter_url(markdown: str) -> str:
    match = re.search(r"(?m)^external_url:\s*(.+?)\s*$", markdown)
    if not match:
        return ""
    raw = match.group(1).strip()
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        value = raw.strip("'\"")
    return value if isinstance(value, str) else ""


def existing_urls() -> set[str]:
    urls: set[str] = set()
    markdown_link = re.compile(r"\]\(\s*<?(https?://[^)\s>]+)>?\s*\)", re.I)
    for path in POSTS.glob("*.md"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        candidates = [_frontmatter_url(text)]
        candidates.extend(markdown_link.findall(text))
        for candidate in candidates:
            if not candidate:
                continue
            try:
                urls.add(normalize_url(candidate))
            except LinkError:
                continue
    return urls


def output_path(url: str, published_at: datetime) -> Path:
    date_prefix = published_at.date().isoformat()
    base = POSTS / f"{date_prefix}-{_slug_for_url(url)}.md"
    if not base.exists():
        return base
    existing = _frontmatter_url(base.read_text(encoding="utf-8", errors="ignore"))
    if existing:
        try:
            if normalize_url(existing) == url:
                return base
        except LinkError:
            pass
    suffix = hashlib.sha256(url.encode("utf-8")).hexdigest()[:8]
    return POSTS / f"{date_prefix}-{_slug_for_url(url)}-{suffix}.md"


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create posts from public web links")
    parser.add_argument("urls", nargs="*", help="HTTP(S) URLs")
    parser.add_argument("--input-file", type=Path, help="file containing one URL per line")
    parser.add_argument("--urls-env", help="environment variable containing newline-separated URLs")
    parser.add_argument("--date", help="publication timestamp in ISO-8601 format")
    parser.add_argument("--no-fetch", action="store_true", help="skip remote metadata fetching")
    parser.add_argument("--dry-run", action="store_true", help="show generated paths without writing")
    return parser.parse_args()


def main() -> int:
    args = _arguments()
    lines = list(args.urls)
    if args.input_file:
        lines.extend(args.input_file.read_text(encoding="utf-8").splitlines())
    if args.urls_env:
        lines.extend(os.environ.get(args.urls_env, "").splitlines())
    try:
        specs = parse_specs(lines)
    except LinkError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if not specs:
        print("error: no URLs provided", file=sys.stderr)
        return 2
    if args.date:
        try:
            published_at = datetime.fromisoformat(args.date.replace("Z", "+00:00"))
        except ValueError as exc:
            print(f"error: invalid --date: {exc}", file=sys.stderr)
            return 2
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
    else:
        published_at = datetime.now(timezone.utc)

    known = existing_urls()
    pending: list[tuple[Path, str, str]] = []
    reserved_paths: set[Path] = set()
    for spec in specs:
        if spec.url in known:
            print(f"skip duplicate: {spec.url}")
            continue
        metadata = PageMetadata("", "") if args.no_fetch else fetch_metadata(spec.url)
        path = output_path(spec.url, published_at)
        if path in reserved_paths:
            suffix = hashlib.sha256(spec.url.encode("utf-8")).hexdigest()[:8]
            path = path.with_name(f"{path.stem}-{suffix}{path.suffix}")
        pending.append((path, build_post(spec, metadata, published_at), spec.url))
        reserved_paths.add(path)
        known.add(spec.url)

    if not pending:
        print("No new links to add.")
        return 0
    for path, content, url in pending:
        relative = path.relative_to(ROOT)
        if args.dry_run:
            print(f"would add {relative}: {url}")
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"added {relative}: {url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
