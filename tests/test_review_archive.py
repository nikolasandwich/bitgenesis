import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import warnings
import stat
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

    def rewrite_manifest(self, path, transform):
        with zipfile.ZipFile(path) as archive:
            entries = [(item, archive.read(item)) for item in archive.infolist()]
        with zipfile.ZipFile(path, "w") as archive:
            for item, data in entries:
                if item.filename == "MANIFEST.json":
                    data = transform(json.loads(data))
                archive.writestr(item, data)

    def test_manifest_schema_is_checked_before_payload(self):
        def changed(manifest, field, value):
            if field == "record":
                manifest["files"]["bitgenesis/README.md"] = value
            elif field == "bytes":
                manifest["files"]["bitgenesis/README.md"]["bytes"] = value
            else:
                manifest[field] = value
            return json.dumps(manifest)

        cases = [("files", []), ("files", None), ("record", []),
                 ("bytes", 17.0), ("bytes", True), ("bytes", -1),
                 ("git_commit", None), ("git_commit", "")]
        with tempfile.TemporaryDirectory() as directory:
            for field, value in cases:
                with self.subTest(field=field, value=value):
                    path = self.build(Path(directory))
                    self.rewrite_manifest(path, lambda m: changed(m, field, value))
                    with self.assertRaisesRegex(ValueError, "manifest"):
                        verify(path)
            for value in ([], None, 1):
                with self.subTest(top_level=value):
                    path = self.build(Path(directory))
                    self.rewrite_manifest(path, lambda m: json.dumps(value))
                    with self.assertRaisesRegex(ValueError, "manifest"):
                        verify(path)

    def test_duplicate_manifest_keys_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.build(Path(directory))
            self.rewrite_manifest(path, lambda m: json.dumps(m).replace(
                '"bytes": 17', '"bytes": 999, "bytes": 17'))
            with self.assertRaisesRegex(ValueError, "Duplicate.*manifest"):
                verify(path)

    def test_duplicate_and_unsupported_members_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            for name in ("../escape.txt", "/absolute.txt", "bitgenesis/../alias.txt",
                         "bitgenesis/README.md", "bitgenesis/link"):
                with self.subTest(name=name):
                    path = self.build(Path(directory))
                    item = zipfile.ZipInfo(name)
                    if name.endswith("/link"):
                        item.create_system = 3
                        item.external_attr = (stat.S_IFLNK | 0o777) << 16
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", UserWarning)
                        with zipfile.ZipFile(path, "a") as archive:
                            archive.writestr(item, "target")
                    with self.assertRaisesRegex(ValueError, "Duplicate|Unsupported"):
                        verify(path)
