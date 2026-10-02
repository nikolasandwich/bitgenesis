import unittest
from itertools import product
from pathlib import Path
from unittest.mock import patch
from scripts import verify_v4_study015_summary as verifier


class Study015VerifierTests(unittest.TestCase):
    def grid(self, offset=0):
        rows=[]
        for seed,mutation,anchor,exchange in product(range(112000,112005),(0,100),(100,200,300,400),(True,False)):
            fractions={k:None for k in verifier.METRICS if k!='occupied'}
            rows.append(dict(seed=seed,mutation=mutation,anchor=anchor,exchange=exchange,status='complete',
                             occupied=anchor//100+offset if exchange else 0,
                             components=dict(initial_components=1,eligible_components=0,fractions=fractions)))
        return rows

    def test_full_grid_retains_zero_population_and_null_secondary(self):
        summary=verifier.aggregate_saved(self.grid(2),self.grid())
        self.assertEqual([len(summary['interaction'][k]) for k in ('pairs','sources','groups')],[40,10,2])
        self.assertEqual(summary['interaction']['groups'][0]['metrics']['occupied'],dict(mean='2',available=5,missing=0))
        self.assertEqual(summary['interaction']['groups'][0]['metrics']['continuous'],dict(mean=None,available=0,missing=5))
        self.assertEqual(summary['histories']['on']['groups'][0]['metrics']['occupied']['mean'],'5/2')
        self.assertEqual(summary['histories']['off']['groups'][0]['metrics']['occupied']['mean'],'9/2')

    def test_asymmetric_null_intersection_before_source_or_group_means(self):
        off,on=self.grid(),self.grid()
        for rows,values in ((off,{100:'1/2',200:'1',300:None,400:None}),
                            (on,{100:'1/4',200:None,300:'1/2',400:None})):
            for r in rows:
                value=values[r['anchor']] if r['seed']==112000 else None
                r['components'].update(eligible_components=int(value is not None))
                r['components']['fractions']['continuous']=value if r['exchange'] or value is None else '0'
        summary=verifier.aggregate_saved(off,on)
        pair=summary['interaction']['pairs'][0]['metrics']['continuous']
        self.assertEqual(pair,dict(on_history='1/4',off_history='1/2',difference='1/4'))
        self.assertEqual(summary['interaction']['pairs'][1]['metrics']['continuous'],dict(on_history=None,off_history='1',difference=None))
        self.assertEqual(summary['interaction']['sources'][0]['metrics']['continuous'],dict(mean='1/4',available=1,missing=3))
        self.assertEqual(summary['interaction']['groups'][0]['metrics']['continuous'],dict(mean='1/4',available=1,missing=4))
        self.assertNotEqual(summary['interaction']['sources'][0]['metrics']['continuous']['mean'],'3/8')

    def test_missing_duplicate_or_failed_rows_in_either_history_rejected(self):
        rows=self.grid()
        for bad in (rows[:-1],rows[:-1]+[rows[0]],[dict(r,status='failed') if i==0 else r for i,r in enumerate(rows)]):
            for off,on in ((bad,rows),(rows,bad)):
                with self.assertRaises((ValueError,AssertionError)):
                    verifier.aggregate_saved(off,on)

    def test_exact_code_inventory_and_manifest_omissions(self):
        required=verifier.required_code()
        for name in ('experiments/v4/study-015.md','scripts/history_exchange_branch.py','scripts/history_exchange_audit.py',
                     'scripts/study015_inputs.py','scripts/run_v4_study015.py','scripts/verify_v4_study015_summary.py'):
            self.assertIn(Path(name),required)
        self.assertTrue(set(Path('src/bitgenesis/v4').glob('*.py'))<=required)
        full={str(p):'test-digest' for p in required}
        with patch('scripts.verify_v4_study012_summary.sha256') as hash_call:
            hash_call.return_value.hexdigest.return_value='test-digest'
            with patch.object(Path,'read_bytes',return_value=b'test'):
                verifier.verify_bindings(full,required)
                for omitted in required:
                    with self.assertRaisesRegex(ValueError,'inventory'):
                        verifier.verify_bindings({k:v for k,v in full.items() if k!=str(omitted)},required)
                with self.assertRaisesRegex(ValueError,'inventory'):
                    verifier.verify_bindings(dict(full,unexpected='test-digest'),required)

    def test_external_tapes_and_final_streams_small_world(self):
        import json
        import copy
        from tempfile import TemporaryDirectory
        from bitgenesis.v4.hereditary_runner import run
        with TemporaryDirectory() as tmp:
            worlds=[]
            for exchange in (True,False):
                directory=Path(tmp)/str(exchange)
                run(directory,105002,steps=3,width=4,height=4,exchange=exchange)
                worlds.append((json.loads((directory/'initial.json').read_text()),
                               json.loads((directory/'final.json').read_text()),
                               [json.loads(s) for s in (directory/'steps.jsonl').read_text().splitlines()]))
            verifier.compare_history(*worlds[1],*worlds[0])
            for index in (0,1,2):
                bad=copy.deepcopy(worlds[1])
                if index==0:bad[0]['raw'][0]+=1
                if index==1:bad[1]['drive_rng'][1][0]+=1
                if index==2:bad[2][1]['mutation_tickets'][0][0]+=1
                with self.assertRaises(AssertionError):
                    verifier.compare_history(*bad,*worlds[0])
