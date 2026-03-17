from __future__ import annotations

from pathlib import Path

from .models import CodexPaths


def resolve_codex_paths(codex_home: str | Path | None = None) -> CodexPaths:
    base = Path(codex_home or Path.home() / ".codex").expanduser()
    return CodexPaths(
        codex_home=base,
        state_db=base / "state_5.sqlite",
        sessions_dir=base / "sessions",
    )
