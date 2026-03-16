from __future__ import annotations

import io
import json
import sqlite3
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from codex_token_count.cli import main


class CliTests(unittest.TestCase):
    def test_project_command_outputs_filtered_sessions(self) -> None:
        with tempfile_directory() as tmp_path:
            build_codex_fixture(tmp_path)
            output = run_cli(tmp_path, "project", "/repo/a")
            self.assertIn("Project Detail", output)
            self.assertIn("/repo/a", output)
            self.assertIn("Breakdown", output)
            self.assertIn("Cached Input", output)
            self.assertIn("sess-001", output)
            self.assertIn("sess-002", output)
            self.assertNotIn("sess-003", output)

    def test_projects_command_limit(self) -> None:
        with tempfile_directory() as tmp_path:
            build_codex_fixture(tmp_path)
            output = run_cli(tmp_path, "--json", "projects", "--limit", "1")
            payload = json.loads(output)
            self.assertEqual(len(payload), 1)

    def test_project_command_supports_unique_substring_match(self) -> None:
        with tempfile_directory() as tmp_path:
            build_codex_fixture(tmp_path)
            output = run_cli(tmp_path, "--json", "project", "repo/b")
            payload = json.loads(output)
            self.assertEqual(payload["path"], "/repo/b")
            self.assertEqual(len(payload["sessions"]), 1)

    def test_session_command_supports_prefix_and_shows_events(self) -> None:
        with tempfile_directory() as tmp_path:
            build_codex_fixture(tmp_path)
            output = run_cli(tmp_path, "session", "sess-001", "--events", "2")
            self.assertIn("Session ID", output)
            self.assertIn("/repo/a", output)
            self.assertIn("Delta", output)
            self.assertIn("15", output)

    def test_session_command_json(self) -> None:
        with tempfile_directory() as tmp_path:
            build_codex_fixture(tmp_path)
            output = run_cli(tmp_path, "--json", "session", "sess-002")
            payload = json.loads(output)
            self.assertEqual(payload["session"]["session_id"], "sess-002")
            self.assertEqual(payload["usage"]["input_tokens"], 15)
            self.assertEqual(payload["usage"]["output_tokens"], 5)
            self.assertEqual(len(payload["token_events"]), 1)

    def test_summary_command_json_includes_breakdown(self) -> None:
        with tempfile_directory() as tmp_path:
            build_codex_fixture(tmp_path)
            output = run_cli(tmp_path, "--json", "summary")
            payload = json.loads(output)
            self.assertEqual(payload["window_days"], 7)
            self.assertIn("tokens_in_window", payload)
            self.assertEqual(payload["input_tokens"], 35)
            self.assertEqual(payload["cached_input_tokens"], 0)
            self.assertEqual(payload["output_tokens"], 12)
            self.assertEqual(payload["reasoning_output_tokens"], 0)

    def test_summary_command_respects_days(self) -> None:
        with tempfile_directory() as tmp_path:
            build_codex_fixture(tmp_path)
            output = run_cli(tmp_path, "--json", "summary", "--days", "1000")
            payload = json.loads(output)
            self.assertEqual(payload["window_days"], 1000)
            self.assertEqual(payload["tokens_in_window"], 90)

    def test_project_command_json_includes_breakdown(self) -> None:
        with tempfile_directory() as tmp_path:
            build_codex_fixture(tmp_path)
            output = run_cli(tmp_path, "--json", "project", "/repo/a")
            payload = json.loads(output)
            self.assertEqual(payload["usage"]["input_tokens"], 35)
            self.assertEqual(payload["usage"]["cached_input_tokens"], 0)
            self.assertEqual(payload["usage"]["output_tokens"], 12)
            self.assertEqual(payload["usage"]["reasoning_output_tokens"], 0)


def run_cli(codex_home: Path, *args: str) -> str:
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        exit_code = main(["--codex-home", str(codex_home), *args])
    if exit_code != 0:
        raise AssertionError(f"CLI exited with {exit_code}")
    return buffer.getvalue()


def build_codex_fixture(codex_home: Path) -> None:
    sessions_dir = codex_home / "sessions" / "2026" / "03" / "15"
    sessions_dir.mkdir(parents=True)

    state_db = codex_home / "state_5.sqlite"
    connection = sqlite3.connect(state_db)
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
              (?, 'x', ?, ?, 'cli', 'openai', ?, ?, 'workspace-write', 'on-request', ?, 1, 0)
            """,
            [
                ("sess-001", 1710000000, 1710003600, "/repo/a", "first", 20),
                ("sess-002", 1710000000, 1710007200, "/repo/a", "second", 30),
                ("sess-003", 1710000000, 1710010800, "/repo/b", "third", 40),
            ],
        )
        connection.commit()
    finally:
        connection.close()

    write_jsonl(
        sessions_dir / "rollout-2026-03-15T10-00-00-sess-001.jsonl",
        [
            {
                "timestamp": "2026-03-15T10:00:00.000Z",
                "type": "event_msg",
                "payload": {
                    "type": "token_count",
                    "info": {
                        "total_token_usage": {
                            "input_tokens": 10,
                            "cached_input_tokens": 0,
                            "output_tokens": 2,
                            "reasoning_output_tokens": 0,
                            "total_tokens": 12,
                        }
                    },
                },
            },
            {
                "timestamp": "2026-03-15T10:05:00.000Z",
                "type": "event_msg",
                "payload": {
                    "type": "token_count",
                    "info": {
                        "total_token_usage": {
                            "input_tokens": 20,
                            "cached_input_tokens": 0,
                            "output_tokens": 7,
                            "reasoning_output_tokens": 0,
                            "total_tokens": 27,
                        }
                    },
                },
            },
        ],
    )
    write_jsonl(
        sessions_dir / "rollout-2026-03-15T10-00-00-sess-002.jsonl",
        [
            {
                "timestamp": "2026-03-15T10:00:00.000Z",
                "type": "event_msg",
                "payload": {
                    "type": "token_count",
                    "info": {
                        "total_token_usage": {
                            "input_tokens": 15,
                            "cached_input_tokens": 0,
                            "output_tokens": 5,
                            "reasoning_output_tokens": 0,
                            "total_tokens": 20,
                        }
                    },
                },
            }
        ],
    )


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")


class tempfile_directory:
    def __enter__(self) -> Path:
        import tempfile

        self._tmp = tempfile.TemporaryDirectory()
        return Path(self._tmp.name)

    def __exit__(self, exc_type, exc, tb) -> None:
        self._tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
