"""Pure offline catalogue comparison tests: these prove no runtime authority."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "hk2"))
import hk2_bundle_preview as preview


def raw(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value):
    return hashlib.sha256(value).hexdigest()


class PreviewTest(unittest.TestCase):
    def setUp(self):
        self.manifest = {"schema": "hk2_job/v1", "phase": "HK1", "kind": "engineering", "production": False,
                         "argv": ["python3", "setup.py", "a b"]}
        self.data = raw(self.manifest)
        self.entry = {"manifest_sha256": digest(self.data), "argv_sha256": preview.command_digest(self.manifest["argv"]),
                      "phase": "HK1", "kind": "engineering", "production": False, "task": "setup"}

    def match(self, data=None, entries=None):
        catalogue = raw({"schema": "hk2_catalogue_preview/v1", "entries": [self.entry] if entries is None else entries})
        return preview.preview_match(self.data if data is None else data, catalogue, digest(catalogue))

    def test_result_is_never_authority(self):
        result = self.match()
        self.assertEqual(result["status"], "PREVIEW_ONLY")
        self.assertFalse(result["submission_authorized"])
        self.assertFalse(result["immutability_verified"])
        self.assertFalse(result["review_authority_verified"])

    def test_byte_change_and_catalogue_mismatch_refused(self):
        with self.assertRaises(preview.PreviewError): self.match(self.data + b" ")
        with self.assertRaises(preview.PreviewError): preview.preview_match(self.data, b"{}", "0" * 64)
        duplicate = dict(self.entry)
        with self.assertRaises(preview.PreviewError): self.match(entries=[self.entry, duplicate])

    def test_command_boundaries_and_misclassification(self):
        self.assertNotEqual(preview.command_digest(["a", "b c"]), preview.command_digest(["a b", "c"]))
        self.entry["argv_sha256"] = "0" * 64
        with self.assertRaises(preview.PreviewError): self.match()
        self.entry["argv_sha256"] = preview.command_digest(self.manifest["argv"])
        self.entry["task"] = "closed_loop"
        with self.assertRaises(preview.PreviewError): self.match()

    def test_changed_phase_and_evidence_are_not_hidden_by_kind(self):
        self.entry["phase"] = "HK6"
        with self.assertRaises(preview.PreviewError): self.match()
        self.entry["phase"] = "HK1"
        self.entry["kind"] = "evidence"
        with self.assertRaises(preview.PreviewError): self.match()

    def test_duplicate_json_fields_refused(self):
        data = b'{"schema":"hk2_job/v1","phase":"HK1","phase":"HK6"}'
        self.entry["manifest_sha256"] = digest(data)
        with self.assertRaises(preview.PreviewError): self.match(data)

    def test_self_consistent_forged_catalogue_cannot_authorize_work(self):
        # Matching bytes cannot prove the catalogue's semantic classification.
        # The fictitious command suggests closed-loop work but the untrusted
        # catalogue falsely calls it setup.  A match remains only a preview.
        self.manifest["argv"] = ["python3", "hypothetical_closed_loop.py"]
        self.data = raw(self.manifest)
        self.entry["manifest_sha256"] = digest(self.data)
        self.entry["argv_sha256"] = preview.command_digest(self.manifest["argv"])
        self.entry["task"] = "setup"
        result = self.match()
        self.assertEqual(result["status"], "PREVIEW_ONLY")
        self.assertFalse(result["submission_authorized"])
        self.assertFalse(result["review_authority_verified"])
        self.assertFalse(result["immutability_verified"])


if __name__ == "__main__":
    unittest.main()
