import json
from hashlib import sha256
from pathlib import Path
import tempfile
import unittest
from bitgenesis.v4.damage import damage
from bitgenesis.v4.damage_branches import run
from bitgenesis.v4.damage_audit import audit
from bitgenesis.v4.growing_runner import run as growing_run
from bitgenesis.v4.local import Unit


class DamageTests(unittest.TestCase):
    def test_per_site_material_retention(self):
        units=[Unit(0,5),None,Unit(2,0)]
        raw=[0,2,1]
        after,stock,row=damage(units,raw,[0,1,2])
        self.assertEqual(after,[None]*3)
        self.assertEqual(stock,[1,2,2])
        self.assertEqual(row['exported_energy'],5)
        self.assertEqual(row['exported_material'],0)
        self.assertEqual(row['recycled_material'],2)
        for i in range(3):
            self.assertEqual(raw[i]+(units[i] is not None),stock[i]+(after[i] is not None))
        self.assertEqual(raw,[0,2,1])

    def test_independent_branch_reconstruction_and_corruption(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            growing_run(root/'prefix',90900,steps=10,width=4,height=4)
            growing_run(root/'continuous',90900,steps=20,width=4,height=4)
            finals=[]
            for name,sites,threshold in (('sham',[],16),('damaged',[0,1,4,5],16),('disabled',[0,1,4,5],65)):
                summary=run(root/name,root/'prefix',10,sites,threshold)
                self.assertEqual(audit(root/name,root/'prefix')['summary'],summary)
                self.assertEqual(summary['initial_material'],summary['final_material'])
                finals.append(json.loads((root/name/'final.json').read_text()))
            self.assertEqual((root/'sham/final.json').read_bytes(),(root/'continuous/final.json').read_bytes())
            for other in finals[1:]:
                self.assertEqual(other['drive_rng'],finals[0]['drive_rng'])
                self.assertEqual(other['direction_rng'],finals[0]['direction_rng'])
            file=root/'damaged/boundary.json'
            row=json.loads(file.read_text())
            row['recycled_material']+=1
            file.write_text(json.dumps(row),encoding='utf-8')
            meta_path=root/'damaged/metadata.json'
            meta=json.loads(meta_path.read_text())
            meta['output_sha256']['boundary.json']=sha256(file.read_bytes()).hexdigest()
            meta_path.write_text(json.dumps(meta),encoding='utf-8')
            with self.assertRaises(ValueError):
                audit(root/'damaged',root/'prefix')

    def test_zero_horizon_still_recycles_and_invalid_sites_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            growing_run(root/'prefix',90901,steps=0,width=3,height=3,occupancy=1000)
            with self.assertRaises(ValueError):
                run(root/'bad',root/'prefix',0,[0,0])
            self.assertFalse((root/'bad').exists())
            summary=run(root/'zero',root/'prefix',0,[0])
            self.assertEqual(audit(root/'zero',root/'prefix')['summary'],summary)
            self.assertEqual(summary['recycled_material'],1)
