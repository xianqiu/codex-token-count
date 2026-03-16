from __future__ import annotations

from datetime import datetime, timezone
import unittest

from codex_token_count.analytics import (
    build_daily_trend,
    build_summary,
    summarize_projects,
    top_sessions,
    usage_from_events,
    usage_from_session_events,
)
from codex_token_count.models import ThreadRecord, TokenEvent


def ts(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(timezone.utc)


def make_threads() -> list[ThreadRecord]:
    return [
        ThreadRecord(
            session_id="s1",
            title="one",
            cwd="/repo/a",
            model_provider="openai",
            created_at=ts("2026-03-10T00:00:00+00:00"),
            updated_at=ts("2026-03-10T12:00:00+00:00"),
            tokens_used=100,
        ),
        ThreadRecord(
            session_id="s2",
            title="two",
            cwd="/repo/a",
            model_provider="openai",
            created_at=ts("2026-03-11T00:00:00+00:00"),
            updated_at=ts("2026-03-12T12:00:00+00:00"),
            tokens_used=250,
        ),
        ThreadRecord(
            session_id="s3",
            title="three",
            cwd="/repo/b",
            model_provider="openai",
            created_at=ts("2026-03-09T00:00:00+00:00"),
            updated_at=ts("2026-03-14T12:00:00+00:00"),
            tokens_used=400,
        ),
    ]


class AnalyticsTests(unittest.TestCase):
    def test_build_summary(self) -> None:
        events = [
            TokenEvent("s1", ts("2026-03-10T10:00:00+00:00"), 80, 10, 20, 5, 100),
            TokenEvent("s2", ts("2026-03-12T10:00:00+00:00"), 200, 50, 50, 0, 250),
        ]
        summary = build_summary(make_threads(), token_events=events, days=2, now=ts("2026-03-15T00:00:00+00:00"))
        self.assertEqual(summary["total_sessions"], 3)
        self.assertEqual(summary["total_tokens"], 750)
        self.assertEqual(summary["window_days"], 2)
        self.assertEqual(summary["tokens_in_window"], 400)
        self.assertEqual(summary["tokens_last_7_days"], 750)
        self.assertEqual(summary["tokens_last_30_days"], 750)
        self.assertEqual(summary["input_tokens"], 280)
        self.assertEqual(summary["cached_input_tokens"], 60)
        self.assertEqual(summary["output_tokens"], 70)
        self.assertEqual(summary["reasoning_output_tokens"], 5)

    def test_top_sessions(self) -> None:
        top = top_sessions(make_threads(), limit=2)
        self.assertEqual([item.session_id for item in top], ["s3", "s2"])

    def test_summarize_projects(self) -> None:
        rows = summarize_projects(make_threads())
        self.assertEqual(rows[0]["cwd"], "/repo/b")
        self.assertEqual(rows[0]["sessions"], 1)
        self.assertEqual(rows[0]["tokens_used"], 400)
        self.assertEqual(rows[1]["cwd"], "/repo/a")

    def test_build_daily_trend_from_events(self) -> None:
        events = [
            TokenEvent("s1", ts("2026-03-13T10:00:00+00:00"), 10, 0, 2, 0, 12),
            TokenEvent("s1", ts("2026-03-14T10:00:00+00:00"), 15, 0, 3, 0, 18),
            TokenEvent("s2", ts("2026-03-14T12:00:00+00:00"), 20, 0, 5, 0, 25),
        ]
        rows = build_daily_trend(
            make_threads(),
            events,
            days=3,
            now=ts("2026-03-15T00:00:00+00:00"),
        )
        self.assertEqual(
            rows,
            [
                {"date": "2026-03-13", "tokens": 12},
                {"date": "2026-03-14", "tokens": 31},
                {"date": "2026-03-15", "tokens": 0},
            ],
        )

    def test_usage_helpers(self) -> None:
        events = [
            TokenEvent("s1", ts("2026-03-13T10:00:00+00:00"), 10, 1, 2, 0, 12),
            TokenEvent("s1", ts("2026-03-14T10:00:00+00:00"), 20, 2, 3, 1, 24),
            TokenEvent("s2", ts("2026-03-14T10:00:00+00:00"), 40, 4, 5, 0, 45),
        ]
        total = usage_from_events(events)
        self.assertEqual(total["input_tokens"], 60)
        self.assertEqual(total["cached_input_tokens"], 6)
        self.assertEqual(total["output_tokens"], 8)
        self.assertEqual(total["reasoning_output_tokens"], 1)
        self.assertEqual(total["total_tokens"], 69)

        session = usage_from_session_events(events[:2])
        self.assertEqual(session["input_tokens"], 20)
        self.assertEqual(session["cached_input_tokens"], 2)
        self.assertEqual(session["output_tokens"], 3)
        self.assertEqual(session["reasoning_output_tokens"], 1)
        self.assertEqual(session["total_tokens"], 24)


if __name__ == "__main__":
    unittest.main()
