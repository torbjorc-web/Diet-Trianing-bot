import csv
import io
from datetime import datetime, timedelta, timezone


def filter_records_by_window(records: list[dict], window: str) -> list[dict]:
    normalized = (window or "7d").strip().lower()
    if normalized == "all":
        return records

    now = datetime.now(timezone.utc)
    if normalized == "today":
        cutoff = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    elif normalized == "30d":
        cutoff = now - timedelta(days=30)
    else:
        cutoff = now - timedelta(days=7)

    filtered: list[dict] = []
    for record in records:
        created_at = str(record.get("created_at", "")).strip()
        if not created_at:
            continue
        try:
            timestamp = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S").replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            continue
        if timestamp >= cutoff:
            filtered.append(record)
    return filtered


def records_to_csv(records: list[dict]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["created_at", "user_id", "success", "prompt", "response"])
    for row in records:
        writer.writerow(
            [
                row.get("created_at", ""),
                row.get("user_id", ""),
                row.get("success", ""),
                row.get("prompt", ""),
                row.get("response", ""),
            ]
        )
    return output.getvalue()
