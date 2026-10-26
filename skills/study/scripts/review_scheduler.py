"""Deterministic scheduling helpers for an agent-selected Study review queue."""

## Imports
## Use only standard-library date and CSV support.
from __future__ import annotations

import csv
import io
from datetime import date, datetime, timedelta
from typing import Any


## Scheduling defaults
## Map demonstrated mastery to modest, revisable review intervals.
DEFAULT_INTERVAL_BY_MASTERY = {
    0: 1,
    1: 1,
    2: 2,
    3: 4,
    4: 7,
    5: 14,
}


## Internal scheduling support
## Resolve dates and target mastery without selecting review content.
def _parse_due_date(value: str | None) -> date | None:
    """Parse an ISO-8601 due timestamp; return its date or None when absent."""
    if not value:
        return None
    normalized_value = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized_value).date()


def _target_mastery_levels(state: dict[str, Any], item: dict[str, Any]) -> list[int]:
    """Return mastery levels for one review item's node and edge targets."""
    levels: list[int] = []
    for node_id in item.get("target_node_ids", []):
        record = state.get("mastery_by_node", {}).get(node_id)
        if record is not None:
            levels.append(int(record.get("level", 0)))
    for edge_id in item.get("target_edge_ids", []):
        record = state.get("mastery_by_edge", {}).get(edge_id)
        if record is not None:
            levels.append(int(record.get("level", 0)))
    return levels


def _default_interval(state: dict[str, Any], item: dict[str, Any]) -> int:
    """Choose a conservative interval from target mastery and misconception status."""
    misconception_id = item.get("misconception_id")
    if misconception_id:
        misconception = next(
            (
                record
                for record in state.get("known_misconceptions", [])
                if record.get("id") == misconception_id
            ),
            None,
        )
        if misconception and misconception.get("status") != "repaired":
            return 1

    levels = _target_mastery_levels(state, item)
    weakest_level = min(levels, default=2)
    return DEFAULT_INTERVAL_BY_MASTERY.get(weakest_level, 2)


## Public schedule generation
## Assign dates to an existing pedagogically chosen review queue.
def build_review_schedule(
    state: dict[str, Any], start_date: date | None = None
) -> list[dict[str, Any]]:
    """Schedule existing review items.

    Parameters:
        state: Study session state containing `review_queue` and mastery maps.
        start_date: Date from which unscheduled intervals begin; defaults to today.

    Returns:
        New schedule rows sorted by due date and review identifier. The function
        does not mutate state or decide which review prompts belong in the queue.
    """
    schedule_start = start_date or date.today()
    rows: list[dict[str, Any]] = []

    for item in state.get("review_queue", []):
        interval_days = item.get("interval_days")
        if interval_days is None:
            interval_days = _default_interval(state, item)

        due_date = _parse_due_date(item.get("due_at"))
        if due_date is None:
            due_date = schedule_start + timedelta(days=int(interval_days))

        rows.append(
            {
                "review_id": item["id"],
                "due_date": due_date.isoformat(),
                "interval_days": int(interval_days),
                "kind": item["kind"],
                "prompt": item["prompt"],
                "status": "scheduled" if item.get("status") == "queued" else item.get("status", "scheduled"),
            }
        )

    return sorted(rows, key=lambda row: (row["due_date"], row["review_id"]))


## Portable CSV serialization
## Convert review content and dates without changing learning state.
def review_schedule_to_csv(rows: list[dict[str, Any]]) -> str:
    """Serialize schedule rows as UTF-8-compatible CSV text.

    Parameters:
        rows: Output from `build_review_schedule`.

    Returns:
        CSV text with stable portable columns.
    """
    columns = ["review_id", "due_date", "interval_days", "kind", "prompt", "status"]
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def review_cards_to_csv(review_queue: list[dict[str, Any]]) -> str:
    """Serialize an agent-selected review queue as portable card CSV.

    Parameters:
        review_queue: Review-item records from Study state.

    Returns:
        CSV text retaining node, edge, misconception, criterion, and source IDs.
    """
    columns = [
        "review_id",
        "kind",
        "prompt",
        "node_ids",
        "edge_ids",
        "misconception_id",
        "success_criteria",
        "source_reference_ids",
    ]
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=columns, lineterminator="\n")
    writer.writeheader()

    for item in review_queue:
        writer.writerow(
            {
                "review_id": item["id"],
                "kind": item["kind"],
                "prompt": item["prompt"],
                "node_ids": "|".join(item.get("target_node_ids", [])),
                "edge_ids": "|".join(item.get("target_edge_ids", [])),
                "misconception_id": item.get("misconception_id") or "",
                "success_criteria": item["success_criteria"],
                "source_reference_ids": "|".join(item.get("source_reference_ids", [])),
            }
        )

    return buffer.getvalue()
