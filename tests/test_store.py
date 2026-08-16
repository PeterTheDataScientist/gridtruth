from datetime import datetime

import pytest

from gridwatch.models import Notice
from gridwatch.store import NoticeStore


def make(area: str, hour: int = 5) -> Notice:
    return Notice(
        area=area,
        area_normalised=area.lower(),
        starts_at=datetime(2026, 8, 14, hour, 0),
        ends_at=datetime(2026, 8, 14, hour + 4, 0),
        published_at=None,
        source_id="test",
        source_url="https://example.invalid",
        snapshot_sha256="x",
        raw_text=f"{area} {hour}",
    )


def test_append_is_idempotent(tmp_path):
    store = NoticeStore(tmp_path / "notices.jsonl")
    batch = [make("Avondale"), make("Borrowdale")]
    assert len(store.append_new(batch)) == 2
    assert len(store.append_new(batch)) == 0
    assert store.count() == 2


def test_only_genuinely_new_records_are_added(tmp_path):
    store = NoticeStore(tmp_path / "notices.jsonl")
    store.append_new([make("Avondale")])
    added = store.append_new([make("Avondale"), make("Avondale", hour=13)])
    assert len(added) == 1
    assert added[0].starts_at.hour == 13


def test_corrupt_line_raises_rather_than_silently_duplicating(tmp_path):
    path = tmp_path / "notices.jsonl"
    path.write_text('{"record_id": "abc"}\nnot json at all\n', encoding="utf-8")
    store = NoticeStore(path)
    with pytest.raises(ValueError, match="corrupt record"):
        store.existing_ids()


def test_count_on_missing_file_is_zero(tmp_path):
    assert NoticeStore(tmp_path / "nope.jsonl").count() == 0
