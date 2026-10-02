import unittest
from scripts.verify_v4_study012_summary import recount, check_coverage


class Study012VerifierTests(unittest.TestCase):
    def test_equal_component_retention_and_initial_eligibility(self):
        records=[]
        for size,survivors,whole in [(2,1,False),(4,3,False),(1,1,False),(7,7,True)]:
            records.append(dict(anchor_size=size,whole_world_anchor=whole,continuous_closed_multi=True,
                primary=False,endpoint=dict(state='closed_multi',descendants=size,original_survivors=survivors)))
        r=recount(records)
        self.assertEqual(r['eligible_components'],2)
        self.assertEqual(r['fractions']['original_retention'],'5/8')
        self.assertEqual(r['fractions']['descendants'],'3')
        self.assertEqual(r['sums']['original_retention'],'5/4')
        self.assertIsNone(recount([])['fractions']['continuous'])

    def test_missing_duplicate_unknown_keys_rejected(self):
        expected={(0,),(1,)}
        check_coverage([{'id':0},{'id':1}],('id',),expected)
        for rows in [[{'id':0}],[{'id':0},{'id':0}],[{'id':0},{'id':2}]]:
            with self.assertRaises(ValueError):check_coverage(rows,('id',),expected)

    def test_binding_inventory_cannot_be_omitted(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from hashlib import sha256
        from scripts.verify_v4_study012_summary import verify_bindings
        with TemporaryDirectory() as temporary:
            p=Path(temporary)/'protocol.md';p.write_text('frozen')
            h=sha256(p.read_bytes()).hexdigest()
            verify_bindings({str(p):h},{p})
            for bad in ({},{str(p):'0'*64},{str(p):h,str(p)+'extra':h}):
                with self.assertRaises(ValueError):verify_bindings(bad,{p})
