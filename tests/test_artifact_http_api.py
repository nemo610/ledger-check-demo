import hashlib
import json
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from data_qa_agent.artifact_server import ArtifactStore, make_handler


TOKEN = "test-token-that-is-long-enough-for-local-tests-123456"


def report_bytes():
    return json.dumps({
        "schema_version": "1.0",
        "source": {"filename": "sample.csv", "size_bytes": 12, "sha256": "b" * 64},
        "report": {"status": "passed", "findings": []},
    }).encode("utf-8")


class ArtifactHTTPAPITests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        store = ArtifactStore(self.tempdir.name)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(store, TOKEN))
        self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()
        self.port = self.server.server_address[1]

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.server_thread.join(timeout=2)
        self.tempdir.cleanup()

    def request(self, method, path, *, body=None, token=None):
        connection = HTTPConnection("127.0.0.1", self.port, timeout=2)
        headers = {}
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"
        if body is not None:
            headers["Content-Type"] = "application/json"
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        raw = response.read()
        result = (response.status, dict(response.getheaders()), raw)
        connection.close()
        return result

    def test_upload_requires_auth_and_download_hash_is_server_computed(self):
        body = report_bytes()
        status, _, _ = self.request("POST", "/v1/artifacts", body=body)
        self.assertEqual(status, 401)

        status, _, raw = self.request("POST", "/v1/artifacts", body=body, token=TOKEN)
        self.assertEqual(status, 201)
        created = json.loads(raw)
        self.assertEqual(created["sha256"], hashlib.sha256(
            json.dumps(json.loads(body), ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n"
        ).hexdigest())

        status, headers, downloaded = self.request(
            "GET", created["path"], token=TOKEN
        )
        self.assertEqual(status, 200)
        self.assertEqual(headers["ETag"], f'"{created["sha256"]}"')
        self.assertEqual(hashlib.sha256(downloaded).hexdigest(), created["sha256"])

        # The buyer can download with the short-lived signed URL, without the
        # upload API's bearer token. A modified signature must be rejected.
        self.assertIn("download_path", created)
        status, _, signed_download = self.request("GET", created["download_path"])
        self.assertEqual(status, 200)
        self.assertEqual(hashlib.sha256(signed_download).hexdigest(), created["sha256"])
        bad_url = created["download_path"].replace("sig=", "sig=0", 1)
        status, _, _ = self.request("GET", bad_url)
        self.assertEqual(status, 401)

    def test_download_and_delete_require_authentication(self):
        status, _, raw = self.request("POST", "/v1/artifacts", body=report_bytes(), token=TOKEN)
        self.assertEqual(status, 201)
        path = json.loads(raw)["path"]

        status, _, _ = self.request("GET", path)
        self.assertEqual(status, 401)
        status, _, _ = self.request("DELETE", path)
        self.assertEqual(status, 401)

        status, _, _ = self.request("DELETE", path, token=TOKEN)
        self.assertEqual(status, 204)
        status, _, _ = self.request("GET", path, token=TOKEN)
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
