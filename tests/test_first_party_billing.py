import unittest

from agent_economy.first_party_billing import process_service_charges


def policy(**overrides):
    item = {
        "policy_id": "qa-hour-v1",
        "service_id": "data-qa",
        "policy_version": "v1",
        "currency": "USD",
        "unit_price": "2.50",
        "enabled": True,
    }
    item.update(overrides)
    return item


def event(**overrides):
    item = {
        "event_id": "evt-1",
        "service_id": "data-qa",
        "customer_agent_id": "buyer-agent",
        "provider_agent_id": "nemo-data-qa",
        "idempotency_key": "request-001",
        "usage_units": "2",
        "currency": "USD",
        "policy_version": "v1",
        "status": "CONFIRMED",
        "source_reference": "synthetic-test",
    }
    item.update(overrides)
    return item


class FirstPartyBillingTests(unittest.TestCase):
    def test_confirmed_usage_creates_proposal_not_settlement(self):
        result = process_service_charges([event()], [policy()])[0]
        self.assertEqual(result["amount"], "5.00")
        self.assertEqual(result["status"], "PROPOSED")
        self.assertFalse(result["settlement_verified"])
        self.assertEqual(result["event_type"], "first_party_service_charge")

    def test_policy_disabled_by_default(self):
        result = process_service_charges([event()], [policy(enabled=False)])[0]
        self.assertEqual(result["status"], "POLICY_DISABLED")
        self.assertEqual(result["amount"], "0.00")

    def test_unconfirmed_usage_is_not_billable(self):
        result = process_service_charges([event(status="OBSERVED")], [policy()])[0]
        self.assertEqual(result["status"], "USAGE_NOT_CONFIRMED")

    def test_duplicate_idempotency_key_is_rejected(self):
        results = process_service_charges(
            [event(), event(event_id="evt-2")], [policy()]
        )
        self.assertEqual(results[0]["status"], "PROPOSED")
        self.assertEqual(results[1]["status"], "DUPLICATE_IDEMPOTENCY_KEY")

    def test_duplicate_event_id_is_rejected(self):
        results = process_service_charges(
            [event(), event(idempotency_key="request-002")], [policy()]
        )
        self.assertEqual(results[1]["status"], "DUPLICATE_EVENT_ID")

    def test_self_charge_is_rejected(self):
        result = process_service_charges(
            [event(customer_agent_id="nemo-data-qa")], [policy()]
        )[0]
        self.assertEqual(result["status"], "SELF_CHARGE_REJECTED")

    def test_ambiguous_policy_fails_closed(self):
        result = process_service_charges([event()], [policy(), policy(policy_id="second")])[0]
        self.assertEqual(result["status"], "AMBIGUOUS_POLICY")

    def test_invalid_units_are_rejected(self):
        with self.assertRaises(ValueError):
            process_service_charges([event(usage_units="0")], [policy()])

    def test_currency_mismatch_is_rejected(self):
        result = process_service_charges([event(currency="ARS")], [policy()])[0]
        self.assertEqual(result["status"], "CURRENCY_MISMATCH")

    def test_reversal_is_a_separate_negative_proposal(self):
        original = event()
        reversal = event(
            event_id="evt-reversal",
            idempotency_key="request-reversal-001",
            status="REVERSED",
            reverses_event_id="evt-1",
        )
        results = process_service_charges([original, reversal], [policy()])
        self.assertEqual(results[1]["event_type"], "first_party_service_reversal")
        self.assertEqual(results[1]["amount"], "-5.00")
        self.assertEqual(results[1]["status"], "REVERSAL_PROPOSED")
        self.assertFalse(results[1]["settlement_verified"])

    def test_reversal_without_original_is_rejected(self):
        result = process_service_charges(
            [event(status="REVERSED", reverses_event_id="missing")], [policy()]
        )[0]
        self.assertEqual(result["status"], "INVALID_REVERSAL_REFERENCE")

    def test_duplicate_reversal_is_rejected(self):
        original = event()
        reverse1 = event(event_id="rev-1", idempotency_key="reverse-1",
                         status="REVERSED", reverses_event_id="evt-1")
        reverse2 = event(event_id="rev-2", idempotency_key="reverse-2",
                         status="REVERSED", reverses_event_id="evt-1")
        results = process_service_charges([original, reverse1, reverse2], [policy()])
        self.assertEqual(results[2]["status"], "DUPLICATE_REVERSAL")


if __name__ == "__main__":
    unittest.main()
