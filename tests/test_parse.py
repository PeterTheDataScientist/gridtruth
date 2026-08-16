from datetime import datetime
from pathlib import Path

import pytest

from gridwatch.fetch import visible_text
from gridwatch.parse import HARARE, normalise_area, parse_notices

FIXTURE = Path(__file__).parent / "fixtures" / "notice_sample.html"


@pytest.fixture
def result():
    html = FIXTURE.read_bytes()
    return parse_notices(
        visible_text(html),
        source_id="test",
        source_url="https://example.invalid/notice",
        snapshot_sha256="deadbeef",
        fallback_date=datetime(2026, 8, 14, tzinfo=HARARE),
    )


def test_finds_every_area(result):
    areas = {n.area_normalised for n in result.notices}
    assert "mount pleasant" in areas
    assert "borrowdale" in areas
    assert "bulawayo cbd" in areas
    assert len(result.notices) == 5


def test_script_content_is_not_parsed_as_a_notice(result):
    # "0100-0200" appears only inside a <script> tag and must never become a record.
    assert not any(n.starts_at.hour == 1 for n in result.notices)


def test_boilerplate_is_ignored(result):
    joined = " ".join(n.area for n in result.notices).lower()
    assert "copyright" not in joined
    assert "privacy" not in joined


def test_twelve_hour_times_convert(result):
    borrowdale = next(n for n in result.notices if n.area_normalised == "borrowdale")
    assert borrowdale.starts_at.hour == 9
    assert borrowdale.ends_at.hour == 13


def test_window_crossing_midnight_rolls_to_next_day(result):
    chitungwiza = next(n for n in result.notices if "chitungwiza" in n.area_normalised)
    assert chitungwiza.starts_at.hour == 22
    assert chitungwiza.ends_at.day == chitungwiza.starts_at.day + 1


def test_record_id_is_stable_and_content_addressed(result):
    first = parse_notices(
        visible_text(FIXTURE.read_bytes()),
        source_id="test",
        source_url="https://example.invalid/notice",
        snapshot_sha256="deadbeef",
        fallback_date=datetime(2026, 8, 14, tzinfo=HARARE),
    )
    assert [n.record_id for n in first.notices] == [n.record_id for n in result.notices]


def test_record_id_ignores_volatile_fields():
    """A re-fetch produces a different snapshot hash. That must not create a new record."""
    a = parse_notices(
        visible_text(FIXTURE.read_bytes()),
        source_id="test",
        source_url="https://example.invalid/notice",
        snapshot_sha256="aaaa",
        fallback_date=datetime(2026, 8, 14, tzinfo=HARARE),
    )
    b = parse_notices(
        visible_text(FIXTURE.read_bytes()),
        source_id="test",
        source_url="https://example.invalid/notice",
        snapshot_sha256="bbbb",
        fallback_date=datetime(2026, 8, 14, tzinfo=HARARE),
    )
    assert {n.record_id for n in a.notices} == {n.record_id for n in b.notices}


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Mt Pleasant", "mount pleasant"),
        ("MT. PLEASANT", "mount pleasant"),
        ("Mount  Pleasant ", "mount pleasant"),
        ("Msasa Park!", "msasa park"),
    ],
)
def test_area_normalisation_collapses_known_variants(raw, expected):
    assert normalise_area(raw) == expected


def test_line_with_time_but_no_date_is_reported_not_dropped():
    res = parse_notices(
        "Avondale 0600-1000",
        source_id="test",
        source_url="https://example.invalid",
        snapshot_sha256="x",
        fallback_date=None,
    )
    assert res.notices == []
    assert res.unparsed == ["Avondale 0600-1000"]


# Regression cases from the first run against the live ZETDC site, which
# produced exactly one record and it was garbage. Kept verbatim.

REAL_FAQ_LINE = (
    "In a domestic household the geyser normally contributes about 60-70% of the "
    "total bill.  The stove and heating requirements in winter normally contribute "
    "another 15-20%.  The balance is used for lighting, pumping and other uses."
)


def test_percentages_in_prose_are_not_outage_windows():
    """The live FAQ page turned '60-70%' into a 12:00 to 22:00 outage."""
    res = parse_notices(
        REAL_FAQ_LINE,
        source_id="test",
        source_url="https://example.invalid",
        snapshot_sha256="x",
        fallback_date=datetime(2026, 8, 14, tzinfo=HARARE),
    )
    assert res.notices == []


@pytest.mark.parametrize(
    "line",
    [
        "page 3-4",
        "about 60-70",
        "contributes 15-20% of the bill",
        "sections 1-2 apply",
    ],
)
def test_bare_number_ranges_are_rejected(line):
    res = parse_notices(
        line,
        source_id="test",
        source_url="https://example.invalid",
        snapshot_sha256="x",
        fallback_date=datetime(2026, 8, 14, tzinfo=HARARE),
    )
    assert res.notices == []


@pytest.mark.parametrize(
    ("line", "expected_hours"),
    [
        ("Avondale 0500-0900", (5, 9)),
        ("Avondale 05:00 - 09:00", (5, 9)),
        ("Avondale 9am to 1pm", (9, 13)),
        ("Avondale 1300 - 1700", (13, 17)),
    ],
)
def test_real_time_formats_still_parse(line, expected_hours):
    res = parse_notices(
        line,
        source_id="test",
        source_url="https://example.invalid",
        snapshot_sha256="x",
        fallback_date=datetime(2026, 8, 14, tzinfo=HARARE),
    )
    assert len(res.notices) == 1
    n = res.notices[0]
    assert (n.starts_at.hour, n.ends_at.hour) == expected_hours


@pytest.mark.parametrize("line", ["Avondale 25:00-26:00", "Avondale 09:75 - 10:80"])
def test_impossible_clock_values_are_rejected(line):
    res = parse_notices(
        line,
        source_id="test",
        source_url="https://example.invalid",
        snapshot_sha256="x",
        fallback_date=datetime(2026, 8, 14, tzinfo=HARARE),
    )
    assert res.notices == []
