import unittest

from agent_economy.http_service import payload


class HttpServiceTests(unittest.TestCase):
    def test_health_is_ok(self):
        status, data = payload("/health")
        self.assertEqual(status, 200)
        self.assertTrue(data["ok"])

    def test_manifest_is_explicitly_staged(self):
        status, data = payload("/.well-known/agent.json")
        self.assertEqual(status, 200)
        self.assertEqual(data["protocol"], "agenc")
        self.assertFalse(data["worker_enabled"])
        self.assertFalse(data["signing_enabled"])
        self.assertEqual(data["registration_status"], "not_verified")

    def test_ready_fails_closed_until_registration(self):
        status, data = payload("/ready")
        self.assertEqual(status, 503)
        self.assertFalse(data["ready"])

    def test_unknown_path(self):
        status, data = payload("/not-a-route")
        self.assertEqual(status, 404)
        self.assertEqual(data["error"], "not_found")


if __name__ == "__main__":
    unittest.main()
