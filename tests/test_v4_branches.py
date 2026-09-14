import json
from hashlib import sha256
from pathlib import Path
import tempfile
import unittest
from bitgenesis.v4.growing_runner import run as growing_run
from bitgenesis.v4.branches import run
from bitgenesis.v4.branch_audit import audit


class BranchTests(unittest.TestCase):
    def test_rehashed_boundary_and_continuation_corruption(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            growing_run(root/'prefix',90802,steps=3,width=3,height=3)
            run(root/'branch',root/'prefix',3,sites=[0,1])
            branch=root/'branch'
            for filename in ('boundary.json','steps.jsonl'):
                original=(branch/filename).read_bytes()
                if filename=='boundary.json':
                    value=json.loads(original)
                    value['exported_energy']+=1
                    data=json.dumps(value).encode()
                else:
                    rows=[json.loads(line) for line in original.splitlines()]
                    rows[0]['directions'][0]=(rows[0]['directions'][0]+1)%4
                    data=''.join(json.dumps(r)+'\n' for r in rows).encode()
                meta=json.loads((branch/'metadata.json').read_text())
                (branch/filename).write_bytes(data)
                meta['output_sha256'][filename]=sha256(data).hexdigest()
                (branch/'metadata.json').write_text(json.dumps(meta),encoding='utf-8')
                with self.assertRaises(ValueError):
                    audit(branch,root/'prefix')
                (branch/filename).write_bytes(original)
                meta['output_sha256'][filename]=sha256(original).hexdigest()
                (branch/'metadata.json').write_text(json.dumps(meta),encoding='utf-8')
            audit(branch,root/'prefix')

    def test_sham_equals_continuous_and_removal_preserves_tickets(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            growing_run(root/'prefix',90800,steps=10,width=4,height=4)
            growing_run(root/'continuous',90800,steps=20,width=4,height=4)
            original=(root/'prefix/final.json').read_bytes()
            for name,sites,threshold in (('sham',[],None),('removed',[0,1,4,5],None),('disabled',[0,1,4,5],65)):
                summary=run(root/name,root/'prefix',10,sites,threshold)
                self.assertEqual(audit(root/name,root/'prefix')['summary'],summary)
                self.assertEqual(summary['initial_energy']+summary['imported']-summary['spent'],summary['final_energy'])
                self.assertEqual(summary['initial_material'],summary['final_material'])
            self.assertEqual((root/'sham/final.json').read_bytes(),(root/'continuous/final.json').read_bytes())
            continuous=(root/'continuous/steps.jsonl').read_bytes().splitlines(keepends=True)[10:]
            self.assertEqual((root/'sham/steps.jsonl').read_bytes(),b''.join(continuous))
            reference=json.loads((root/'sham/final.json').read_text())
            for name in ('removed','disabled'):
                final=json.loads((root/name/'final.json').read_text())
                for key in ('drive_rng','direction_rng'):
                    self.assertEqual(final[key],reference[key])
            self.assertEqual((root/'prefix/final.json').read_bytes(),original)
            self.assertEqual(json.loads((root/'disabled/summary.json').read_text())['formations'],0)

    def test_zero_horizon_and_preflight(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            growing_run(root/'prefix',90801,steps=0,width=3,height=3)
            for kwargs in ({'sites':[0,0]},{'threshold':False},{'max_site_records':1}):
                with self.assertRaises(ValueError):
                    run(root/'bad',root/'prefix',0,**kwargs)
                self.assertFalse((root/'bad').exists())
            summary=run(root/'zero',root/'prefix',0,sites=[0,1])
            self.assertEqual(audit(root/'zero',root/'prefix')['summary'],summary)
            self.assertEqual(summary['formations'],0)
            self.assertEqual(summary['initial_energy'],summary['final_energy'])
            self.assertEqual((root/'zero/steps.jsonl').read_bytes(),b'')
            with self.assertRaises(FileExistsError):
                run(root/'zero',root/'prefix',0)
