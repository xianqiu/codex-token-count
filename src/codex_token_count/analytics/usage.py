from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime, timedelta, timezone

from ..models import TokenEvent


def empty_usage() -> dict[str, int]:
    return {
        "total_tokens": 0,
        "input_tokens": 0,
        "cached_input_tokens": 0,
        "non_cached_input_tokens": 0,
        "output_tokens": 0,
        "reasoning_output_tokens": 0,
        "non_reasoning_output_tokens": 0,
    }


def usage_from_events(events: Iterable[TokenEvent]) -> dict[str, int]:
    latest_by_session: dict[str, TokenEvent] = {}
    for event in events:
        latest = latest_by_session.get(event.session_id)
        if latest is None or event.timestamp >= latest.timestamp:
            latest_by_session[event.session_id] = event

    totals = empty_usage()
    for event in latest_by_session.values():
        totals["input_tokens"] += event.input_tokens
        totals["cached_input_tokens"] += event.cached_input_tokens
        totals["output_tokens"] += event.output_tokens
        totals["reasoning_output_tokens"] += event.reasoning_output_tokens
        totals["total_tokens"] += event.total_tokens
    totals["non_cached_input_tokens"] = max(totals["input_tokens"] - totals["cached_input_tokens"], 0)
    totals["non_reasoning_output_tokens"] = max(totals["output_tokens"] - totals["reasoning_output_tokens"], 0)
    return totals


def usage_from_session_events(events: Iterable[TokenEvent]) -> dict[str, int]:
    return usage_from_events(events)


def daily_usage_from_events(
    events: Iterable[TokenEvent],
    days: int,
    now: datetime | None = None,
) -> list[dict[str, object]]:
    current = now or datetime.now(timezone.utc)
    window_days = max(days, 1)
    start_day = (current - timedelta(days=window_days - 1)).date()
    rows_by_day: dict[date, dict[str, int]] = {
        start_day + timedelta(days=offset): empty_usage() for offset in range(window_days)
    }

    previous_by_session: dict[str, TokenEvent] = {}
    for event in sorted(events, key=lambda item: (item.timestamp, item.session_id)):
        previous = previous_by_session.get(event.session_id)
        if previous is None:
            delta_input = event.input_tokens
            delta_cached = event.cached_input_tokens
            delta_output = event.output_tokens
            delta_reasoning = event.reasoning_output_tokens
            delta_total = event.total_tokens
        else:
            delta_input = max(event.input_tokens - previous.input_tokens, 0)
            delta_cached = max(event.cached_input_tokens - previous.cached_input_tokens, 0)
            delta_output = max(event.output_tokens - previous.output_tokens, 0)
            delta_reasoning = max(event.reasoning_output_tokens - previous.reasoning_output_tokens, 0)
            delta_total = max(event.total_tokens - previous.total_tokens, 0)

        event_day = event.timestamp.date()
        if event_day in rows_by_day:
            usage = rows_by_day[event_day]
            usage["input_tokens"] += delta_input
            usage["cached_input_tokens"] += delta_cached
            usage["output_tokens"] += delta_output
            usage["reasoning_output_tokens"] += delta_reasoning
            usage["total_tokens"] += delta_total
        previous_by_session[event.session_id] = event

    rows: list[dict[str, object]] = []
    for current_day in sorted(rows_by_day):
        usage = rows_by_day[current_day]
        usage["non_cached_input_tokens"] = max(usage["input_tokens"] - usage["cached_input_tokens"], 0)
        usage["non_reasoning_output_tokens"] = max(usage["output_tokens"] - usage["reasoning_output_tokens"], 0)
        rows.append({"date": current_day.isoformat(), "usage": usage})
    return rows
