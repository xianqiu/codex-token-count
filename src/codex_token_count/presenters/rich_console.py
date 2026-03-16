from __future__ import annotations

from datetime import datetime

from rich.box import SIMPLE_HEAVY
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


def build_console() -> Console:
    return Console(color_system="auto", soft_wrap=False)


def _fmt_datetime(value: object) -> str:
    if isinstance(value, datetime):
        return value.astimezone().strftime("%Y-%m-%d %H:%M:%S")
    return "-"


def _fmt_int(value: object, compact: bool = False) -> str:
    if not isinstance(value, int):
        return "-"
    if not compact:
        return f"{value:,}"

    thresholds = [
        (1_000_000_000, "B"),
        (1_000_000, "M"),
        (1_000, "K"),
    ]
    for threshold, suffix in thresholds:
        if value >= threshold:
            return f"{value / threshold:.1f}{suffix}"
    return str(value)


def _fmt_value(value: object) -> str:
    if value is None:
        return "-"
    if isinstance(value, datetime):
        return _fmt_datetime(value)
    if isinstance(value, int):
        return _fmt_int(value)
    return str(value)


def _sparkline(values: list[int]) -> str:
    if not values:
        return ""
    blocks = "▁▂▃▄▅▆▇█"
    max_value = max(values)
    if max_value <= 0:
        return blocks[0] * len(values)
    result: list[str] = []
    for value in values:
        index = round((value / max_value) * (len(blocks) - 1))
        result.append(blocks[index])
    return "".join(result)


def _fmt_percent(numerator: int, denominator: int) -> str:
    if denominator <= 0:
        return "0.0%"
    return f"{(numerator / denominator) * 100:.1f}%"


def _input_breakdown_rows(input_tokens: int, cached_input_tokens: int) -> list[tuple[str, str]]:
    non_cached_input_tokens = max(input_tokens - cached_input_tokens, 0)
    return [
        ("Input Tokens", _fmt_value(input_tokens)),
        (
            "  - Cached Input",
            f"{_fmt_value(cached_input_tokens)} ({_fmt_percent(cached_input_tokens, input_tokens)})",
        ),
        (
            "  - Non-cached Input",
            f"{_fmt_value(non_cached_input_tokens)} ({_fmt_percent(non_cached_input_tokens, input_tokens)})",
        ),
    ]


def _output_breakdown_rows(output_tokens: int, reasoning_output_tokens: int) -> list[tuple[str, str]]:
    non_reasoning_output_tokens = max(output_tokens - reasoning_output_tokens, 0)
    return [
        ("Output Tokens", _fmt_value(output_tokens)),
        (
            "  - Reasoning Output",
            f"{_fmt_value(reasoning_output_tokens)} ({_fmt_percent(reasoning_output_tokens, output_tokens)})",
        ),
        (
            "  - Non-reasoning Output",
            f"{_fmt_value(non_reasoning_output_tokens)} ({_fmt_percent(non_reasoning_output_tokens, output_tokens)})",
        ),
    ]


def _build_breakdown_panel(input_tokens: int, cached_input_tokens: int, output_tokens: int, reasoning_output_tokens: int) -> Panel:
    breakdown = Table.grid(expand=True, padding=(0, 3))
    breakdown.add_column(style="bold cyan")
    breakdown.add_column(justify="right", style="magenta")
    input_rows = _input_breakdown_rows(input_tokens, cached_input_tokens)
    output_rows = _output_breakdown_rows(output_tokens, reasoning_output_tokens)
    for label, value in input_rows:
        breakdown.add_row(label, value)
    breakdown.add_row("", "")
    for label, value in output_rows:
        breakdown.add_row(label, value)
    return Panel(breakdown, title="Breakdown", box=SIMPLE_HEAVY)


def print_summary_view(console: Console, summary: dict[str, object], trend_rows: list[dict[str, object]]) -> None:
    kpis = [
        ("Sessions", summary["total_sessions"], "cyan"),
        ("Total Tokens", summary["total_tokens"], "magenta"),
        (f"{summary['window_days']}-Day Tokens", summary["tokens_in_window"], "yellow"),
        ("30-Day Tokens", summary["tokens_last_30_days"], "green"),
    ]
    panels = [
        Panel.fit(
            Text.from_markup(f"[bold {color}]{_fmt_int(value, compact=True)}[/bold {color}]\n[dim]{label}[/dim]"),
            box=SIMPLE_HEAVY,
            padding=(1, 2),
        )
        for label, value, color in kpis
    ]
    console.print(Columns(panels, equal=True, expand=True))

    last_updated = summary.get("last_updated_at")
    trend_values = [int(row["tokens"]) for row in trend_rows]
    trend_table = Table(box=SIMPLE_HEAVY, expand=True)
    trend_table.add_column("Date", style="bold")
    trend_table.add_column("Tokens", justify="right", style="magenta")
    trend_table.add_column("Bar", style="cyan")
    max_value = max(trend_values, default=0)
    for row in trend_rows:
        value = int(row["tokens"])
        bar_length = 1 if max_value == 0 else max(1, round((value / max_value) * 18))
        trend_table.add_row(
            str(row["date"]),
            _fmt_int(value),
            "█" * bar_length if value > 0 else "·",
        )

    console.print(
        Panel(
            trend_table,
            title="Usage Summary",
            subtitle=f"Last updated {_fmt_datetime(last_updated)}",
            box=SIMPLE_HEAVY,
        )
    )
    console.print(
        _build_breakdown_panel(
            int(summary["input_tokens"]),
            int(summary["cached_input_tokens"]),
            int(summary["output_tokens"]),
            int(summary["reasoning_output_tokens"]),
        )
    )


def print_rows_table(
    console: Console,
    rows: list[dict[str, object]],
    columns: list[tuple[str, str]],
    *,
    title: str | None = None,
) -> None:
    table = Table(title=title, box=SIMPLE_HEAVY, header_style="bold cyan", expand=True)
    numeric_keys = {"tokens_used", "sessions", "tokens", "total_tokens", "delta_tokens", "input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens"}
    for key, header in columns:
        justify = "right" if key in numeric_keys else "left"
        overflow = "fold" if key in {"title", "cwd"} else "ellipsis"
        style = "magenta" if "token" in key else None
        table.add_column(header, justify=justify, overflow=overflow, style=style)

    for row in rows:
        rendered = [_fmt_value(row.get(key)) for key, _ in columns]
        table.add_row(*rendered)

    console.print(table)


def print_project_view(
    console: Console,
    path: str,
    summary: dict[str, object],
    usage: dict[str, int],
    rows: list[dict[str, object]],
) -> None:
    meta = Table.grid(padding=(0, 2))
    meta.add_column(style="bold cyan")
    meta.add_column()
    meta.add_row("Project", path)
    meta.add_row("Sessions", _fmt_value(summary["total_sessions"]))
    meta.add_row("Total tokens", _fmt_value(summary["total_tokens"]))
    meta.add_row("Last updated", _fmt_datetime(summary["last_updated_at"]))
    console.print(Panel(meta, title="Project Detail", box=SIMPLE_HEAVY))
    console.print(
        _build_breakdown_panel(
            usage["input_tokens"],
            usage["cached_input_tokens"],
            usage["output_tokens"],
            usage["reasoning_output_tokens"],
        )
    )
    if rows:
        print_rows_table(
            console,
            rows,
            [
                ("session_id", "Session ID"),
                ("tokens_used", "Tokens"),
                ("updated_at", "Updated At"),
                ("title", "Title"),
            ],
            title="Sessions",
        )


def print_session_view(
    console: Console,
    session: dict[str, object],
    usage: dict[str, int],
    event_rows: list[dict[str, object]],
    event_count: int,
) -> None:
    meta = Table.grid(padding=(0, 2))
    meta.add_column(style="bold cyan")
    meta.add_column()
    meta.add_row("Session ID", str(session["session_id"]))
    meta.add_row("Title", str(session["title"]))
    meta.add_row("CWD", str(session["cwd"]))
    meta.add_row("Model", str(session["model_provider"]))
    meta.add_row("Created", _fmt_datetime(session["created_at"]))
    meta.add_row("Updated", _fmt_datetime(session["updated_at"]))
    meta.add_row("Tokens", _fmt_value(session["tokens_used"]))
    meta.add_row("Events", _fmt_int(event_count))
    console.print(Panel(meta, title="Session Detail", box=SIMPLE_HEAVY))
    console.print(
        _build_breakdown_panel(
            usage["input_tokens"],
            usage["cached_input_tokens"],
            usage["output_tokens"],
            usage["reasoning_output_tokens"],
        )
    )
    if event_rows:
        print_rows_table(
            console,
            event_rows,
            [
                ("timestamp", "Timestamp"),
                ("total_tokens", "Total"),
                ("delta_tokens", "Delta"),
                ("input_tokens", "Input"),
                ("cached_input_tokens", "Cached"),
                ("output_tokens", "Output"),
                ("reasoning_output_tokens", "Reasoning"),
            ],
            title="Recent Token Events",
        )


def print_trend_view(console: Console, rows: list[dict[str, object]]) -> None:
    print_rows_table(console, rows, [("date", "Date"), ("tokens", "Tokens")], title="Daily Trend")
