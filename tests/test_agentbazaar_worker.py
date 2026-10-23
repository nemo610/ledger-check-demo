import unittest

from agent_economy.agentbazaar_worker import process_job_payload


class AgentBazaarWorkerPayloadTests(unittest.TestCase):
    def test_valid_csv_payload(self):
        result = process_job_payload({
            "filename": "example.csv",
            "format": "csv",
            "content": "id,name\n1,Ada\n",
        })
        self.assertTrue(result["valid"])
        self.assertFalse(result["stored"])
        self.assertEqual(result["format"], "csv")

    def test_valid_json_payload(self):
        result = process_job_payload({
            "filename": "example.json",
            "format": "json",
            "content": '{"ok": true}',
        })
        self.assertTrue(result["valid"])
        self.assertEqual(result["root_type"], "dict")

    def test_rejects_unstructured_payload(self):
        with self.assertRaises(ValueError):
            process_job_payload("validate this file")

    def test_rejects_extra_fields(self):
        with self.assertRaises(ValueError):
            process_job_payload({
                "filename": "example.csv",
                "format": "csv",
                "content": "id\n1\n",
                "url": "https://example.com/file.csv",
            })


if __name__ == "__main__":
    unittest.main()
