from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from bitgenesis.v2.development import DevelopmentGenome
from bitgenesis.v3.branches import run_branch, donor_schedule
from bitgenesis.v3.branch_replay import verify
from bitgenesis.v3.genome import EcologyGenome
from bitgenesis.v3.runner import state, encoded
from bitgenesis.v3.world import Config, World


class BranchTests(unittest.TestCase):
    def origin(self):
        genome=EcologyGenome(DevelopmentGenome((6,100,0,0,0,0,0,0,1,1)),16)
        world=World(Config(width=5,height=5,founders=2,initial_energy=400,birth_threshold=160),85600,
                    founder_genomes=[genome]*2)
        for _ in range(3):
            world.step()
        return world

    def test_neutral_matches_uninterrupted_and_treatments_are_isolated(self):
        origin=self.origin()
        before=encoded(state(origin))
        direct=deepcopy(origin)
        for _ in range(20):
            direct.step()
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            run_branch(root/'reference',origin,20)
            final=json.loads((root/'reference/final.json').read_text())
            self.assertEqual(encoded(final),encoded(state(direct)))
            schedule=donor_schedule(root/'reference',0)
            self.assertTrue(schedule)
            self.assertTrue(all(origin.tick<t<origin.tick+20 for t in schedule))
            removed=run_branch(root/'removed',origin,20,remove_founder=0)
            replay=run_branch(root/'replay',origin,20,remove_founder=0,deposits=schedule)
            self.assertGreater(removed['exported_energy'],0)
            self.assertEqual(removed['exported_energy'],replay['exported_energy'])
            self.assertGreater(replay['imported_energy'],0)
            self.assertEqual(encoded(state(origin)),before)
            for name in ('reference','removed','replay'):
                self.assertIn('same-engine',verify(root/name,origin)['scope'])
            for name in ('removed','replay'):
                self.assertEqual((root/name/'initial.json').read_bytes(),(root/'reference/initial.json').read_bytes())
            records=[json.loads(line) for line in (root/'replay/steps.jsonl').read_text().splitlines()]
            for row in records:
                self.assertEqual(row['boundary']['energy_after'],row['step']['energy_before'])

    def test_rehashed_boundary_corruption_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'branch'
            origin=self.origin()
            run_branch(root,origin,3,remove_founder=0)
            rows=[json.loads(line) for line in (root/'steps.jsonl').read_text().splitlines()]
            rows[0]['boundary']['exported_energy']+=1
            data=''.join(encoded(row) for row in rows).encode()
            (root/'steps.jsonl').write_bytes(data)
            meta=json.loads((root/'metadata.json').read_text())
            meta['output_sha256']['steps.jsonl']=sha256(data).hexdigest()
            (root/'metadata.json').write_text(json.dumps(meta),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'independent boundary record'):
                verify(root,origin)

    def test_invalid_schedule_rejected_before_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'bad'
            origin=self.origin()
            with self.assertRaises(ValueError):
                run_branch(root,origin,2,deposits={origin.tick+2:[(0,1)]})
            self.assertFalse(root.exists())


if __name__=='__main__':
    unittest.main()
