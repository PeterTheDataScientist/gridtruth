"""Command line entry point. Kept thin so the logic stays testable without argv."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .fetch import fetch, visible_text
from .models import RunRecord
from .parse import HARARE, parse_notices
from .sources import SOURCES
from .store import NoticeStore, RunStore

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
NOTICES = ROOT / "data" / "processed" / "notices.jsonl"
RUNS = ROOT / "data" / "processed" / "runs.jsonl"


def run_once(*, dry_run: bool = False) -> int:
    notices = NoticeStore(NOTICES)
    runs = RunStore(RUNS)
    checked_at = datetime.now(timezone.utc)
    records: list[RunRecord] = []

    for source in SOURCES:
        try:
            got = fetch(source.url, RAW_DIR)
        except Exception as exc:
            records.append(
                RunRecord(
                    checked_at=checked_at,
                    source_id=source.id,
                    url=source.url,
                    ok=False,
                    http_status=None,
                    snapshot_sha256=None,
                    content_changed=False,
                    notices_parsed=0,
                    notices_new=0,
                    unparsed_blocks=0,
                    error=f"{type(exc).__name__}: {exc}",
                )
            )
            continue

        result = parse_notices(
            visible_text(got.body),
            source_id=source.id,
            source_url=source.url,
            snapshot_sha256=got.sha256,
            fallback_date=datetime.now(HARARE),
        )
        added = [] if dry_run else notices.append_new(result.notices)
        records.append(
            RunRecord(
                checked_at=checked_at,
                source_id=source.id,
                url=source.url,
                ok=True,
                http_status=got.status,
                snapshot_sha256=got.sha256,
                content_changed=not got.from_cache,
                notices_parsed=len(result.notices),
                notices_new=len(added),
                unparsed_blocks=len(result.unparsed),
            )
        )

    if not dry_run:
        runs.append(records)

    print(
        json.dumps(
            {
                "checked_at": checked_at.isoformat(),
                "new_records": sum(r.notices_new for r in records),
                "sources": [json.loads(r.to_json()) for r in records],
            },
            indent=2,
        )
    )
    # A run where every source failed is an error, so the scheduler notices.
    return 0 if any(r.ok for r in records) else 1


def summary() -> dict:
    """Numbers the public dashboard reports. Kept here so the page and the CLI
    can never disagree about what the dataset says."""
    runs_seen = RunStore(RUNS).count()
    notice_count = NoticeStore(NOTICES).count()
    first_check = last_check = None
    if RUNS.exists():
        with RUNS.open(encoding="utf-8") as fh:
            stamps = [json.loads(ln)["checked_at"] for ln in fh if ln.strip()]
        if stamps:
            first_check, last_check = min(stamps), max(stamps)
    return {
        "notices": notice_count,
        "observations": runs_seen,
        "sources_watched": len(SOURCES),
        "first_check": first_check,
        "last_check": last_check,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="gridwatch")
    ap.add_argument("--once", action="store_true", help="fetch and parse all sources once")
    ap.add_argument("--dry-run", action="store_true", help="parse but do not write")
    ap.add_argument("--show", action="store_true", help="summarise the local dataset")
    ap.add_argument("--version", action="version", version=__version__)
    args = ap.parse_args(argv)

    if args.show:
        print(json.dumps(summary(), indent=2))
        return 0
    if args.once or args.dry_run:
        return run_once(dry_run=args.dry_run)
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
