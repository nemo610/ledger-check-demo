import json
import os
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from unittest.mock import patch

from agent_economy import monitor


class MonitorTests(unittest.TestCase):
    def test_requires_wallet_without_network_access(self):
        stderr = StringIO()
        with patch.dict(os.environ, {}, clear=True), redirect_stderr(stderr):
            code = monitor.main()
        self.assertEqual(code, 2)
        self.assertIn("AGENC_WALLET", stderr.getvalue())

    @patch("agent_economy.monitor.fetch_settled_earnings")
    def test_reports_counts_without_claiming_settlement(self, fetch):
        fetch.return_value = {
            "referrer": {"hires": [{"id": "h1"}]},
            "operator": {"hires": []},
        }
        stdout = StringIO()
        with patch.dict(os.environ, {"AGENC_WALLET": "11111111111111111111111111111111"}), redirect_stdout(stdout):
            code = monitor.main()
        payload = json.loads(stdout.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(payload["referrer_hires_reported"], 1)
        self.assertEqual(payload["operator_hires_reported"], 0)
        self.assertFalse(payload["settlement_verified"])
        self.assertEqual(payload["mode"], "read_only")


if __name__ == "__main__":
    unittest.main()
