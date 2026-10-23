import unittest
from unittest.mock import patch

from agent_economy.agenc_readiness import ReadinessError, inspect_wallet

WALLET = "CG8BV7x2jWnFkfnV4WMkjLLi3aj6Q2Hu5M8t98MLA391"


class AgenCReadinessTests(unittest.TestCase):
    def test_registered_agent_with_hireable_listing_is_not_called_paid_or_signed(self):
        payloads = {
            f"/api/agents?authority={WALLET}&page=1&pageSize=100": {
                "items": [{"pda": "agent-pda", "authority": WALLET, "status": "active",
                           "stake": "10000000", "reputation": 0, "tasksCompleted": 0}],
                "total": 1,
            },
            f"/api/listings?wallet={WALLET}&page=1&pageSize=100": {
                "items": [{"pda": "listing-pda", "authority": WALLET, "name": "CSV QA",
                           "state": 0, "priceLamports": "10000000"}], "total": 1,
            },
            f"/api/listings?wallet={WALLET}&hireable=1&page=1&pageSize=100": {
                "items": [{"pda": "listing-pda", "name": "CSV QA", "state": 0}], "total": 1,
            },
            f"/api/stores?wallet={WALLET}&optional=1": {"store": {"handle": "nemo"}},
        }
        report = inspect_wallet(WALLET, getter=lambda path: payloads[path])
        self.assertEqual(report["status"], "PROVIDER_API_READY_REQUIRES_RUNTIME_AND_SIGNED_FLOW_TEST")
        self.assertTrue(report["readiness"]["worker_registered"])
        self.assertTrue(report["readiness"]["provider_listing_hireable"])
        self.assertEqual(report["transactions_signed"], 0)
        self.assertEqual(report["claims_made"], 0)
        self.assertEqual(report["payments_made"], 0)

    def test_unregistered_agent_and_no_listing_are_reported_as_pending(self):
        payloads = {
            f"/api/agents?authority={WALLET}&page=1&pageSize=100": {"items": [], "total": 0},
            f"/api/listings?wallet={WALLET}&page=1&pageSize=100": {"items": [], "total": 0},
            f"/api/listings?wallet={WALLET}&hireable=1&page=1&pageSize=100": {"items": [], "total": 0},
            f"/api/stores?wallet={WALLET}&optional=1": {"store": None},
        }
        report = inspect_wallet(WALLET, getter=lambda path: payloads[path])
        self.assertEqual(report["status"], "REGISTRATION_OR_LISTING_PENDING")
        self.assertFalse(report["readiness"]["worker_registered"])
        self.assertFalse(report["readiness"]["provider_listing_hireable"])

    def test_api_failure_is_fail_closed_and_does_not_claim_ready(self):
        def fail(path):
            raise ReadinessError("offline")
        report = inspect_wallet(WALLET, getter=fail)
        self.assertEqual(report["status"], "INCOMPLETE_API_CHECK")
        self.assertFalse(report["readiness"]["worker_registered"])

    def test_rejects_invalid_wallet(self):
        with self.assertRaises(ValueError):
            inspect_wallet("not-a-wallet", getter=lambda path: {})

    def test_bad_response_schema_is_not_treated_as_empty(self):
        paths = {
            f"/api/agents?authority={WALLET}&page=1&pageSize=100": {"items": []},
            f"/api/listings?wallet={WALLET}&page=1&pageSize=100": {"items": []},
            f"/api/listings?wallet={WALLET}&hireable=1&page=1&pageSize=100": {"items": []},
            f"/api/stores?wallet={WALLET}&optional=1": {"store": None},
        }
        report = inspect_wallet(WALLET, getter=lambda path: paths[path])
        self.assertEqual(report["checks"]["agent_registration"]["status"], "ok")
        self.assertFalse(report["readiness"]["worker_registered"])


if __name__ == "__main__":
    unittest.main()
