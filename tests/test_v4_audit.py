from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from bitgenesis.v4.runner import run
from bitgenesis.v4.audit import audit


class AuditTests(unittest.TestCase):
    def test_exchange_controls_zero_cost_and_empty_horizon(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for index,(exchange,cost,steps) in enumerate(((True,1,30),(False,1,30),(True,0,30),(False,0,0))):
                path=root/str(index)
                result=run(path,90200,steps,width=5,height=5,exchange=exchange,bond_cost=cost)
                self.assertEqual(audit(path)['summary'],result)

    def test_rehashed_component_corruption(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'run'
            run(path,90201,5,width=5,height=5)
            rows=[json.loads(line) for line in (path/'steps.jsonl').read_text().splitlines()]
            rows[0]['components']=[]
            data=''.join(json.dumps(r)+'\n' for r in rows).encode()
            (path/'steps.jsonl').write_bytes(data)
            meta=json.loads((path/'metadata.json').read_text())
            meta['output_sha256']['steps.jsonl']=sha256(data).hexdigest()
            (path/'metadata.json').write_text(json.dumps(meta),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'state/component'):
                audit(path)


if __name__=='__main__':
    unittest.main()
