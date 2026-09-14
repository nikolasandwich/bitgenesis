from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from bitgenesis.v2.development import DevelopmentGenome
from bitgenesis.v3.genome import EcologyGenome
from bitgenesis.v3.resource_audit import audit
from bitgenesis.v3.spatial_audit import reconstruct
from bitgenesis.v3.audit import audit as full_audit
from bitgenesis.v3.runner import run
from bitgenesis.v3.world import Config


class ResourceAuditTests(unittest.TestCase):
    def test_births_recycling_removal_and_failed_founders(self):
        genome=EcologyGenome(DevelopmentGenome((6,100,0,0,0,0,0,0,1,1)),16)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for recycle in (0,1):
                path=root/str(recycle)
                config=Config(width=5,height=5,founders=4,initial_energy=400,
                              birth_threshold=160,initial_b=24,recycling=recycle)
                summary=run(path,config,85200,80,founder_genomes=[genome]*4)
                self.assertGreater(summary['births'],0)
                self.assertGreater(audit(path)['feedings'],0)
                self.assertTrue(reconstruct(path)['spatial_reconstruction'])
                self.assertEqual(full_audit(path)['summary'],summary)
            path=root/'failed'
            run(path,Config(width=3,height=3,founders=2,initial_energy=1),85201,5)
            self.assertEqual(audit(path)['actors'],0)
            self.assertEqual(reconstruct(path)['decisions'],0)
            self.assertEqual(full_audit(path)['summary']['population'],0)

    def test_rehashed_wrong_final_position_rejected(self):
        genome=EcologyGenome(DevelopmentGenome((6,100,0,0,0,0,0,0,1,1)),16)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'run'
            run(path,Config(width=3,height=3,founders=1),85300,3,founder_genomes=[genome])
            final=json.loads((path/'final.json').read_text())
            final['lineage'][0]['x']=(final['lineage'][0]['x']+1)%3
            data=json.dumps(final).encode()
            (path/'final.json').write_bytes(data)
            meta=json.loads((path/'metadata.json').read_text())
            meta['output_sha256']['final.json']=sha256(data).hexdigest()
            (path/'metadata.json').write_text(json.dumps(meta),encoding='utf-8')
            audit(path)  # Resource-only scope intentionally does not certify position.
            with self.assertRaisesRegex(ValueError,'final position'):
                reconstruct(path)

    def test_rehashed_semantic_corruptions_rejected(self):
        genome=EcologyGenome(DevelopmentGenome((6,100,0,0,0,0,0,0,1,1)),16)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'run'
            run(path,Config(width=3,height=3,founders=1),85202,3,founder_genomes=[genome])
            original=(path/'steps.jsonl').read_bytes()
            for change in ('release','renewal','site'):
                rows=[json.loads(line) for line in original.splitlines()]
                if change=='release':
                    rows[0]['actors'][0]['feeding']['released_b']+=1
                elif change=='renewal':
                    rows[0]['resource_added']+=1
                else:
                    rows[0]['actors'][0]['feeding']['site']=-1
                data=''.join(json.dumps(row)+'\n' for row in rows).encode()
                (path/'steps.jsonl').write_bytes(data)
                meta=json.loads((path/'metadata.json').read_text())
                meta['output_sha256']['steps.jsonl']=sha256(data).hexdigest()
                (path/'metadata.json').write_text(json.dumps(meta),encoding='utf-8')
                with self.assertRaises(ValueError):
                    audit(path)


if __name__=='__main__':
    unittest.main()
