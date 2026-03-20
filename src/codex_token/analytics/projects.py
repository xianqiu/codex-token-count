from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from hashlib import sha1
from pathlib import Path

from ..models import ThreadRecord
from .pricing import estimate_cost
from .usage import usage_from_events


def build_project_names(paths: Iterable[str]) -> dict[str, str]:
    unique_paths = sorted(set(paths))
    if not unique_paths:
        return {}

    path_parts = {path: _normalized_parts(path) for path in unique_paths}
    names = {path: parts[-1] if parts else path for path, parts in path_parts.items()}

    while True:
        grouped: dict[str, list[str]] = defaultdict(list)
        for path, name in names.items():
            grouped[name].append(path)

        collisions = {name: items for name, items in grouped.items() if len(items) > 1}
        if not collisions:
            return names

        updated = False
        for paths_with_same_name in collisions.values():
            for path in paths_with_same_name:
                parts = path_parts[path]
                current_name = names[path]
                used_parts = len(current_name.split("/"))
                if used_parts < len(parts):
                    names[path] = "/".join(parts[-(used_parts + 1):])
                    updated = True
                else:
                    names[path] = f"{current_name}-{sha1(path.encode('utf-8')).hexdigest()[:6]}"
                    updated = True
        if not updated:
            return names


def build_project_list(
    threads: Iterable[ThreadRecord],
    token_events: Iterable,
    pricing,
    *,
    limit: int,
) -> list[dict[str, object]]:
    thread_items = list(threads)
    project_names = build_project_names(thread.cwd for thread in thread_items)
    events_by_session: dict[str, list] = defaultdict(list)
    for event in token_events:
        events_by_session[event.session_id].append(event)

    rows: list[dict[str, object]] = []
    for cwd, project_threads in _group_threads_by_cwd(thread_items).items():
        project_events = [
            event
            for thread in project_threads
            for event in events_by_session.get(thread.session_id, [])
        ]
        usage = usage_from_events(project_events)
        rows.append(
            {
                "project_id": cwd,
                "project_name": project_names[cwd],
                "sessions": len(project_threads),
                "last_updated_at": max(thread.updated_at for thread in project_threads),
                "usage": usage,
                "cost": estimate_cost(usage, pricing),
            }
        )

    rows.sort(
        key=lambda item: (
            int(item["usage"]["total_tokens"]),
            item["last_updated_at"],
            str(item["project_name"]),
        ),
        reverse=True,
    )
    return rows[: max(limit, 1)]


def build_project_detail(
    threads: Iterable[ThreadRecord],
    token_events: Iterable,
    pricing,
    project_ref: str,
) -> dict[str, object] | None:
    thread_items = list(threads)
    project_names = build_project_names(thread.cwd for thread in thread_items)
    resolved_cwd = _resolve_project_ref(project_ref, project_names)
    if resolved_cwd is None:
        return None

    project_threads = [thread for thread in thread_items if thread.cwd == resolved_cwd]
    session_ids = {thread.session_id for thread in project_threads}
    project_events = [event for event in token_events if event.session_id in session_ids]
    usage = usage_from_events(project_events)
    return {
        "scope": "project_detail",
        "project": {
            "project_id": resolved_cwd,
            "project_name": project_names[resolved_cwd],
            "cwd": resolved_cwd,
            "sessions": len(project_threads),
            "last_updated_at": max((thread.updated_at for thread in project_threads), default=None),
        },
        "usage": usage,
        "cost": estimate_cost(usage, pricing),
    }


def _group_threads_by_cwd(threads: Iterable[ThreadRecord]) -> dict[str, list[ThreadRecord]]:
    grouped: dict[str, list[ThreadRecord]] = defaultdict(list)
    for thread in threads:
        grouped[thread.cwd].append(thread)
    return grouped


def _normalized_parts(path: str) -> list[str]:
    parts = [part for part in Path(path).parts if part not in {"", "/"}]
    return parts or [path]


def _resolve_project_ref(project_ref: str, project_names: dict[str, str]) -> str | None:
    if project_ref in project_names:
        return project_ref

    cwd_by_name = {name: cwd for cwd, name in project_names.items()}
    return cwd_by_name.get(project_ref)
