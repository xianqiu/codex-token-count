from __future__ import annotations

from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import sqlite3
import unittest
from unittest.mock import patch

from codex_token.cli import main


class CliTests(unittest.TestCase):
    def test_default_command_matches_summary_text(self) -> None:
        with tempfile_directory() as tmp_path:
            build_codex_fixture(tmp_path / ".codex")
            write_config(tmp_path)
            output = run_cli(tmp_path)
            self.assertIn("Usage Summary", output)
            self.assertIn("7-Day Usage", output)

    def test_default_command_matches_summary_json(self) -> None:
        with tempfile_directory() as tmp_path:
            build_codex_fixture(tmp_path / ".codex")
            write_config(tmp_path)
            output = run_cli(tmp_path, "--json")
            payload = json.loads(output)
            self.assertEqual(payload["scope"], "summary")
            self.assertEqual(payload["sessions"], 3)

    def test_summary_command_json_includes_usage_and_cost(self) -> None:
        with tempfile_directory() as tmp_path:
            build_codex_fixture(tmp_path / ".codex")
            write_config(tmp_path)
            output = run_cli(tmp_path, "--json", "summary")
            payload = json.loads(output)
            self.assertEqual(payload["scope"], "summary")
            self.assertEqual(payload["sessions"], 3)
            self.assertEqual(payload["projects"], 2)
            self.assertIn("tokens_last_7_days", payload)
            self.assertIn("tokens_last_30_days", payload)
            self.assertEqual(len(payload["trend_rows"]), 7)
            self.assertEqual(payload["usage"]["cached_input_tokens"], 5)
            self.assertIsNotNone(payload["cost"])
            self.assertTrue(all("cost" in row for row in payload["trend_rows"]))

    def test_summary_text_hides_breakdown(self) -> None:
        with tempfile_directory() as tmp_path:
            build_codex_fixture(tmp_path / ".codex")
            write_config(tmp_path)
            output = run_cli(tmp_path, "summary")
            self.assertIn("Usage Summary", output)
            self.assertIn("7-Day Usage", output)
            self.assertIn("Total", output)
            self.assertIn("Tokens", output)
            self.assertIn("Estimated Cost", output)
            self.assertIn("7-Day", output)
            self.assertIn("30-Day", output)
            self.assertIn("Cost", output)
            self.assertNotIn("Breakdown", output)

    def test_trend_command_uses_config_default_days(self) -> None:
        with tempfile_directory() as tmp_path:
            build_codex_fixture(tmp_path / ".codex")
            write_config(tmp_path, trend_days=5)
            output = run_cli(tmp_path, "--json", "trend")
            payload = json.loads(output)
            self.assertEqual(payload["days"], 5)
            self.assertEqual(len(payload["rows"]), 5)

    def test_project_list_json_uses_project_names_only(self) -> None:
        with tempfile_directory() as tmp_path:
            build_codex_fixture(tmp_path / ".codex")
            write_config(tmp_path)
            output = run_cli(tmp_path, "--json", "project")
            payload = json.loads(output)
            self.assertEqual(payload["scope"], "project_list")
            self.assertEqual(payload["limit"], 3)
            self.assertEqual(payload["rows"][0]["project_id"], "/repo/foo/api")
            self.assertEqual(payload["rows"][0]["project_name"], "foo/api")
            self.assertNotIn("cwd", payload["rows"][0])

    def test_project_detail_by_stable_project_id(self) -> None:
        with tempfile_directory() as tmp_path:
            build_codex_fixture(tmp_path / ".codex")
            write_config(tmp_path)
            output = run_cli(tmp_path, "--json", "project", "/repo/foo/api")
            payload = json.loads(output)
            self.assertEqual(payload["scope"], "project_detail")
            self.assertEqual(payload["project"]["project_id"], "/repo/foo/api")
            self.assertEqual(payload["project"]["project_name"], "foo/api")
            self.assertEqual(payload["project"]["cwd"], "/repo/foo/api")
            self.assertEqual(payload["usage"]["total_tokens"], 43)

    def test_project_detail_by_display_name_remains_supported(self) -> None:
        with tempfile_directory() as tmp_path:
            build_codex_fixture(tmp_path / ".codex")
            write_config(tmp_path)
            output = run_cli(tmp_path, "--json", "project", "foo/api")
            payload = json.loads(output)
            self.assertEqual(payload["project"]["project_id"], "/repo/foo/api")

    def test_missing_pricing_returns_null_cost(self) -> None:
        with tempfile_directory() as tmp_path:
            build_codex_fixture(tmp_path / ".codex")
            write_config(tmp_path, include_pricing=False)
            output = run_cli(tmp_path, "--json", "summary")
            payload = json.loads(output)
            self.assertIsNone(payload["cost"])

    def test_config_can_override_codex_home(self) -> None:
        with tempfile_directory() as tmp_path:
            custom_home = tmp_path / "custom-codex"
            build_codex_fixture(custom_home)
            write_config(tmp_path, codex_home="./custom-codex")
            output = run_cli(tmp_path, "--json", "summary")
            payload = json.loads(output)
            self.assertEqual(payload["sessions"], 3)

    def test_summary_excludes_archived_sessions_by_default(self) -> None:
        with tempfile_directory() as tmp_path:
            build_codex_fixture(tmp_path / ".codex", include_archived_session=True)
            write_config(tmp_path)
            output = run_cli(tmp_path, "--json", "summary")
            payload = json.loads(output)
            self.assertEqual(payload["sessions"], 3)
            self.assertEqual(payload["usage"]["total_tokens"], 83)

    def test_summary_can_include_archived_sessions_from_config(self) -> None:
        with tempfile_directory() as tmp_path:
            build_codex_fixture(tmp_path / ".codex", include_archived_session=True)
            write_config(tmp_path, include_archived=True)
            output = run_cli(tmp_path, "--json", "summary")
            payload = json.loads(output)
            self.assertEqual(payload["sessions"], 4)
            self.assertEqual(payload["usage"]["total_tokens"], 98)

    def test_summary_can_use_fallback_config_outside_project_dir(self) -> None:
        with tempfile_directory() as tmp_path:
            config_home = tmp_path / "config-home"
            work_dir = tmp_path / "elsewhere"
            build_codex_fixture(config_home / ".codex")
            write_config(config_home)
            work_dir.mkdir()
            with patch("codex_token.config._fallback_config_candidates", return_value=(config_home / ".codex-token.toml",)):
                output = run_cli(work_dir, "--json", "summary")
            payload = json.loads(output)
            self.assertEqual(payload["scope"], "summary")
            self.assertIsNotNone(payload["cost"])
            self.assertEqual(payload["sessions"], 3)


def run_cli(project_dir: Path, *args: str) -> str:
    buffer = io.StringIO()
    previous_cwd = Path.cwd()
    try:
        os.chdir(project_dir)
        with redirect_stdout(buffer):
            exit_code = main(list(args))
    finally:
        os.chdir(previous_cwd)
    if exit_code != 0:
        raise AssertionError(f"CLI exited with {exit_code}")
    return buffer.getvalue()


def write_config(
    project_dir: Path,
    *,
    trend_days: int = 7,
    include_pricing: bool = True,
    codex_home: str = "./.codex",
    include_archived: bool = False,
) -> None:
    pricing_section = (
        "\n[pricing]\ninput_per_million_usd = 2.5\ncached_input_per_million_usd = 0.25\noutput_per_million_usd = 15.0\n"
        if include_pricing
        else ""
    )
    (project_dir / ".codex-token.toml").write_text(
        f"""[codex]
home = "{codex_home}"

[defaults]
trend_days = {trend_days}
project_limit = 3
include_archived = {"true" if include_archived else "false"}
{pricing_section}
""",
        encoding="utf-8",
    )


def build_codex_fixture(codex_home: Path, *, include_archived_session: bool = False) -> None:
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
                ("sess-001", 1710000000, 1710003600, "/repo/foo/api", "first", 20),
                ("sess-002", 1710000000, 1710007200, "/repo/foo/api", "second", 30),
                ("sess-003", 1710000000, 1710010800, "/repo/bar/api", "third", 40),
                *(
                    [("sess-004", 1710000000, 1710014400, "/repo/archived/api", "archived", 15)]
                    if include_archived_session
                    else []
                ),
            ],
        )
        if include_archived_session:
            connection.execute("UPDATE threads SET archived = 1 WHERE id = 'sess-004'")
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
                            "cached_input_tokens": 5,
                            "output_tokens": 3,
                            "reasoning_output_tokens": 1,
                            "total_tokens": 23,
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
    write_jsonl(
        sessions_dir / "rollout-2026-03-15T10-00-00-sess-003.jsonl",
        [
            {
                "timestamp": "2026-03-15T10:00:00.000Z",
                "type": "event_msg",
                "payload": {
                    "type": "token_count",
                    "info": {
                        "total_token_usage": {
                            "input_tokens": 30,
                            "cached_input_tokens": 0,
                            "output_tokens": 10,
                            "reasoning_output_tokens": 2,
                            "total_tokens": 40,
                        }
                    },
                },
            }
        ],
    )
    if include_archived_session:
        write_jsonl(
            sessions_dir / "rollout-2026-03-15T10-00-00-sess-004.jsonl",
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
                                "output_tokens": 5,
                                "reasoning_output_tokens": 1,
                                "total_tokens": 15,
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
