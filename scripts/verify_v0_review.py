"""Verify a review ZIP without extracting or executing anything inside it."""

import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import stat
from urllib.parse import unquote, urlsplit
import zipfile


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        self.links.extend(value for key, value in attrs if key in ("href", "src") and value)


def verify(path, expected_sha256=None):
    with Path(path).open("rb") as stream:
        archive_hash = hashlib.file_digest(stream, "sha256").hexdigest()
    if expected_sha256 is not None:
        if not re.fullmatch(r"[0-9a-fA-F]{64}", expected_sha256) or archive_hash != expected_sha256.lower():
            raise ValueError("Archive SHA-256 does not match the expected value")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate archive member names")
        for item in archive.infolist():
            name = item.filename
            parts = PurePosixPath(name).parts
            if (not parts or name.startswith("/") or "\\" in name or ":" in parts[0]
                or ".." in parts or posixpath.normpath(name) != name
                or item.is_dir() or stat.S_ISLNK(item.external_attr >> 16)):
                raise ValueError(f"Unsupported archive member: {name}")
        manifest = json.loads(archive.read("MANIFEST.json"))
        if manifest["format"] != "bitgenesis-review-1":
            raise ValueError("Unsupported review manifest")
        files = manifest["files"]
        if not files or set(names) != set(files) | {"MANIFEST.json", "START-HERE.txt"}:
            raise ValueError("Archive and manifest file lists differ")
        links_checked = pages = 0
        for name, record in files.items():
            if not name.startswith("bitgenesis/"):
                raise ValueError("Manifest payload outside bitgenesis directory")
            if archive.getinfo(name).file_size != record["bytes"]:
                raise ValueError(f"File size mismatch: {name}")
            with archive.open(name) as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            if digest != record["sha256"]:
                raise ValueError(f"File hash mismatch: {name}")
            if name.endswith(".html"):
                pages += 1
                parser = Links()
                parser.feed(archive.read(name).decode("utf-8"))
                for link in parser.links:
                    url = urlsplit(link)
                    if url.scheme or url.netloc or not url.path:
                        continue
                    target = posixpath.normpath(posixpath.join(posixpath.dirname(name), unquote(url.path)))
                    if target not in files:
                        raise ValueError(f"Missing local HTML target: {name} -> {link}")
                    links_checked += 1
        return {"status": "verified", "sha256": archive_hash,
                "expected_hash_matched": expected_sha256 is not None,
                "source_commit": manifest["git_commit"], "files": len(files),
                "html_pages": pages, "local_html_targets": links_checked,
                "scope": "Stored file integrity and static HTML targets; no scripts executed or scientific claims validated."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--expected-sha256")
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.archive, args.expected_sha256), indent=2))
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as error:
        parser.error(str(error))
