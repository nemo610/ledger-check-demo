import unittest

from agent_economy.scalable_bot_fleet import (
    DEFAULT_FLEET_SIZE,
    BotSpec,
    evaluate_batch,
    evaluate_candidate,
    iter_bot_specs,
)


class FakeRiskEngine:
    def __init__(self):
        self.calls = []

    def evaluar_orden(self, **kwargs):
        self.calls.append(kwargs)
        return {"aprobada": True, "motivo": "test only"}


class ScalableBotFleetTests(unittest.TestCase):
    def test_default_fleet_is_one_million_and_lazy(self):
        bots = iter_bot_specs()
        self.assertEqual(DEFAULT_FLEET_SIZE, 1_000_000)
        self.assertEqual(next(bots).bot_id, "nemo-risk-bot-0000001")
        self.assertEqual(next(iter_bot_specs(start=999_999)).bot_id, "nemo-risk-bot-1000000")

    def test_ids_are_stable_and_rules_cycle(self):
        bots = list(iter_bot_specs(12))
        self.assertEqual(len({b.bot_id for b in bots}), 12)
        self.assertEqual(bots[0].sizing_rule, bots[6].sizing_rule)

    def test_invalid_fleet_ranges_rejected(self):
        for kwargs in ({"count": 0}, {"count": 1_000_001}, {"count": True},
                       {"count": 2, "start": -1}, {"count": 2, "start": 999_999}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                list(iter_bot_specs(**kwargs))

    def test_candidate_is_passed_to_risk_engine(self):
        engine = FakeRiskEngine()
        bot = next(iter_bot_specs(1))
        result = evaluate_candidate(engine, bot, {
            "precio_actual": 100.0,
            "capital_disponible": 1_000.0,
            "drawdown_actual": -0.02,
        })
        self.assertEqual(len(engine.calls), 1)
        self.assertEqual(engine.calls[0]["regla_sizing"], bot.sizing_rule)
        self.assertTrue(result["risk_decision"]["aprobada"])
        self.assertFalse(result["order_submitted"])
        self.assertFalse(result["live_execution_enabled"])

    def test_missing_inputs_fail_closed(self):
        engine = FakeRiskEngine()
        bot = next(iter_bot_specs(1))
        with self.assertRaises(ValueError):
            evaluate_candidate(engine, bot, {"precio_actual": 100})
        self.assertEqual(engine.calls, [])

    def test_live_bot_spec_rejected(self):
        engine = FakeRiskEngine()
        bot = BotSpec("unsafe", 0, "BASE_50", live_execution_enabled=True)
        with self.assertRaises(ValueError):
            evaluate_candidate(engine, bot, {"precio_actual": 1, "capital_disponible": 10})

    def test_batch_is_bounded_and_calls_engine(self):
        engine = FakeRiskEngine()
        candidates = [
            {"precio_actual": 10, "capital_disponible": 100}
            for _ in range(5)
        ]
        results = evaluate_batch(engine, candidates, max_items=3)
        self.assertEqual(len(results), 3)
        self.assertEqual(len(engine.calls), 3)
        self.assertTrue(all(item["order_submitted"] is False for item in results))

    def test_batch_limit_cannot_exceed_ten_thousand(self):
        with self.assertRaises(ValueError):
            evaluate_batch(FakeRiskEngine(), [], max_items=10_001)


if __name__ == "__main__":
    unittest.main()
