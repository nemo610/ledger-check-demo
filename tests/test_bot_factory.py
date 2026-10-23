import tempfile
import unittest
from pathlib import Path

from agent_economy.bot_factory import ARCHETYPES, build_registry, write_registry


class BotFactoryTests(unittest.TestCase):
    def test_generates_one_thousand_unique_slots_by_default(self):
        result = build_registry()
        ids = [bot["bot_id"] for bot in result["bots"]]
        self.assertEqual(len(ids), 1000)
        self.assertEqual(len(set(ids)), 1000)
        self.assertFalse(result["live_execution_enabled"])
        self.assertEqual(result["revenue_claim"], "none")

    def test_archetypes_cycle_without_copying_code(self):
        result = build_registry(count=len(ARCHETYPES) * 2)
        self.assertEqual(
            [bot["role"] for bot in result["bots"][:len(ARCHETYPES)]],
            [item.role for item in ARCHETYPES],
        )
        self.assertEqual(result["bots"][0]["role"], result["bots"][len(ARCHETYPES)]["role"])

    def test_all_slots_blocked_without_verified_provider(self):
        result = build_registry(count=5)
        self.assertTrue(all(bot["status"] == "blocked_no_verified_provider" for bot in result["bots"]))
        self.assertTrue(all(bot["live_execution_enabled"] is False for bot in result["bots"]))

    def test_invalid_counts_fail_closed(self):
        for value in (0, 1001, -1, True, 1.5):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    build_registry(count=value)

    def test_writes_valid_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "output" / "registry.json"
            result = write_registry(str(path), count=7)
            self.assertTrue(path.exists())
            self.assertEqual(len(__import__("json").loads(path.read_text())["bots"]), 7)
            self.assertEqual(result["requested_bot_slots"], 7)


if __name__ == "__main__":
    unittest.main()
