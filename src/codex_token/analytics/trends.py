from __future__ import annotations

from collections.abc import Iterable

from ..models import TokenEvent
from .pricing import estimate_cost
from .usage import daily_usage_from_events


def build_daily_trend(
    token_events: Iterable[TokenEvent],
    pricing,
    *,
    days: int,
    now=None,
) -> dict[str, object]:
    rows = daily_usage_from_events(token_events, days=days, now=now)
    return {
        "scope": "trend",
        "days": max(days, 1),
        "rows": [
            {
                "date": row["date"],
                "usage": row["usage"],
                "cost": estimate_cost(row["usage"], pricing),
            }
            for row in rows
        ],
    }
