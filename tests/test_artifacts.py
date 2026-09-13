import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from bitgenesis.v0.artifacts import write_json_atomic


class ArtifactCheckpointTests(unittest.TestCase):
    def test_streamed_json_preserves_existing_file_format(self):
        value = {"label": "谱系", "records": [{"id": i, "parent": None if i == 0 else i - 1,
                  "values": [i / 7, True, "\\\"\n"]} for i in range(1000)]}
        expected = (json.dumps(value, indent=2, allow_nan=False) + "\n").encode("utf-8")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "records.json"
            write_json_atomic(path, value)
            self.assertEqual(path.read_bytes(), expected)

    def test_failed_replacement_preserves_previous_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "metadata.json"
            write_json_atomic(path, {"status": "running", "completed_steps": 10})
            previous = path.read_bytes()
            with patch("bitgenesis.v0.artifacts.os.replace", side_effect=OSError("simulated failure")):
                with self.assertRaises(OSError):
                    write_json_atomic(path, {"status": "complete", "completed_steps": 100})
            self.assertEqual(path.read_bytes(), previous)
            self.assertEqual(list(Path(directory).iterdir()), [path])
            write_json_atomic(path, {"status": "complete", "completed_steps": 100})
            self.assertEqual(json.loads(path.read_text())["completed_steps"], 100)

    def test_nonfinite_values_do_not_damage_existing_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "summary.json"
            write_json_atomic(path, {"mean_genome": None})
            previous = path.read_bytes()
            with self.assertRaises(ValueError):
                write_json_atomic(path, {"mean_genome": float("nan")})
            self.assertEqual(path.read_bytes(), previous)
            self.assertEqual(list(Path(directory).iterdir()), [path])


if __name__ == "__main__":
    unittest.main()
