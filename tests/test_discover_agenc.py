import json
import subprocess
import unittest
from unittest.mock import patch

from agent_economy.discover_agenc import (
    COMMAND,
    DiscoveryError,
    discover_tasks,
)


class DiscoveryTests(unittest.TestCase):
    def test_success_is_read_only_and_preserves_provider_payload(self):
        payload = {"tasks": [{"id": "task-1", "reward": "0.5 SOL"}]}
        completed = subprocess.CompletedProcess(
            args=["agenc-marketplace", *COMMAND],
            returncode=0,
            stdout=json.dumps(payload),
            stderr="",
        )
        with patch("agent_economy.discover_agenc.shutil.which", return_value="/usr/bin/agenc-marketplace"):
            snapshot = discover_tasks(runner=lambda *args, **kwargs: completed)
        self.assertEqual(snapshot["claimable_tasks"], payload)
        self.assertFalse(snapshot["write_operations_enabled"])
        self.assertEqual(snapshot["mode"], "read_only")
        self.assertIn("No task was claimed", snapshot["note"])

    def test_missing_cli_fails_closed(self):
        with patch("agent_economy.discover_agenc.shutil.which", return_value=None):
            with self.assertRaisesRegex(DiscoveryError, "CLI not found"):
                discover_tasks()

    def test_invalid_json_fails_closed(self):
        completed = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="not-json", stderr=""
        )
        with patch("agent_economy.discover_agenc.shutil.which", return_value="/usr/bin/agenc-marketplace"):
            with self.assertRaisesRegex(DiscoveryError, "valid JSON"):
                discover_tasks(runner=lambda *args, **kwargs: completed)

    def test_cli_error_does_not_return_tasks(self):
        completed = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="network unavailable"
        )
        with patch("agent_economy.discover_agenc.shutil.which", return_value="/usr/bin/agenc-marketplace"):
            with self.assertRaisesRegex(DiscoveryError, "network unavailable"):
                discover_tasks(runner=lambda *args, **kwargs: completed)

    def test_timeout_bounds(self):
        with self.assertRaisesRegex(ValueError, "timeout"):
            discover_tasks(timeout=0)


if __name__ == "__main__":
    unittest.main()
