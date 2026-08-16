"""Command line entry point. Kept thin so the logic stays testable without argv."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from . import __version__
from .fetch import fetch, visible_text
from .parse import HARARE, parse_notices
from .sources import SOURCES
from .store import NoticeStore

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
NOTICES = ROOT / "data" / "processed" / "notices.jsonl"


def run_once(*, dry_run: bool = False) -> int:
    store = NoticeStore(NOTICES)
    total_new = 0
    report: list[dict] = []

    for source in SOURCES:
        entry = {"source": source.id, "url": source.url}
        try:
            got = fetch(source.url, RAW_DIR)
        except Exception as exc:
            entry |= {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
            report.append(entry)
            continue

        result = parse_notices(
            visible_text(got.body),
            source_id=source.id,
            source_url=source.url,
            snapshot_sha256=got.sha256,
            fallback_date=datetime.now(HARARE),
        )
        added = [] if dry_run else store.append_new(result.notices)
        total_new += len(added)
        entry |= {
            "ok": True,
            "http": got.status,
            "snapshot": got.sha256[:12],
            "unchanged": got.from_cache,
            "parsed": len(result.notices),
            "new": len(added),
            "unparsed_blocks": len(result.unparsed),
        }
        report.append(entry)

    print(json.dumps({"new_records": total_new, "sources": report}, indent=2))
    # A run where every source failed is an error, so the scheduler notices.
    return 0 if any(r.get("ok") for r in report) else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="gridwatch")
    ap.add_argument("--once", action="store_true", help="fetch and parse all sources once")
    ap.add_argument("--dry-run", action="store_true", help="parse but do not write")
    ap.add_argument("--show", action="store_true", help="summarise the local dataset")
    ap.add_argument("--version", action="version", version=__version__)
    args = ap.parse_args(argv)

    if args.show:
        print(json.dumps({"notices": NoticeStore(NOTICES).count()}, indent=2))
        return 0
    if args.once or args.dry_run:
        return run_once(dry_run=args.dry_run)
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
