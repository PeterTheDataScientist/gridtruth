"""Turn a fetched page into Notice records.

Design note. Zimbabwean utility notices are written for humans and the format
changes without warning, so this parser is built to fail loudly and partially
rather than quietly and completely. Every block it cannot interpret is returned
in `unparsed` so a run that silently produces zero notices is distinguishable
from a run where the page genuinely had none.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timedelta

from dateutil import parser as dateparser

from .models import Notice

# Time ranges as they actually appear: "0500-0900", "05:00 - 09:00", "5am to 9am".
_TIME_RANGE = re.compile(
    r"(?P<h1>\d{1,2})[:.]?(?P<m1>\d{2})?\s*(?P<ap1>am|pm)?\s*(?:-|to|–|until)\s*"
    r"(?P<h2>\d{1,2})[:.]?(?P<m2>\d{2})?\s*(?P<ap2>am|pm)?",
    re.IGNORECASE,
)

# A date somewhere in the line. Deliberately permissive; validated after parsing.
_DATE_HINT = re.compile(
    r"\b(\d{1,2}\s+\w+\s+\d{4}|\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4})\b"
)

_NOISE = re.compile(r"\b(cookie|privacy|copyright|all rights reserved|menu|search)\b", re.I)


def normalise_area(name: str) -> str:
    """Join key for an area name.

    Utilities spell the same suburb several ways across notices ("Mt Pleasant",
    "Mount Pleasant", "MT. PLEASANT"). This collapses the easy cases. It does not
    attempt fuzzy matching, because a wrong join is worse than a missed one and
    the unresolved names are reported rather than guessed.
    """
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    s = s.lower().strip()
    s = re.sub(r"^(mt|mount)\.?\s+", "mount ", s)
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _plausible_area(text: str) -> bool:
    """Is this text plausibly an area name rather than a fragment or boilerplate?

    Deliberately conservative. A false negative costs one missed notice, which is
    visible in `unparsed`. A false positive puts garbage into the public dataset,
    which is much worse and much harder to notice.
    """
    if not (3 <= len(text) <= 80):
        return False
    if _NOISE.search(text):
        return False
    letters = sum(ch.isalpha() for ch in text)
    return letters >= 3 and letters / len(text) > 0.5


@dataclass(slots=True)
class ParseResult:
    notices: list[Notice]
    unparsed: list[str]
    """Blocks that looked like they might be notices but could not be read."""


def _to_time(h: str, m: str | None, ap: str | None) -> tuple[int, int]:
    hour = int(h)
    minute = int(m) if m else 0
    if ap:
        ap = ap.lower()
        if ap == "pm" and hour != 12:
            hour += 12
        if ap == "am" and hour == 12:
            hour = 0
    return hour % 24, minute


def parse_notices(
    text: str,
    *,
    source_id: str,
    source_url: str,
    snapshot_sha256: str,
    fallback_date: datetime | None = None,
) -> ParseResult:
    """Extract Notice records from the visible text of a page.

    `fallback_date` is used when a line gives a time range but no date, which is
    common in notices that carry one date in a heading and times in a table below.
    """
    notices: list[Notice] = []
    unparsed: list[str] = []
    current_date = fallback_date
    pending_area: str | None = None

    for line in (ln.strip() for ln in text.splitlines()):
        if not line or _NOISE.search(line):
            continue

        date_match = _DATE_HINT.search(line)
        if date_match:
            try:
                current_date = dateparser.parse(date_match.group(1), dayfirst=True)
            except (ValueError, OverflowError):
                pass

        time_match = _TIME_RANGE.search(line)
        if not time_match:
            # Text with no time range. Almost always the area name from the cell
            # before the time cell, because HTML tables flatten to one cell per
            # line. Held as a candidate for the next line that does carry a time.
            candidate = _DATE_HINT.sub("", line).strip(" -–:\t|")
            pending_area = candidate if _plausible_area(candidate) else None
            continue

        if current_date is None:
            unparsed.append(line)
            pending_area = None
            continue

        area = _TIME_RANGE.sub("", line)
        area = _DATE_HINT.sub("", area).strip(" -–:\t|")
        if not _plausible_area(area):
            # Time range on its own line. Pair it with the area seen just before.
            if pending_area is None:
                unparsed.append(line)
                continue
            area = pending_area
        pending_area = None

        h1, m1 = _to_time(time_match["h1"], time_match["m1"], time_match["ap1"])
        h2, m2 = _to_time(time_match["h2"], time_match["m2"], time_match["ap2"])

        starts = current_date.replace(hour=h1, minute=m1, second=0, microsecond=0)
        ends = current_date.replace(hour=h2, minute=m2, second=0, microsecond=0)
        if ends <= starts:
            # Window crosses midnight. Common for overnight shedding.
            ends += timedelta(days=1)

        notices.append(
            Notice(
                area=area,
                area_normalised=normalise_area(area),
                starts_at=starts,
                ends_at=ends,
                published_at=None,
                source_id=source_id,
                source_url=source_url,
                snapshot_sha256=snapshot_sha256,
                raw_text=line,
            )
        )

    return ParseResult(notices=notices, unparsed=unparsed)
