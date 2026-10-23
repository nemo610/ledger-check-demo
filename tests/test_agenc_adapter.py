"""Unit tests for the read-only AgenC adapter; no network calls are made."""
import unittest
from unittest.mock import patch

from agent_economy import agenc_adapter


VALID_WALLET = "11111111111111111111111111111111"


class AgenCAdapterTests(unittest.TestCase):
    @patch("agent_economy.agenc_adapter._get_json")
    def test_returns_provider_hires_without_claiming_verified_settlement(self, get_json):
        get_json.side_effect = [
            {"live": True, "hires": [{"id": "hire-1"}]},
            {"live": True, "hires": []},
        ]
        result = agenc_adapter.fetch_settled_earnings(VALID_WALLET)
        self.assertEqual(result["provider"], "agenc")
        self.assertEqual(result["referrer"]["hires"], [{"id": "hire-1"}])
        self.assertEqual(result["operator"]["hires"], [])
        self.assertFalse(result["settlement_verified"])
        self.assertEqual(get_json.call_count, 2)

    def test_rejects_bank_alias_or_invalid_wallet(self):
        with self.assertRaises(ValueError):
            agenc_adapter.fetch_settled_earnings("donatonuevaesperanza")

    @patch("agent_economy.agenc_adapter._get_json")
    def test_rejects_empty_or_non_live_provider_payload(self, get_json):
        get_json.side_effect = agenc_adapter.AgenCAPIError("not live")
        with self.assertRaises(agenc_adapter.AgenCAPIError):
            agenc_adapter.fetch_settled_earnings(VALID_WALLET)

    @patch("agent_economy.agenc_adapter._get_json")
    def test_valid_empty_hires_is_not_an_error(self, get_json):
        get_json.return_value = {"live": True, "hires": []}
        result = agenc_adapter.fetch_settled_earnings(VALID_WALLET)
        self.assertEqual(result["referrer"]["hires"], [])
        self.assertEqual(result["operator"]["hires"], [])
        self.assertFalse(result["settlement_verified"])

    @patch("agent_economy.agenc_adapter._get_json")
    def test_rejects_malformed_hires(self, get_json):
        get_json.return_value = {"live": True, "hires": {}}
        with self.assertRaises(agenc_adapter.AgenCAPIError):
            agenc_adapter.fetch_settled_earnings(VALID_WALLET)


if __name__ == "__main__":
    unittest.main()
