from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import random
import tempfile
import unittest

from bitgenesis.v4.growing_audit import audit, reconstruct_material
from bitgenesis.v4.growing_runner import run
from bitgenesis.v4.local import Unit
from bitgenesis.v4.material import convert


class GrowingAuditTests(unittest.TestCase):
    def test_independent_material_reconstruction(self):
        rng = random.Random(90700)
        for _ in range(200):
            units = [Unit(rng.randrange(4), rng.randrange(25)) if rng.randrange(2) else None
                     for _ in range(16)]
            raw = [rng.randrange(3) for _ in units]
            directions = [rng.randrange(4) for _ in units]
            expected, stock, record = convert(units, raw, 4, 4, directions)
            actual = reconstruct_material([None if u is None else asdict(u) for u in units],
                                          raw, 4, 4, directions, 16, 4)
            self.assertEqual(actual, ([None if u is None else asdict(u) for u in expected], stock, record))

    def test_rehashed_corruption_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)/'run'
            run(root, 90701, steps=10, width=4, height=4)
            audit(root)
            original = (root/'steps.jsonl').read_bytes()
            for field in ('directions', 'raw', 'material', 'interaction_units'):
                with self.subTest(field=field):
                    rows = [json.loads(s) for s in original.splitlines()]
                    if field == 'directions':
                        rows[0][field][0] = (rows[0][field][0] + 1) % 4
                    elif field == 'raw':
                        rows[0][field][0] += 1
                    elif field == 'material':
                        rows[0][field]['spent'] += 1
                    else:
                        rows[0][field] = [None] * 16
                    data = ''.join(json.dumps(r)+'\n' for r in rows).encode()
                    (root/'steps.jsonl').write_bytes(data)
                    meta = json.loads((root/'metadata.json').read_text())
                    meta['output_sha256']['steps.jsonl'] = sha256(data).hexdigest()
                    (root/'metadata.json').write_text(json.dumps(meta), encoding='utf-8')
                    with self.assertRaises(ValueError):
                        audit(root)


if __name__ == '__main__':
    unittest.main()
