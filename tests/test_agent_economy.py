import unittest
from agent_economy.ledger import FeePolicy, ServiceEvent, calculate_commission, process_events


class AgentEconomyTests(unittest.TestCase):
    def setUp(self):
        self.policy = FeePolicy("p1", "market", "0.10", "USD", True)
        self.event = ServiceEvent("e1", "market", "agent-a", "agent-b", "12.50", "USD", "CONFIRMED")

    def test_calculates_decimal_fee(self):
        result = calculate_commission(self.event, self.policy)
        self.assertEqual(result["commission_amount"], "1.25")
        self.assertEqual(result["commission_status"], "PROPOSED")
        self.assertFalse(result["settlement_verified"])

    def test_observed_event_not_eligible(self):
        event = ServiceEvent("e2", "market", "agent-a", "agent-b", "12.50", "USD", "OBSERVED")
        self.assertEqual(calculate_commission(event, self.policy)["commission_amount"], "0.00")

    def test_disabled_policy_fails_closed(self):
        policy = FeePolicy("p1", "market", "0.10", "USD", False)
        self.assertEqual(calculate_commission(self.event, policy)["commission_status"], "NOT_ELIGIBLE")

    def test_self_referral_not_eligible(self):
        event = ServiceEvent("e3", "market", "same", "same", "12.50", "USD", "CONFIRMED")
        self.assertEqual(calculate_commission(event, self.policy)["commission_amount"], "0.00")

    def test_duplicate_event_id_is_idempotent(self):
        event = {"event_id":"x", "provider_id":"market", "payer_agent_id":"a",
                 "provider_agent_id":"b", "gross_amount":"20", "currency":"USD", "status":"CONFIRMED"}
        policy = {"policy_id":"p", "provider_id":"market", "rate":"0.1", "currency":"USD", "enabled":True}
        result = process_events([event, event], [policy])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["commission_amount"], "2.00")

    def test_no_policy_means_no_commission(self):
        event = {"event_id":"x", "provider_id":"unknown", "payer_agent_id":"a",
                 "provider_agent_id":"b", "gross_amount":"20", "currency":"USD", "status":"SETTLED"}
        self.assertEqual(process_events([event], [])[0]["commission_status"], "NO_POLICY")

    def test_rejects_negative_amount(self):
        with self.assertRaises(ValueError):
            ServiceEvent.from_dict({"event_id":"x", "provider_id":"m", "payer_agent_id":"a",
              "provider_agent_id":"b", "gross_amount":"-1", "currency":"USD", "status":"CONFIRMED"})

    def test_rejects_bad_status(self):
        with self.assertRaises(ValueError):
            ServiceEvent.from_dict({"event_id":"x", "provider_id":"m", "payer_agent_id":"a",
              "provider_agent_id":"b", "gross_amount":"1", "currency":"USD", "status":"PAID"})

if __name__ == "__main__":
    unittest.main()
