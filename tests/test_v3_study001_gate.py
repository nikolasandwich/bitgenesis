from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from scripts.verify_v3_study001 import verify


class StudyGateTests(unittest.TestCase):
    def test_missing_and_duplicate_sources_rejected_before_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            meta=dict(status='complete',completed_sources=5,planned_sources=5,
                      protocol_sha256=sha256(Path('experiments/v3/study-001.md').read_bytes()).hexdigest())
            (root/'metadata.json').write_text(json.dumps(meta),encoding='utf-8')
            for seeds in (range(88000,88004),[88000,88001,88002,88003,88003]):
                (root/'results.json').write_text(json.dumps([dict(seed=s) for s in seeds]),encoding='utf-8')
                with self.assertRaisesRegex(ValueError,'source grid mismatch'):
                    verify(root)


if __name__=='__main__':
    unittest.main()
