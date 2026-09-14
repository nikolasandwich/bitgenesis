from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from bitgenesis.v2.development import DevelopmentGenome
from bitgenesis.v3.genome import EcologyGenome
from bitgenesis.v3.audit import audit
from bitgenesis.v3.runner import run
from bitgenesis.v3.world import Config


class HistoryAuditTests(unittest.TestCase):
    def test_failed_children_and_rehashed_ancestry_corruption(self):
        genome=EcologyGenome(DevelopmentGenome((6,100,0,0,0,0,0,0,1,3)),16)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'run'
            config=Config(width=5,height=5,founders=8,initial_energy=270,birth_threshold=160)
            run(path,config,85400,100,founder_genomes=[genome]*8)
            final=json.loads((path/'final.json').read_text())
            self.assertTrue(any(a['parent'] is not None and not a['valid'] for a in final['attempts']))
            audit(path)
            final['lineage'][0]['generation']+=1
            data=json.dumps(final).encode()
            (path/'final.json').write_bytes(data)
            meta=json.loads((path/'metadata.json').read_text())
            meta['output_sha256']['final.json']=sha256(data).hexdigest()
            (path/'metadata.json').write_text(json.dumps(meta),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'final inherited state'):
                audit(path)


if __name__=='__main__':
    unittest.main()
