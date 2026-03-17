from __future__ import annotations

from pathlib import Path
import sqlite3
import unittest

from codex_token_count.datasource.session_jsonl_reader import read_token_events
from codex_token_count.datasource.sqlite_reader import read_threads


class ReaderTests(unittest.TestCase):
    def test_read_threads(self) -> None:
        with self.subTest("sqlite"), tempfile_directory() as tmp_path:
            db_path = tmp_path / "state_5.sqlite"
            connection = sqlite3.connect(db_path)
            try:
                connection.execute(
                    """
                    CREATE TABLE threads (
                      id TEXT PRIMARY KEY,
                      rollout_path TEXT NOT NULL,
                      created_at INTEGER NOT NULL,
                      updated_at INTEGER NOT NULL,
                      source TEXT NOT NULL,
                      model_provider TEXT NOT NULL,
                      cwd TEXT NOT NULL,
                      title TEXT NOT NULL,
                      sandbox_policy TEXT NOT NULL,
                      approval_mode TEXT NOT NULL,
                      tokens_used INTEGER NOT NULL DEFAULT 0,
                      has_user_event INTEGER NOT NULL DEFAULT 0,
                      archived INTEGER NOT NULL DEFAULT 0
                    )
                    """
                )
                connection.execute(
                    """
                    INSERT INTO threads
                      (id, rollout_path, created_at, updated_at, source, model_provider, cwd, title, sandbox_policy, approval_mode, tokens_used, has_user_event, archived)
                    VALUES
                      ('abc', 'x', 1710000000, 1710003600, 'cli', 'openai', '/repo', 'title', 'workspace-write', 'on-request', 123, 1, 0)
                    """
                )
                connection.commit()
            finally:
                connection.close()

            rows = read_threads(db_path)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].session_id, "abc")
            self.assertEqual(rows[0].tokens_used, 123)

    def test_read_threads_excludes_archived_by_default(self) -> None:
        with self.subTest("archived"), tempfile_directory() as tmp_path:
            db_path = tmp_path / "state_5.sqlite"
            connection = sqlite3.connect(db_path)
            try:
                connection.execute(
                    """
                    CREATE TABLE threads (
                      id TEXT PRIMARY KEY,
                      rollout_path TEXT NOT NULL,
                      created_at INTEGER NOT NULL,
                      updated_at INTEGER NOT NULL,
                      source TEXT NOT NULL,
                      model_provider TEXT NOT NULL,
                      cwd TEXT NOT NULL,
                      title TEXT NOT NULL,
                      sandbox_policy TEXT NOT NULL,
                      approval_mode TEXT NOT NULL,
                      tokens_used INTEGER NOT NULL DEFAULT 0,
                      has_user_event INTEGER NOT NULL DEFAULT 0,
                      archived INTEGER NOT NULL DEFAULT 0
                    )
                    """
                )
                connection.executemany(
                    """
                    INSERT INTO threads
                      (id, rollout_path, created_at, updated_at, source, model_provider, cwd, title, sandbox_policy, approval_mode, tokens_used, has_user_event, archived)
                    VALUES
                      (?, 'x', 1710000000, 1710003600, 'cli', 'openai', '/repo', 'title', 'workspace-write', 'on-request', 123, 1, ?)
                    """,
                    [("active", 0), ("archived", 1)],
                )
                connection.commit()
            finally:
                connection.close()

            rows = read_threads(db_path)
            self.assertEqual([row.session_id for row in rows], ["active"])

            all_rows = read_threads(db_path, include_archived=True)
            self.assertEqual(sorted(row.session_id for row in all_rows), ["active", "archived"])

    def test_read_token_events(self) -> None:
        with self.subTest("jsonl"), tempfile_directory() as tmp_path:
            session_dir = tmp_path / "sessions" / "2026" / "03" / "15"
            session_dir.mkdir(parents=True)
            session_file = session_dir / "rollout-2026-03-15T10-00-00-abc123.jsonl"
            session_file.write_text(
                "\n".join(
                    [
                        '{"timestamp":"2026-03-15T10:00:00.000Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":10,"cached_input_tokens":2,"output_tokens":3,"reasoning_output_tokens":1,"total_tokens":13}}}}',
                        '{"timestamp":"2026-03-15T10:00:01.000Z","type":"response_item","payload":{"type":"message"}}',
                    ]
                ),
                encoding="utf-8",
            )

            rows = read_token_events(tmp_path / "sessions")
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].session_id, "abc123")
            self.assertEqual(rows[0].total_tokens, 13)

    def test_read_token_events_with_uuid_session_id(self) -> None:
        with self.subTest("uuid"), tempfile_directory() as tmp_path:
            session_dir = tmp_path / "sessions" / "2026" / "03" / "15"
            session_dir.mkdir(parents=True)
            session_file = session_dir / "rollout-2026-03-15T10-00-00-019cf082-0614-7663-882c-6892056f3d12.jsonl"
            session_file.write_text(
                '{"timestamp":"2026-03-15T10:00:00.000Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"total_tokens":99}}}}',
                encoding="utf-8",
            )

            rows = read_token_events(tmp_path / "sessions")
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].session_id, "019cf082-0614-7663-882c-6892056f3d12")
            self.assertEqual(rows[0].total_tokens, 99)


class tempfile_directory:
    def __enter__(self) -> Path:
        import tempfile

        self._tmp = tempfile.TemporaryDirectory()
        return Path(self._tmp.name)

    def __exit__(self, exc_type, exc, tb) -> None:
        self._tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
