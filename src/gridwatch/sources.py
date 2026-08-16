"""Registry of upstream sources.

Kept as data rather than scattered through the fetchers so that the provenance
of the dataset is one readable list, and so adding a source is a one-line change
rather than a code change.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Source:
    id: str
    name: str
    url: str
    kind: str
    """html, pdf or api. Determines which parser runs."""

    notes: str = ""


SOURCES: tuple[Source, ...] = (
    Source(
        id="zetdc-important-notices",
        name="ZETDC important notices",
        url="https://www.zetdc.co.zw/?page_id=4768",
        kind="html",
        notes="General notices page. Outage announcements appear here irregularly.",
    ),
    Source(
        id="zetdc-stakeholder-notices",
        name="ZETDC stakeholder notices",
        url="https://www.zetdc.co.zw/?page_id=4763",
        kind="html",
        notes="Stakeholder-facing notices, often PDFs linked from the page body.",
    ),
    Source(
        id="zetdc-loadshedding-faq",
        name="ZETDC load shedding FAQs",
        url="https://www.zetdc.co.zw/?page_id=7328",
        kind="html",
        notes="Not a schedule. Watched because stage definitions change here first.",
    ),
)


def by_id(source_id: str) -> Source:
    for s in SOURCES:
        if s.id == source_id:
            return s
    raise KeyError(f"unknown source: {source_id}")
