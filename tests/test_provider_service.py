import json
import unittest
from agent_economy.provider_service import app, validate_payload

class ProviderServiceTests(unittest.TestCase):
    def test_valid_csv(self):
        r=validate_payload({"filename":"data.csv","format":"csv","content":"id,name\n1,Ada\n"})
        self.assertTrue(r["valid"]); self.assertEqual(r["data_rows"],1); self.assertEqual(len(r["sha256"]),64)
        self.assertFalse(r["stored"]); self.assertFalse(r["settlement_verified"])
    def test_csv_findings(self):
        r=validate_payload({"filename":"data.csv","format":"csv","content":"id,ID,name\n1,2\n"})
        codes={f["code"] for f in r["findings"]}
        self.assertIn("DUPLICATE_COLUMN",codes); self.assertIn("ROW_WIDTH_MISMATCH",codes); self.assertFalse(r["valid"])
    def test_json(self):
        self.assertTrue(validate_payload({"filename":"x.json","format":"json","content":'{"ok":true}'})["valid"])
        r=validate_payload({"filename":"x.json","format":"json","content":'{"ok":'})
        self.assertFalse(r["valid"]); self.assertEqual(r["findings"][0]["code"],"JSON_PARSE_ERROR")
    def test_rejects_path_format_and_oversize(self):
        with self.assertRaises(ValueError): validate_payload({"filename":"../secret.csv","format":"csv","content":"a\n1"})
        with self.assertRaises(ValueError): validate_payload({"filename":"x","format":"xml","content":"x"})
        with self.assertRaises(OverflowError): validate_payload({"filename":"x.json","format":"json","content":" "*200000})
    def test_health_and_404(self):
        for path,expected in [("/health","200 OK"),("/bad","404 Not Found")]:
            got={}; body=b"".join(app({"REQUEST_METHOD":"GET","PATH_INFO":path},lambda status,headers:got.update(status=status,headers=headers)))
            self.assertEqual(got["status"],expected); self.assertIsInstance(json.loads(body),dict)
if __name__=="__main__": unittest.main()
