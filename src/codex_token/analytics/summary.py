from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from ..models import ThreadRecord, TokenEvent
from .pricing import estimate_cost
from .projects import build_project_names
from .usage import daily_usage_from_events, usage_from_events


def build_summary(
    threads: Iterable[ThreadRecord],
    token_events: Iterable[TokenEvent],
    pricing,
    *,
    now: datetime | None = None,
) -> dict[str, object]:
    items = list(threads)
    event_items = list(token_events)
    usage = usage_from_events(event_items)
    project_count = len(build_project_names(thread.cwd for thread in items))
    trend_rows = [
        {
            "date": row["date"],
            "usage": row["usage"],
            "cost": estimate_cost(row["usage"], pricing),
        }
        for row in daily_usage_from_events(event_items, days=7, now=now)
    ]
    last_7_days_tokens = sum(int(row["usage"]["total_tokens"]) for row in trend_rows)
    last_30_days_rows = daily_usage_from_events(event_items, days=30, now=now)
    last_30_days_tokens = sum(int(row["usage"]["total_tokens"]) for row in last_30_days_rows)

    return {
        "scope": "summary",
        "sessions": len(items),
        "projects": project_count,
        "last_updated_at": max((item.updated_at for item in items), default=None),
        "tokens_last_7_days": last_7_days_tokens,
        "tokens_last_30_days": last_30_days_tokens,
        "trend_rows": trend_rows,
        "usage": usage,
        "cost": estimate_cost(usage, pricing),
    }
