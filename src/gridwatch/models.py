"""Record schemas for the public dataset.

Every record written to data/processed/ is one of these, serialised as a single
JSON object on one line. The schema is deliberately flat and boring: this file
is the contract that anyone reusing the dataset depends on, so changes to it are
breaking changes and get a version bump plus a note in data/SOURCES.md.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Any

SCHEMA_VERSION = 1


def _canonical(payload: dict[str, Any]) -> str:
    """Stable JSON for hashing. Sorted keys, no whitespace, no volatile fields."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


@dataclass(slots=True)
class Notice:
    """One announced outage for one area over one time window.

    A single published notice usually expands into many Notice records, one per
    area named in it. That is intentional: the area is the unit everything else
    joins on.
    """

    area: str
    """Suburb, feeder or group name exactly as published, not normalised."""

    area_normalised: str
    """Lowercased, punctuation-stripped form used for joining. Never displayed."""

    starts_at: datetime
    ends_at: datetime
    published_at: datetime | None
    source_id: str
    """Which entry in sources.py produced this."""

    source_url: str
    snapshot_sha256: str
    """Points at the raw bytes in data/raw/ that this was parsed from."""

    raw_text: str
    """The fragment of the notice this record came from. Kept so a parser bug is
    auditable after the fact rather than silently losing information."""

    schema_version: int = SCHEMA_VERSION
    record_id: str = field(default="", init=False)

    def __post_init__(self) -> None:
        self.record_id = self.compute_id()

    def compute_id(self) -> str:
        """Content address. Two runs that see the same notice produce the same id,
        so re-running ingestion is idempotent and the store can dedup without state."""
        return hashlib.sha256(
            _canonical(
                {
                    "area": self.area_normalised,
                    "starts_at": self.starts_at.isoformat(),
                    "ends_at": self.ends_at.isoformat(),
                    "source_id": self.source_id,
                }
            ).encode()
        ).hexdigest()[:16]

    def to_json(self) -> str:
        d = asdict(self)
        d["record_id"] = self.record_id
        return json.dumps(d, sort_keys=True, default=str)


@dataclass(slots=True)
class Observation:
    """One night-light radiance observation for one area on one night.

    Deliberately stores the raw radiance and the quality flag rather than a verdict.
    Verdicts are derived downstream and can be recomputed when the method changes;
    the observation cannot be recovered if it was thrown away.
    """

    area_normalised: str
    night: date
    radiance: float | None
    """VNP46A2 gap-filled DNB BRDF-corrected radiance, nW/cm2/sr. None if masked."""

    quality: int
    """Mandatory quality flag from the product. Non-zero means do not trust radiance."""

    cloud_fraction: float | None
    baseline: float | None
    """The un-shed reference for this area, computed per the method in DESIGN.md."""

    baseline_method: str
    product: str = "VNP46A2"
    schema_version: int = SCHEMA_VERSION

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, default=str)
