import csv
import json
import tempfile
import unittest
from pathlib import Path

from commission_bot.core import load_offers, make_draft, summarize_events, write_campaigns


class CommissionBotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.offer = {"id": "tool1", "name": "Tool One", "description": "Useful tool.",
                      "audience": "small teams", "affiliate_url": "https://vendor.example/ref/abc",
                      "commission_model": "revenue share", "affiliate_approved": True}

    def tearDown(self):
        self.tmp.cleanup()

    def offers_file(self, offers=None):
        path = self.root / "offers.json"
        path.write_text(json.dumps([self.offer] if offers is None else offers), encoding="utf-8")
        return path

    def test_load_valid_offer(self):
        self.assertEqual(load_offers(self.offers_file())[0]["id"], "tool1")

    def test_reject_unapproved_offer(self):
        offer = {**self.offer, "affiliate_approved": False}
        with self.assertRaisesRegex(ValueError, "no está marcada como aprobada"):
            load_offers(self.offers_file([offer]))

    def test_reject_non_https(self):
        offer = {**self.offer, "affiliate_url": "http://vendor.example/ref"}
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            load_offers(self.offers_file([offer]))

    def test_reject_duplicate_ids(self):
        with self.assertRaisesRegex(ValueError, "duplicado"):
            load_offers(self.offers_file([self.offer, self.offer]))

    def test_draft_has_disclosure_and_link(self):
        draft = make_draft(self.offer)
        self.assertIn("Aviso de afiliación", draft)
        self.assertIn(self.offer["affiliate_url"], draft)

    def test_email_channel(self):
        self.assertIn("Asunto:", make_draft(self.offer, "email"))

    def test_invalid_channel(self):
        with self.assertRaises(ValueError):
            make_draft(self.offer, "auto-post")

    def test_summary_counts_and_commission(self):
        path = self.root / "events.csv"
        path.write_text("event_type,offer_id,amount\nclick,tool1,0\nconversion,tool1,0\ncommission,tool1,4.25\n", encoding="utf-8")
        result = summarize_events(path)
        self.assertEqual(result["tool1"]["clicks"], 1)
        self.assertEqual(result["tool1"]["conversions"], 1)
        self.assertEqual(result["tool1"]["commission"], 4.25)

    def test_bad_csv_schema(self):
        path = self.root / "events.csv"
        path.write_text("foo,bar\nx,y\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "columnas"):
            summarize_events(path)

    def test_negative_commission_rejected(self):
        path = self.root / "events.csv"
        path.write_text("event_type,offer_id,amount\ncommission,tool1,-2\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "negativo"):
            summarize_events(path)

    def test_generate_output(self):
        output = self.root / "nested" / "drafts.md"
        self.assertEqual(write_campaigns(self.offers_file(), output), 1)
        self.assertTrue(output.exists())
        self.assertIn("BORRADOR", output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
