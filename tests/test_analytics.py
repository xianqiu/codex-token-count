from __future__ import annotations

from datetime import datetime, timezone
import unittest

from codex_token_count.analytics import (
    build_daily_trend,
    build_project_detail,
    build_project_list,
    build_project_names,
    build_summary,
    estimate_cost,
    usage_from_events,
    usage_from_session_events,
)
from codex_token_count.config import PricingConfig
from codex_token_count.models import ThreadRecord, TokenEvent


def ts(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(timezone.utc)


def make_threads() -> list[ThreadRecord]:
    return [
        ThreadRecord(
            session_id="s1",
            title="one",
            cwd="/repo/foo/api",
            model_provider="openai",
            created_at=ts("2026-03-10T00:00:00+00:00"),
            updated_at=ts("2026-03-10T12:00:00+00:00"),
            tokens_used=100,
        ),
        ThreadRecord(
            session_id="s2",
            title="two",
            cwd="/repo/foo/api",
            model_provider="openai",
            created_at=ts("2026-03-11T00:00:00+00:00"),
            updated_at=ts("2026-03-12T12:00:00+00:00"),
            tokens_used=250,
        ),
        ThreadRecord(
            session_id="s3",
            title="three",
            cwd="/repo/bar/api",
            model_provider="openai",
            created_at=ts("2026-03-09T00:00:00+00:00"),
            updated_at=ts("2026-03-14T12:00:00+00:00"),
            tokens_used=400,
        ),
    ]


def make_events() -> list[TokenEvent]:
    return [
        TokenEvent("s1", ts("2026-03-13T10:00:00+00:00"), 10, 2, 2, 1, 12),
        TokenEvent("s1", ts("2026-03-14T10:00:00+00:00"), 20, 4, 3, 1, 23),
        TokenEvent("s2", ts("2026-03-14T12:00:00+00:00"), 40, 10, 5, 0, 45),
        TokenEvent("s3", ts("2026-03-15T12:00:00+00:00"), 30, 0, 10, 2, 40),
    ]


class AnalyticsTests(unittest.TestCase):
    def test_usage_from_events_includes_derived_breakdown(self) -> None:
        total = usage_from_events(make_events())
        self.assertEqual(total["input_tokens"], 90)
        self.assertEqual(total["cached_input_tokens"], 14)
        self.assertEqual(total["non_cached_input_tokens"], 76)
        self.assertEqual(total["output_tokens"], 18)
        self.assertEqual(total["reasoning_output_tokens"], 3)
        self.assertEqual(total["non_reasoning_output_tokens"], 15)
        self.assertEqual(total["total_tokens"], 108)

    def test_estimate_cost_rounds_to_two_decimals(self) -> None:
        cost = estimate_cost(
            {
                "total_tokens": 0,
                "input_tokens": 0,
                "cached_input_tokens": 100_000,
                "non_cached_input_tokens": 400_000,
                "output_tokens": 500_000,
                "reasoning_output_tokens": 0,
                "non_reasoning_output_tokens": 500_000,
            },
            PricingConfig(2.5, 0.25, 15.0),
        )
        self.assertEqual(cost["input_cost_usd"], 1.0)
        self.assertEqual(cost["cached_input_cost_usd"], 0.03)
        self.assertEqual(cost["output_cost_usd"], 7.5)
        self.assertEqual(cost["total_cost_usd"], 8.53)

    def test_build_summary(self) -> None:
        summary = build_summary(make_threads(), make_events(), PricingConfig(2.5, 0.25, 15.0))
        self.assertEqual(summary["scope"], "summary")
        self.assertEqual(summary["sessions"], 3)
        self.assertEqual(summary["projects"], 2)
        self.assertEqual(summary["usage"]["total_tokens"], 108)
        self.assertEqual(summary["cost"]["total_cost_usd"], 0.0)

    def test_build_daily_trend(self) -> None:
        trend = build_daily_trend(
            make_events(),
            PricingConfig(2.5, 0.25, 15.0),
            days=3,
            now=ts("2026-03-15T23:00:00+00:00"),
        )
        self.assertEqual(trend["scope"], "trend")
        self.assertEqual(
            trend["rows"],
            [
                {
                    "date": "2026-03-13",
                    "usage": {
                        "total_tokens": 12,
                        "input_tokens": 10,
                        "cached_input_tokens": 2,
                        "non_cached_input_tokens": 8,
                        "output_tokens": 2,
                        "reasoning_output_tokens": 1,
                        "non_reasoning_output_tokens": 1,
                    },
                    "cost": {
                        "currency": "USD",
                        "input_cost_usd": 0.0,
                        "cached_input_cost_usd": 0.0,
                        "output_cost_usd": 0.0,
                        "total_cost_usd": 0.0,
                        "pricing": {
                            "input_per_million_usd": 2.5,
                            "cached_input_per_million_usd": 0.25,
                            "output_per_million_usd": 15.0,
                        },
                    },
                },
                {
                    "date": "2026-03-14",
                    "usage": {
                        "total_tokens": 56,
                        "input_tokens": 50,
                        "cached_input_tokens": 12,
                        "non_cached_input_tokens": 38,
                        "output_tokens": 6,
                        "reasoning_output_tokens": 0,
                        "non_reasoning_output_tokens": 6,
                    },
                    "cost": {
                        "currency": "USD",
                        "input_cost_usd": 0.0,
                        "cached_input_cost_usd": 0.0,
                        "output_cost_usd": 0.0,
                        "total_cost_usd": 0.0,
                        "pricing": {
                            "input_per_million_usd": 2.5,
                            "cached_input_per_million_usd": 0.25,
                            "output_per_million_usd": 15.0,
                        },
                    },
                },
                {
                    "date": "2026-03-15",
                    "usage": {
                        "total_tokens": 40,
                        "input_tokens": 30,
                        "cached_input_tokens": 0,
                        "non_cached_input_tokens": 30,
                        "output_tokens": 10,
                        "reasoning_output_tokens": 2,
                        "non_reasoning_output_tokens": 8,
                    },
                    "cost": {
                        "currency": "USD",
                        "input_cost_usd": 0.0,
                        "cached_input_cost_usd": 0.0,
                        "output_cost_usd": 0.0,
                        "total_cost_usd": 0.0,
                        "pricing": {
                            "input_per_million_usd": 2.5,
                            "cached_input_per_million_usd": 0.25,
                            "output_per_million_usd": 15.0,
                        },
                    },
                },
            ],
        )

    def test_build_project_names_generates_unique_suffixes(self) -> None:
        names = build_project_names(["/repo/foo/api", "/repo/bar/api"])
        self.assertEqual(names["/repo/foo/api"], "foo/api")
        self.assertEqual(names["/repo/bar/api"], "bar/api")

    def test_build_project_list_and_detail(self) -> None:
        pricing = PricingConfig(2.5, 0.25, 15.0)
        rows = build_project_list(make_threads(), make_events(), pricing, limit=3)
        self.assertEqual(rows[0]["project_id"], "/repo/foo/api")
        self.assertEqual(rows[0]["project_name"], "foo/api")
        self.assertEqual(rows[0]["usage"]["total_tokens"], 68)
        self.assertEqual(rows[1]["project_id"], "/repo/bar/api")
        self.assertEqual(rows[1]["project_name"], "bar/api")
        self.assertEqual(rows[1]["usage"]["total_tokens"], 40)

        detail = build_project_detail(make_threads(), make_events(), pricing, "/repo/foo/api")
        self.assertEqual(detail["project"]["project_id"], "/repo/foo/api")
        self.assertEqual(detail["project"]["project_name"], "foo/api")
        self.assertEqual(detail["project"]["cwd"], "/repo/foo/api")
        self.assertEqual(detail["usage"]["total_tokens"], 68)

    def test_build_project_detail_accepts_display_name_for_compatibility(self) -> None:
        detail = build_project_detail(make_threads(), make_events(), PricingConfig(2.5, 0.25, 15.0), "foo/api")
        self.assertIsNotNone(detail)
        self.assertEqual(detail["project"]["project_id"], "/repo/foo/api")

    def test_usage_from_session_events_uses_same_logic_as_usage_from_events(self) -> None:
        session_events = [event for event in make_events() if event.session_id == "s1"]
        self.assertEqual(usage_from_session_events(session_events), usage_from_events(session_events))


if __name__ == "__main__":
    unittest.main()
