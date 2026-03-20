from __future__ import annotations

from pathlib import Path

from ..paths import resolve_codex_paths
from ..models import ThreadRecord, TokenEvent
from .session_jsonl_reader import read_token_events
from .sqlite_reader import read_threads


def load_threads(codex_home: str | Path | None = None, *, include_archived: bool = False) -> list[ThreadRecord]:
    paths = resolve_codex_paths(codex_home)
    return read_threads(paths.state_db, include_archived=include_archived)


def load_token_events(
    codex_home: str | Path | None = None,
    *,
    session_ids: set[str] | None = None,
) -> list[TokenEvent]:
    paths = resolve_codex_paths(codex_home)
    events = read_token_events(paths.sessions_dir)
    if session_ids is None:
        return events
    return [event for event in events if event.session_id in session_ids]
