import hashlib
import json
import unittest

from agent_economy.job_spec import MAX_JOB_SPEC_BYTES, JobSpecError, verify_job_spec


class JobSpecVerificationTests(unittest.TestCase):
    def test_accepts_exact_pinned_json_bytes_but_never_approves_execution(self):
        raw = b'{"title":"Validate a CSV","deliverable":"JSON report"}'
        result = verify_job_spec(raw, hashlib.sha256(raw).hexdigest())
        self.assertEqual(result["spec"]["title"], "Validate a CSV")
        self.assertEqual(result["sha256"], hashlib.sha256(raw).hexdigest())
        self.assertFalse(result["trusted"])
        self.assertFalse(result["execution_approved"])

    def test_rejects_modified_bytes_even_if_json_still_parses(self):
        raw = b'{"title":"changed"}'
        with self.assertRaisesRegex(JobSpecError, "does not match"):
            verify_job_spec(raw, "a" * 64)

    def test_rejects_bad_hash_format(self):
        with self.assertRaisesRegex(JobSpecError, "64-character"):
            verify_job_spec(b'{"title":"ok"}', "abc123")

    def test_rejects_invalid_utf8_and_invalid_json(self):
        for raw in (b"\xff", b'{"bad":}'):
            with self.subTest(raw=raw):
                with self.assertRaisesRegex(JobSpecError, "valid UTF-8 JSON"):
                    verify_job_spec(raw, hashlib.sha256(raw).hexdigest())

    def test_rejects_non_object_root(self):
        raw = b'["not-an-object"]'
        with self.assertRaisesRegex(JobSpecError, "root must be an object"):
            verify_job_spec(raw, hashlib.sha256(raw).hexdigest())

    def test_rejects_empty_and_oversized_specs(self):
        with self.assertRaisesRegex(JobSpecError, "empty"):
            verify_job_spec(b"", hashlib.sha256(b"").hexdigest())
        raw = b" " * (MAX_JOB_SPEC_BYTES + 1)
        with self.assertRaisesRegex(JobSpecError, "size limit"):
            verify_job_spec(raw, hashlib.sha256(raw).hexdigest())

    def test_rejects_non_bytes_input_and_invalid_size_configuration(self):
        with self.assertRaisesRegex(JobSpecError, "raw bytes"):
            verify_job_spec('{"title":"ok"}', "a" * 64)
        with self.assertRaisesRegex(JobSpecError, "max_bytes"):
            verify_job_spec(b'{"title":"ok"}', hashlib.sha256(b'{"title":"ok"}').hexdigest(), max_bytes=0)


if __name__ == "__main__":
    unittest.main()
