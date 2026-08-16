"""Fetch pages and keep a byte-exact snapshot of everything seen.

The snapshot is the provenance record. If a parser bug is found in six months,
the raw bytes are still there and the whole history can be reparsed. Snapshots
are content-addressed, so an unchanged page costs nothing.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import httpx
from selectolax.parser import HTMLParser

USER_AGENT = (
    "GridWatchZW/0.1 (+https://github.com/PeterTheDataScientist/gridwatch-zw; "
    "public-interest research on load shedding schedule reliability)"
)


@dataclass(slots=True)
class Fetched:
    url: str
    status: int
    body: bytes
    sha256: str
    fetched_at: datetime
    from_cache: bool


def visible_text(html: bytes) -> str:
    """Text a human would see. Script and style content is dropped."""
    tree = HTMLParser(html.decode("utf-8", errors="replace"))
    for tag in tree.css("script, style, noscript"):
        tag.decompose()
    body = tree.body
    return body.text(separator="\n") if body else ""


def fetch(url: str, raw_dir: Path, *, timeout: float = 30.0) -> Fetched:
    raw_dir.mkdir(parents=True, exist_ok=True)
    with httpx.Client(
        follow_redirects=True, timeout=timeout, headers={"User-Agent": USER_AGENT}
    ) as client:
        resp = client.get(url)
    body = resp.content
    digest = hashlib.sha256(body).hexdigest()
    dest = raw_dir / f"{digest}.html"
    existed = dest.exists()
    if not existed:
        dest.write_bytes(body)
    return Fetched(
        url=url,
        status=resp.status_code,
        body=body,
        sha256=digest,
        fetched_at=datetime.now(timezone.utc),
        from_cache=existed,
    )
