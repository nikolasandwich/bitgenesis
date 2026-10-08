from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from bitgenesis.v0.runner import provenance


class ProvenanceTests(unittest.TestCase):
    def test_extracted_source_does_not_borrow_enclosing_repository(self):
        with tempfile.TemporaryDirectory() as temporary:
            outer = Path(temporary)
            (outer / ".git").mkdir()
            source = outer / "extracted"
            module = source / "src/bitgenesis/v0/runner.py"
            module.parent.mkdir(parents=True)
            module.write_text("# extracted source\n")
            with patch("bitgenesis.v0.runner.__file__", str(module)), patch(
                    "bitgenesis.v0.runner.subprocess.check_output", return_value="outer-commit") as git:
                result = provenance()
            self.assertEqual(result["installation_kind"], "source")
            self.assertIsNone(result["git_commit"])
            self.assertIsNone(result["git_dirty"])
            self.assertIn("src/bitgenesis/v0/runner.py", result["source_sha256"])
            git.assert_not_called()

    def test_source_worktree_git_file_remains_supported(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary)
            (source / ".git").write_text("gitdir: external-worktree-metadata\n")
            module = source / "src/bitgenesis/v0/runner.py"
            module.parent.mkdir(parents=True)
            module.write_text("# source worktree\n")
            with patch("bitgenesis.v0.runner.__file__", str(module)), patch(
                    "bitgenesis.v0.runner.subprocess.check_output", side_effect=["", "own-commit"]):
                result = provenance()
            self.assertEqual(result["git_commit"], "own-commit")
            self.assertFalse(result["git_dirty"])
