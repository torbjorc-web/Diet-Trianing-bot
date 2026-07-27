import csv
import io
from datetime import UTC, datetime, timedelta

import pytest

from chatbot.admin_reporting import filter_records_by_window, records_to_csv


def record(created_at: datetime | str, user_id: str = "alice") -> dict:
    if isinstance(created_at, datetime):
        created_at = created_at.strftime("%Y-%m-%d %H:%M:%S")
    return {
        "user_id": user_id,
        "prompt": "meal plan",
        "response": "Meal plan: ...",
        "success": True,
        "created_at": created_at,
    }


@pytest.fixture
def records() -> list[dict]:
    now = datetime.now(UTC).replace(tzinfo=None)
    return [
        record(now - timedelta(seconds=1), "just_now"),
        record(now - timedelta(days=3), "three_days"),
        record(now - timedelta(days=10), "ten_days"),
        record(now - timedelta(days=100), "hundred_days"),
    ]


def ids(filtered: list[dict]) -> list[str]:
    return [item["user_id"] for item in filtered]


def test_window_all_returns_everything(records):
    assert filter_records_by_window(records, "all") == records


def test_window_today_keeps_only_current_utc_day(records):
    assert ids(filter_records_by_window(records, "today")) == ["just_now"]


def test_window_7d_keeps_last_week(records):
    assert ids(filter_records_by_window(records, "7d")) == ["just_now", "three_days"]


def test_window_30d_keeps_last_month(records):
    assert ids(filter_records_by_window(records, "30d")) == [
        "just_now",
        "three_days",
        "ten_days",
    ]


@pytest.mark.parametrize("window", ["", "  ", "unknown"])
def test_unknown_window_falls_back_to_7d(records, window):
    assert ids(filter_records_by_window(records, window)) == ["just_now", "three_days"]


def test_window_matching_is_case_insensitive(records):
    assert filter_records_by_window(records, "ALL") == records


def test_records_with_unparsable_timestamps_are_dropped():
    assert filter_records_by_window([record("not-a-date")], "all") != []
    assert filter_records_by_window([record("not-a-date")], "7d") == []


def test_records_without_timestamp_are_dropped():
    assert filter_records_by_window([record("")], "30d") == []


def test_csv_has_header_and_one_row_per_record():
    rows = list(csv.reader(io.StringIO(records_to_csv([record("2026-01-01 10:00:00")]))))

    assert rows[0] == ["created_at", "user_id", "success", "prompt", "response"]
    assert rows[1] == ["2026-01-01 10:00:00", "alice", "True", "meal plan", "Meal plan: ..."]


def test_csv_for_empty_records_is_header_only():
    rows = [row for row in csv.reader(io.StringIO(records_to_csv([]))) if row]
    assert len(rows) == 1


def test_csv_escapes_delimiters_and_newlines():
    messy = record("2026-01-01 10:00:00")
    messy["prompt"] = 'meal, plan\nwith "quotes"'

    parsed = list(csv.reader(io.StringIO(records_to_csv([messy]))))

    assert parsed[1][3] == 'meal, plan\nwith "quotes"'


def test_csv_tolerates_missing_keys():
    parsed = list(csv.reader(io.StringIO(records_to_csv([{}]))))
    assert parsed[1] == ["", "", "", "", ""]
