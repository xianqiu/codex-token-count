from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timedelta, timezone

from ..models import ThreadRecord, TokenEvent
from .usage import usage_from_events


def build_summary(
    threads: Iterable[ThreadRecord],
    token_events: Iterable[TokenEvent] | None = None,
    days: int = 7,
    now: datetime | None = None,
) -> dict[str, object]:
    items = list(threads)
    current = now or datetime.now(timezone.utc)
    custom_start = current - timedelta(days=max(days, 1))
    last_7_start = current - timedelta(days=7)
    last_30_start = current - timedelta(days=30)
    usage = usage_from_events(token_events or [])

    return {
        "total_sessions": len(items),
        "total_tokens": sum(item.tokens_used for item in items),
        "last_updated_at": max((item.updated_at for item in items), default=None),
        "window_days": max(days, 1),
        "tokens_in_window": sum(item.tokens_used for item in items if item.updated_at >= custom_start),
        "tokens_last_7_days": sum(item.tokens_used for item in items if item.updated_at >= last_7_start),
        "tokens_last_30_days": sum(item.tokens_used for item in items if item.updated_at >= last_30_start),
        "input_tokens": usage["input_tokens"],
        "cached_input_tokens": usage["cached_input_tokens"],
        "output_tokens": usage["output_tokens"],
        "reasoning_output_tokens": usage["reasoning_output_tokens"],
    }
