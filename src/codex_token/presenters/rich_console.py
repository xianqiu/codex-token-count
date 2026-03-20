from __future__ import annotations

from datetime import datetime

from rich.box import SIMPLE_HEAVY
from rich.columns import Columns
from rich.align import Align
from rich.console import Console
from rich.padding import Padding
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

    thresholds = [(1_000_000_000, "B"), (1_000_000, "M"), (1_000, "K")]
    for threshold, suffix in thresholds:
        if value >= threshold:
            return f"{value / threshold:.1f}{suffix}"
    return str(value)


def _fmt_money(value: object) -> str:
    if not isinstance(value, (int, float)):
        return "-"
    return f"${value:.2f}"


def _spark_bar(value: int, max_value: int, width: int = 18) -> str:
    if value <= 0 or max_value <= 0:
        return "·"
    bar_length = max(1, round((value / max_value) * width))
    return "█" * bar_length


def _fmt_value(value: object) -> str:
    if value is None:
        return "-"
    if isinstance(value, datetime):
        return _fmt_datetime(value)
    if isinstance(value, int):
        return _fmt_int(value)
    if isinstance(value, float):
        return _fmt_money(value)
    return str(value)


def _fmt_percent(numerator: int, denominator: int) -> str:
    if denominator <= 0:
        return "0.0%"
    return f"{(numerator / denominator) * 100:.1f}%"


def _build_breakdown_panel(usage: dict[str, int]) -> Panel:
    breakdown = Table.grid(expand=True, padding=(0, 3))
    breakdown.add_column(style="bold cyan")
    breakdown.add_column(justify="right", style="magenta")
    breakdown.add_row("Input Tokens", _fmt_value(usage["input_tokens"]))
    breakdown.add_row(
        "  - Cached Input",
        f"{_fmt_value(usage['cached_input_tokens'])} ({_fmt_percent(usage['cached_input_tokens'], usage['input_tokens'])})",
    )
    breakdown.add_row(
        "  - Non-cached Input",
        f"{_fmt_value(usage['non_cached_input_tokens'])} ({_fmt_percent(usage['non_cached_input_tokens'], usage['input_tokens'])})",
    )
    breakdown.add_row("", "")
    breakdown.add_row("Output Tokens", _fmt_value(usage["output_tokens"]))
    breakdown.add_row(
        "  - Reasoning Output",
        f"{_fmt_value(usage['reasoning_output_tokens'])} ({_fmt_percent(usage['reasoning_output_tokens'], usage['output_tokens'])})",
    )
    breakdown.add_row(
        "  - Non-reasoning Output",
        f"{_fmt_value(usage['non_reasoning_output_tokens'])} ({_fmt_percent(usage['non_reasoning_output_tokens'], usage['output_tokens'])})",
    )
    return Panel(breakdown, title="Breakdown", box=SIMPLE_HEAVY)


def print_summary_view(console: Console, payload: dict[str, object]) -> None:
    console.print(Padding(Align.center(Text("Usage Summary", style="bold")), (1, 0, 1, 0)))

    cards = [
        ("Sessions", payload["sessions"], "cyan"),
        ("Total Tokens", payload["usage"]["total_tokens"], "magenta"),
        ("7-Day Tokens", payload["tokens_last_7_days"], "yellow"),
        ("30-Day Tokens", payload["tokens_last_30_days"], "green"),
    ]
    if payload.get("cost") is not None:
        cards.append(("Estimated Cost", payload["cost"]["total_cost_usd"], "green"))

    kpi_grid = Table.grid(expand=False, padding=(0, 8))
    for _ in cards:
        kpi_grid.add_column(justify="left")
    kpi_grid.add_row(
        *[
            Text.from_markup(
                f"[bold {color}]{_fmt_money(value) if isinstance(value, float) else _fmt_int(value, compact=True)}[/bold {color}]\n[dim]{label}[/dim]"
            )
            for label, value, color in cards
        ]
    )
    console.print(Padding(Align.center(kpi_grid), (1, 0, 1, 0)))

    trend_rows = payload["trend_rows"]
    title = Text("7-Day Usage", style="bold")
    trend_table = Table(title=title, title_justify="center", box=SIMPLE_HEAVY, header_style="bold", expand=True, pad_edge=True)
    trend_table.add_column("Date", style="bold")
    trend_table.add_column("Tokens", justify="right", style="magenta")
    trend_table.add_column("Bar", style="cyan")
    show_cost = any(row.get("cost") is not None for row in trend_rows)
    if show_cost:
        trend_table.add_column("Cost", justify="right", style="green")
    max_value = max((row["usage"]["total_tokens"] for row in trend_rows), default=0)
    for row in reversed(trend_rows):
        value = int(row["usage"]["total_tokens"])
        rendered = [str(row["date"]), _fmt_int(value), _spark_bar(value, max_value)]
        if show_cost:
            rendered.append(_fmt_money(row["cost"]["total_cost_usd"]) if row.get("cost") is not None else "-")
        trend_table.add_row(*rendered)
    console.print(Padding(trend_table, (1, 1, 0, 1)))
    updated_text = Text(f"Last updated {_fmt_datetime(payload.get('last_updated_at'))}")
    console.print(Padding(updated_text, (1, 0, 1, 0)), justify="center")


def print_trend_view(console: Console, payload: dict[str, object]) -> None:
    title = Text(f"Trend / {payload['days']}-Day Usage", style="bold")
    table = Table(title=title, title_justify="center", box=SIMPLE_HEAVY, header_style="bold", expand=True, pad_edge=True)
    table.add_column("Date")
    table.add_column("Tokens", justify="right", style="magenta")
    table.add_column("Bar", style="cyan")
    if payload["rows"] and payload["rows"][0].get("cost") is not None:
        table.add_column("Cost", justify="right", style="green")

    max_value = max((row["usage"]["total_tokens"] for row in payload["rows"]), default=0)
    for row in reversed(payload["rows"]):
        usage = row["usage"]
        rendered = [
            str(row["date"]),
            _fmt_int(usage["total_tokens"]),
            _spark_bar(int(usage["total_tokens"]), max_value),
        ]
        if row.get("cost") is not None:
            rendered.append(_fmt_money(row["cost"]["total_cost_usd"]))
        table.add_row(*rendered)

    console.print(Padding(table, (1, 1, 0, 1)))


def print_project_list_view(console: Console, payload: dict[str, object]) -> None:
    table = Table(title="Projects", box=SIMPLE_HEAVY, header_style="bold cyan", expand=True)
    table.add_column("Project")
    table.add_column("Sessions", justify="right")
    table.add_column("Tokens", justify="right", style="magenta")
    table.add_column("Updated", justify="left")
    show_cost = any(row.get("cost") is not None for row in payload["rows"])
    if show_cost:
        table.add_column("Cost", justify="right", style="green")

    for row in payload["rows"]:
        rendered = [
            str(row["project_name"]),
            _fmt_int(row["sessions"]),
            _fmt_int(row["usage"]["total_tokens"]),
            _fmt_datetime(row["last_updated_at"]),
        ]
        if show_cost:
            rendered.append(_fmt_money(row["cost"]["total_cost_usd"]) if row.get("cost") is not None else "-")
        table.add_row(*rendered)
    console.print(table)


def print_project_detail_view(console: Console, payload: dict[str, object]) -> None:
    project = payload["project"]
    cost = payload.get("cost")
    title = Text("Project Detail", style="bold")
    title.append(" - ", style="bold")
    title.append(str(project["project_name"]), style="bold cyan")
    console.print(Padding(Align.center(title), (1, 0, 1, 0)))

    cards = [
        ("Sessions", project["sessions"], "cyan"),
        ("Total Tokens", payload["usage"]["total_tokens"], "magenta"),
    ]
    if cost is not None:
        cards.append(("Estimated Cost", cost["total_cost_usd"], "green"))

    card_grid = Table.grid(expand=False, padding=(0, 8))
    for _ in cards:
        card_grid.add_column(justify="left")
    card_grid.add_row(
        *[
            Text.from_markup(
                f"[bold {color}]{_fmt_money(value) if isinstance(value, float) else _fmt_int(value, compact=True)}[/bold {color}]\n[dim]{label}[/dim]"
            )
            for label, value, color in cards
        ]
    )
    console.print(Padding(Align.center(card_grid), (1, 0, 1, 0)))

    console.print(Padding(_build_breakdown_panel(payload["usage"]), (1, 1, 0, 1)))
    updated_text = Text(f"Last updated {_fmt_datetime(project['last_updated_at'])}")
    console.print(Padding(updated_text, (1, 0, 1, 0)), justify="center")
