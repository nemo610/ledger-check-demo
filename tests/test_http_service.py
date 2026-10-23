import unittest

from agent_economy.http_service import payload
from agent_economy.provider_service import validate_payload


class HttpServiceTests(unittest.TestCase):
    def test_health_is_ok(self):
        status, data = payload("/health")
        self.assertEqual(status, 200)
        self.assertTrue(data["ok"])

    def test_manifest_is_explicitly_staged_and_advertises_validation(self):
        status, data = payload("/.well-known/agent.json")
        self.assertEqual(status, 200)
        self.assertEqual(data["protocol"], "agenc")
        self.assertFalse(data["worker_enabled"])
        self.assertFalse(data["signing_enabled"])
        self.assertEqual(data["registration_status"], "not_verified")
        self.assertEqual(data["service_api"]["validation_endpoint"], "/v1/validate")
        self.assertFalse(data["service_api"]["stores_uploads"])
        self.assertFalse(data["service_api"]["performs_payments"])

    def test_ready_fails_closed_until_registration(self):
        status, data = payload("/ready")
        self.assertEqual(status, 503)
        self.assertFalse(data["ready"])

    def test_unknown_path(self):
        status, data = payload("/not-a-route")
        self.assertEqual(status, 404)
        self.assertEqual(data["error"], "not_found")

    def test_valid_csv(self):
        result = validate_payload({"filename": "data.csv", "format": "csv", "content": "id,name\n1,Ada\n"})
        self.assertTrue(result["valid"])
        self.assertEqual(result["data_rows"], 1)
        self.assertFalse(result["stored"])
        self.assertFalse(result["settlement_verified"])

    def test_csv_reports_duplicate_columns_and_bad_row_width(self):
        result = validate_payload({"filename": "data.csv", "format": "csv", "content": "id,ID,name\n1,2\n"})
        codes = {item["code"] for item in result["findings"]}
        self.assertIn("DUPLICATE_COLUMN", codes)
        self.assertIn("ROW_WIDTH_MISMATCH", codes)
        self.assertFalse(result["valid"])

    def test_json_valid_and_invalid(self):
        valid = validate_payload({"filename": "x.json", "format": "json", "content": '{"ok":true}'})
        invalid = validate_payload({"filename": "x.json", "format": "json", "content": '{"ok":'})
        self.assertTrue(valid["valid"])
        self.assertFalse(invalid["valid"])
        self.assertEqual(invalid["findings"][0]["code"], "JSON_PARSE_ERROR")

    def test_rejects_paths_formats_and_oversized_content(self):
        with self.assertRaises(ValueError):
            validate_payload({"filename": "../secret.csv", "format": "csv", "content": "a\n1"})
        with self.assertRaises(ValueError):
            validate_payload({"filename": "x", "format": "xml", "content": "x"})
        with self.assertRaises(OverflowError):
            validate_payload({"filename": "x.json", "format": "json", "content": " " * 200000})


if __name__ == "__main__":
    unittest.main()
