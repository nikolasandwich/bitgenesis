import csv
import json
from pathlib import Path
import tempfile
import unittest

from bitgenesis.v0.audit import audit
from bitgenesis.v0.engine import Config
from bitgenesis.v0.runner import run


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name) / "run"
        self.summary = run(Config(width=8, height=8, initial_population=12), 50, self.output)

    def test_valid_artifacts_reconcile(self):
        result = audit(self.output)
        self.assertEqual(result["status"], "verified")
        self.assertEqual(result["final_population"], self.summary["population"])

    def test_energy_corruption_is_detected(self):
        path = self.output / "metrics.csv"
        with path.open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        rows[1]["supplied_energy"] = str(int(rows[1]["supplied_energy"]) + 1)
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        with self.assertRaisesRegex(ValueError, "Energy accounting mismatch"):
            audit(self.output)

    def test_missing_lifecycle_event_is_detected(self):
        path = self.output / "events.jsonl"
        lines = path.read_text().splitlines(keepends=True)
        # Remove a newborn birth; either missing-birth or invalid-death ordering must fail.
        index = next(i for i, line in enumerate(lines) if json.loads(line).get("parent_id") is not None)
        path.write_text("".join(lines[:index] + lines[index + 1:]), encoding="utf-8")
        with self.assertRaises(ValueError):
            audit(self.output)

    def test_wrong_parent_is_detected(self):
        path = self.output / "lineage.json"
        records = json.loads(path.read_text())
        child = next(o for o in records if o["parent_id"] is not None)
        child["parent_id"] = 999999
        path.write_text(json.dumps(records), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Missing parent"):
            audit(self.output)

    def test_trait_metrics_are_reconstructed_from_lifecycle(self):
        path = self.output / "metrics.csv"
        with path.open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        rows[1]["mean_genome"] = str(float(rows[1]["mean_genome"]) + 1)
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        with self.assertRaisesRegex(ValueError, "Trait mean mismatch"):
            audit(self.output)

    def test_partial_run_is_not_verified(self):
        path = self.output / "metadata.json"
        metadata = json.loads(path.read_text())
        metadata["status"] = "interrupted"
        path.write_text(json.dumps(metadata), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "not marked complete"):
            audit(self.output)

    def test_incomplete_or_unknown_config_keys_are_rejected(self):
        path = self.output / "metadata.json"
        original = path.read_bytes()
        for missing in (True, False):
            metadata = json.loads(original)
            if missing:
                del metadata["config"]["seed"]
            else:
                metadata["config"]["unused_setting"] = 1
            path.write_text(json.dumps(metadata), encoding="utf-8")
            with self.subTest(missing=missing), self.assertRaisesRegex(ValueError, "configuration keys"):
                audit(self.output)
        path.write_bytes(original)

    def test_noninteger_metadata_is_rejected(self):
        path = self.output / "metadata.json"
        original = path.read_bytes()
        for field, value in (("completed_steps", 50.0), ("requested_steps", 50.0),
                             ("seed", True), ("width", 8.0), ("mutation_probability", 100.0)):
            metadata = json.loads(original)
            target = metadata if field.endswith("steps") else metadata["config"]
            target[field] = value
            path.write_text(json.dumps(metadata), encoding="utf-8")
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "integer"):
                audit(self.output)
        path.write_bytes(original)

    def test_wrong_json_container_has_a_readable_error(self):
        for filename, value in (("metadata.json", []), ("metadata.json", None),
                                ("lineage.json", {}), ("frames.json", {}),
                                ("summary.json", [])):
            path = self.output / filename
            original = path.read_bytes()
            try:
                path.write_text(json.dumps(value), encoding="utf-8")
                with self.subTest(filename=filename, value=value):
                    with self.assertRaisesRegex(ValueError, filename):
                        audit(self.output)
            finally:
                path.write_bytes(original)

    def test_missing_field_has_a_readable_error(self):
        path = self.output / "lineage.json"
        records = json.loads(path.read_text())
        del records[0]["genome"]
        path.write_text(json.dumps(records), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Malformed run artifact"):
            audit(self.output)


if __name__ == "__main__":
    unittest.main()
