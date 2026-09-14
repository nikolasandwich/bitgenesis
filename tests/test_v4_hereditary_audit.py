import json
from hashlib import sha256
from pathlib import Path
import tempfile
import unittest
from bitgenesis.v4.hereditary_runner import run
from bitgenesis.v4.hereditary_audit import audit


class HereditaryAuditTests(unittest.TestCase):
    def test_rehashed_program_and_ticket_corruption(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'run'
            run(root,95005,20,width=4,height=4,occupancy=250,mutation_per_thousand=1000)
            audit(root)
            original=(root/'steps.jsonl').read_bytes()
            for field in ('child_program','mutation_tickets'):
                rows=[json.loads(line) for line in original.splitlines()]
                if field=='child_program':
                    formed=next(p for r in rows for p in r['material']['proposals'] if p['reason']=='formed')
                    formed[field][0]=(formed[field][0]+1)%4
                else:
                    rows[0][field][0][0]=(rows[0][field][0][0]+1)%1000
                data=''.join(json.dumps(r)+'\n' for r in rows).encode()
                (root/'steps.jsonl').write_bytes(data)
                meta=json.loads((root/'metadata.json').read_text())
                meta['output_sha256']['steps.jsonl']=sha256(data).hexdigest()
                (root/'metadata.json').write_text(json.dumps(meta),encoding='utf-8')
                with self.assertRaises(ValueError):
                    audit(root)
