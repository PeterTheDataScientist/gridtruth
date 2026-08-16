"""Append-only JSONL store.

The dataset lives in git rather than a database. That means the store has to be
idempotent (re-running ingestion must not duplicate rows) and order-stable (so a
diff shows only genuinely new records, not a reshuffle).
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

from .models import Notice, RunRecord


class NoticeStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def existing_ids(self) -> set[str]:
        if not self.path.exists():
            return set()
        ids: set[str] = set()
        with self.path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    ids.add(json.loads(line)["record_id"])
                except (json.JSONDecodeError, KeyError):
                    # A corrupt line must not silently drop the dedup set, which
                    # would cause every subsequent record to be re-appended.
                    raise ValueError(
                        f"corrupt record in {self.path}: {line[:120]!r}"
                    ) from None
        return ids

    def append_new(self, notices: Iterable[Notice]) -> list[Notice]:
        """Append only records not already present. Returns what was actually added."""
        seen = self.existing_ids()
        added: list[Notice] = []
        with self.path.open("a", encoding="utf-8") as fh:
            for n in notices:
                if n.record_id in seen:
                    continue
                fh.write(n.to_json() + "\n")
                seen.add(n.record_id)
                added.append(n)
        return added

    def count(self) -> int:
        if not self.path.exists():
            return 0
        with self.path.open(encoding="utf-8") as fh:
            return sum(1 for line in fh if line.strip())


class RunStore:
    """Append-only log of monitoring runs. No dedup: every check is a distinct
    observation, and the gaps between them are as informative as the records."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, runs: Iterable[RunRecord]) -> int:
        n = 0
        with self.path.open("a", encoding="utf-8") as fh:
            for r in runs:
                fh.write(r.to_json() + "\n")
                n += 1
        return n

    def count(self) -> int:
        if not self.path.exists():
            return 0
        with self.path.open(encoding="utf-8") as fh:
            return sum(1 for line in fh if line.strip())
