from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class ThreadRecord:
    session_id: str
    title: str
    cwd: str
    model_provider: str
    created_at: datetime
    updated_at: datetime
    tokens_used: int


@dataclass(frozen=True)
class TokenEvent:
    session_id: str
    timestamp: datetime
    input_tokens: int
    cached_input_tokens: int
    output_tokens: int
    reasoning_output_tokens: int
    total_tokens: int


@dataclass(frozen=True)
class CodexPaths:
    codex_home: Path
    state_db: Path
    sessions_dir: Path
