from datetime import datetime
from pathlib import Path

import pytest

from gridwatch.fetch import visible_text
from gridwatch.parse import normalise_area, parse_notices

FIXTURE = Path(__file__).parent / "fixtures" / "notice_sample.html"


@pytest.fixture
def result():
    html = FIXTURE.read_bytes()
    return parse_notices(
        visible_text(html),
        source_id="test",
        source_url="https://example.invalid/notice",
        snapshot_sha256="deadbeef",
        fallback_date=datetime(2026, 8, 14),
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
        fallback_date=datetime(2026, 8, 14),
    )
    assert [n.record_id for n in first.notices] == [n.record_id for n in result.notices]


def test_record_id_ignores_volatile_fields():
    """A re-fetch produces a different snapshot hash. That must not create a new record."""
    a = parse_notices(
        visible_text(FIXTURE.read_bytes()),
        source_id="test",
        source_url="https://example.invalid/notice",
        snapshot_sha256="aaaa",
        fallback_date=datetime(2026, 8, 14),
    )
    b = parse_notices(
        visible_text(FIXTURE.read_bytes()),
        source_id="test",
        source_url="https://example.invalid/notice",
        snapshot_sha256="bbbb",
        fallback_date=datetime(2026, 8, 14),
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
