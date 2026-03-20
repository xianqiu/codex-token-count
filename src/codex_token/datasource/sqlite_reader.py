from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from ..models import ThreadRecord


def _from_unix(ts: int) -> datetime:
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def read_threads(state_db: Path, *, include_archived: bool = False) -> list[ThreadRecord]:
    if not state_db.exists():
        return []

    connection = sqlite3.connect(state_db)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            """
            SELECT
              id,
              title,
              cwd,
              model_provider,
              created_at,
              updated_at,
              tokens_used
            FROM threads
            WHERE (? OR archived = 0)
            ORDER BY updated_at DESC, id DESC
            """,
            (1 if include_archived else 0,),
        ).fetchall()
    finally:
        connection.close()

    return [
        ThreadRecord(
            session_id=row["id"],
            title=row["title"],
            cwd=row["cwd"],
            model_provider=row["model_provider"],
            created_at=_from_unix(row["created_at"]),
            updated_at=_from_unix(row["updated_at"]),
            tokens_used=row["tokens_used"],
        )
        for row in rows
    ]
