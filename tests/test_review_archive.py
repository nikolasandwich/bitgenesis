import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from scripts.verify_v0_review import verify


class ReviewArchiveTests(unittest.TestCase):
    def build(self, root, *, corrupt=False, missing=False, extra=False):
        files = {"bitgenesis/data/index.html": b'<a href="../README.md">Read</a>',
                 "bitgenesis/README.md": b"Research snapshot"}
        if missing:
            files.pop("bitgenesis/README.md")
        manifest = {"format": "bitgenesis-review-1", "git_commit": "fixture",
                    "files": {name: {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
                              for name, data in files.items()}}
        if corrupt:
            files["bitgenesis/README.md"] = b"Changed snapshot!"
        path = root / "review.zip"
        with zipfile.ZipFile(path, "w") as archive:
            for name, data in files.items():
                archive.writestr(name, data)
            archive.writestr("MANIFEST.json", json.dumps(manifest))
            archive.writestr("START-HERE.txt", "Open data/index.html")
            if extra:
                archive.writestr("bitgenesis/unlisted.txt", "extra")
        return path

    def test_complete_archive_and_external_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.build(Path(directory))
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            result = verify(path, digest)
            self.assertTrue(result["expected_hash_matched"])
            self.assertEqual(result["local_html_targets"], 1)
            with self.assertRaisesRegex(ValueError, "expected value"):
                verify(path, "0" * 64)

    def test_changed_payload_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "mismatch"):
                verify(self.build(Path(directory), corrupt=True))

    def test_missing_link_target_is_rejected_even_with_valid_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "Missing local HTML"):
                verify(self.build(Path(directory), missing=True))

    def test_unlisted_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "file lists differ"):
                verify(self.build(Path(directory), extra=True))
