from __future__ import annotations

import argparse
import json
from datetime import datetime

from .analytics import build_daily_trend, build_project_detail, build_project_list, build_summary
from .config import load_config
from .datasource import load_threads, load_token_events
from .presenters import build_console, print_project_detail_view, print_project_list_view, print_summary_view, print_trend_view


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="codex-token", description="Analyze local Codex token usage.")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Output JSON.")

    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("summary", help="Show global usage summary.")

    trend_parser = subparsers.add_parser("trend", help="Show daily token trend.")
    trend_parser.add_argument("--days", type=int, help="Custom trend window in days.")

    project_parser = subparsers.add_parser("project", help="Show project ranking or one project.")
    project_parser.add_argument("project_ref", nargs="?", help="Stable project id to inspect. Display name is also accepted.")
    project_parser.add_argument("--limit", type=int, help="Number of projects to show in list mode.")

    return parser


def _serialize(value: object) -> object:
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _print_json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, default=_serialize))


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.command = args.command or "summary"
    config = load_config()
    console = None if args.as_json else build_console()

    threads = load_threads(
        config.codex_home,
        include_archived=config.defaults.include_archived,
    )
    token_events = load_token_events(
        config.codex_home,
        session_ids={thread.session_id for thread in threads},
    )

    if args.command == "summary":
        payload = build_summary(threads, token_events, config.pricing)
        if args.as_json:
            _print_json(payload)
            return 0
        print_summary_view(console, payload)
        return 0

    if args.command == "trend":
        days = max(args.days or config.defaults.trend_days, 1)
        payload = build_daily_trend(token_events, config.pricing, days=days)
        if args.as_json:
            _print_json(payload)
            return 0
        print_trend_view(console, payload)
        return 0

    if args.command == "project":
        if args.project_ref:
            payload = build_project_detail(threads, token_events, config.pricing, args.project_ref)
            if payload is None:
                parser.error(f"Project not found: {args.project_ref}")
            if args.as_json:
                _print_json(payload)
                return 0
            print_project_detail_view(console, payload)
            return 0

        limit = max(args.limit or config.defaults.project_limit, 1)
        rows = build_project_list(threads, token_events, config.pricing, limit=limit)
        payload = {"scope": "project_list", "limit": limit, "rows": rows}
        if args.as_json:
            _print_json(payload)
            return 0
        print_project_list_view(console, payload)
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2
