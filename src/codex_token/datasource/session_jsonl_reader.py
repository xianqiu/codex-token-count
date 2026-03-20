from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from ..models import TokenEvent


SESSION_ID_PATTERN = re.compile(
    r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$",
    re.IGNORECASE,
)
ROLLOUT_FILE_PATTERN = re.compile(
    r"^rollout-\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}-(.+)$",
    re.IGNORECASE,
)


def _parse_timestamp(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value).astimezone(timezone.utc)


def _extract_session_id(file_path: Path) -> str:
    match = SESSION_ID_PATTERN.search(file_path.stem)
    if match:
        return match.group(1)
    rollout_match = ROLLOUT_FILE_PATTERN.match(file_path.stem)
    if rollout_match:
        return rollout_match.group(1)
    return file_path.stem


def read_token_events(sessions_dir: Path) -> list[TokenEvent]:
    if not sessions_dir.exists():
        return []

    events: list[TokenEvent] = []
    for file_path in sorted(sessions_dir.rglob("*.jsonl")):
        with file_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue

                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if payload.get("type") != "event_msg":
                    continue

                event_payload = payload.get("payload") or {}
                if event_payload.get("type") != "token_count":
                    continue

                info = event_payload.get("info") or {}
                total_usage = info.get("total_token_usage") or {}
                session_id = _extract_session_id(file_path)
                timestamp = payload.get("timestamp")
                if not timestamp:
                    continue

                events.append(
                    TokenEvent(
                        session_id=session_id,
                        timestamp=_parse_timestamp(timestamp),
                        input_tokens=int(total_usage.get("input_tokens", 0)),
                        cached_input_tokens=int(total_usage.get("cached_input_tokens", 0)),
                        output_tokens=int(total_usage.get("output_tokens", 0)),
                        reasoning_output_tokens=int(total_usage.get("reasoning_output_tokens", 0)),
                        total_tokens=int(total_usage.get("total_tokens", 0)),
                    )
                )

    events.sort(key=lambda item: (item.timestamp, item.session_id))
    return events
