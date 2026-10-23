import io
import json
import unittest
from agent_economy.provider_service import app, validate_payload

def call_app(method, path, payload=None):
    raw = b"" if payload is None else json.dumps(payload).encode("utf-8")
    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "CONTENT_TYPE": "application/json",
        "CONTENT_LENGTH": str(len(raw)),
        "REMOTE_ADDR": "test-client-" + path,
        "wsgi.input": io.BytesIO(raw),
    }
    got = {}
    body = b"".join(app(environ, lambda status, headers: got.update(status=status, headers=headers)))
    return got["status"], json.loads(body)

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
            got, body = call_app("GET",path)
            self.assertEqual(got,expected); self.assertIsInstance(body,dict)
    def test_agentbazaar_webhook_valid_csv(self):
        status, body = call_app("POST","/",{
            "task":"Validate this CSV",
            "payload":{"filename":"sample.csv","format":"csv","content":"id,name\n1,Ada\n"}
        })
        self.assertEqual(status,"200 OK")
        self.assertEqual(body["task_status"],"completed")
        self.assertTrue(body["result"]["valid"])
        self.assertFalse(body["result"]["stored"])
    def test_agentbazaar_webhook_rejects_missing_payload(self):
        status, body = call_app("POST","/",{"task":"Validate a file"})
        self.assertEqual(status,"400 Bad Request")
        self.assertEqual(body["error"],"invalid_request")
    def test_direct_validate_route_unchanged(self):
        status, body = call_app("POST","/v1/validate",{
            "filename":"sample.json","format":"json","content":'{"ok":true}'
        })
        self.assertEqual(status,"200 OK")
        self.assertTrue(body["valid"])
        self.assertEqual(body["format"],"json")

if __name__=="__main__": unittest.main()
