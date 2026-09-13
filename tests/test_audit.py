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


if __name__ == "__main__":
    unittest.main()
