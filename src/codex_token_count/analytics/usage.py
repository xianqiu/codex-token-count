from __future__ import annotations

from collections.abc import Iterable

from ..models import TokenEvent


def usage_from_events(events: Iterable[TokenEvent]) -> dict[str, int]:
    latest_by_session: dict[str, TokenEvent] = {}
    for event in events:
        latest = latest_by_session.get(event.session_id)
        if latest is None or event.timestamp >= latest.timestamp:
            latest_by_session[event.session_id] = event

    totals = {
        "input_tokens": 0,
        "cached_input_tokens": 0,
        "output_tokens": 0,
        "reasoning_output_tokens": 0,
        "total_tokens": 0,
    }
    for event in latest_by_session.values():
        totals["input_tokens"] += event.input_tokens
        totals["cached_input_tokens"] += event.cached_input_tokens
        totals["output_tokens"] += event.output_tokens
        totals["reasoning_output_tokens"] += event.reasoning_output_tokens
        totals["total_tokens"] += event.total_tokens
    return totals


def usage_from_session_events(events: Iterable[TokenEvent]) -> dict[str, int]:
    latest: TokenEvent | None = None
    for event in events:
        if latest is None or event.timestamp >= latest.timestamp:
            latest = event

    if latest is None:
        return {
            "input_tokens": 0,
            "cached_input_tokens": 0,
            "output_tokens": 0,
            "reasoning_output_tokens": 0,
            "total_tokens": 0,
        }

    return {
        "input_tokens": latest.input_tokens,
        "cached_input_tokens": latest.cached_input_tokens,
        "output_tokens": latest.output_tokens,
        "reasoning_output_tokens": latest.reasoning_output_tokens,
        "total_tokens": latest.total_tokens,
    }
