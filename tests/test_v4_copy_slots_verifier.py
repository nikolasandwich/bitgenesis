import json
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
from scripts import verify_v4_copy_slots as v
from bitgenesis.v4.structure_audit import reconstruct

SITES = [[85, 86], [101, 102], [117, 118]]
FLAGS = ('occupied', 'material_match', 'genetic_match', 'whole_component', 'descendant', 'all_new', 'copy', 'new_copy')

def fixture():
    units = [None]*256; ids = [None]*256; raw = [0]*256
    for i,s in enumerate((85,86,204)):
        units[s] = dict(material=0 if i < 2 else 3, program=[0]*4 if i < 2 else [3]*4, energy=64); ids[s] = i
    for s in (101,102,117,118): raw[s] = 1
    initial = dict(units=units, raw=raw, site_ids=ids, tick=0, observation=reconstruct(units,ids,16,16,'final'))
    rows = [dict(tick=t, site_ids=ids.copy(), physical=dict(units=deepcopy(units)), observation=deepcopy(initial['observation'])) for t in range(1,33)]
    return dict(mode='random-direction',exchange=False,seed=120000,initial=initial,rows=rows,final=dict(parents=[None]*3))

def record_fixture():
    with patch.object(v.old,'recount'):
        return v.analyze_case(fixture(),'homogeneous')

class CopySlotsVerifierTests(unittest.TestCase):
    def test_placements_periodic_order_no_rotation(self):
        self.assertEqual(v.placements([85,86,101,102,117,118,204]),SITES)
        self.assertEqual(v.placements([15,0,16]),[[15,0]])
        self.assertEqual(v.placements([0,16]),[])

    def test_physics_and_observation_gate(self):
        case=fixture()
        with patch.object(v.old,'recount') as replay:
            result=v.analyze_case(case,'homogeneous'); replay.assert_called_once_with(case,'homogeneous')
        self.assertEqual(result['rows'][0]['copy_count'],1)
        self.assertEqual(result['rows'][0]['new_copy_count'],0)
        for target in ('initial','row'):
            case=fixture(); obs=case['initial']['observation'] if target=='initial' else case['rows'][0]['observation']; obs['components']['material']=[]
            with patch.object(v.old,'recount'),self.assertRaises(ValueError):v.analyze_case(case,'homogeneous')
        with patch.object(v.old,'recount',side_effect=ValueError('physics')),self.assertRaisesRegex(ValueError,'physics'):v.analyze_case(fixture(),'homogeneous')

    def test_new_copy_component_and_ancestry_boundaries(self):
        case=fixture(); case['final']['parents'] += [0,1,3,4]
        row=case['rows'][0]; row['physical']['units'][85]=None; row['physical']['units'][86]=None; row['site_ids'][85]=row['site_ids'][86]=None
        for s,i in ((101,5),(102,6)):
            row['physical']['units'][s]=deepcopy(case['initial']['units'][85]);row['site_ids'][s]=i
        row['observation']=reconstruct(row['physical']['units'],row['site_ids'],16,16,'final')
        with patch.object(v.old,'recount'):result=v.analyze_case(case,'homogeneous')
        slot=result['rows'][0]['slots'][1];self.assertTrue(slot['new_copy']);self.assertEqual(slot['roots'],[0,1])
        self.assertTrue(all(not result['rows'][0]['slots'][0][f] for f in FLAGS))
        # Add a third material member: the adjacent pair is no longer a whole component.
        row['physical']['units'][117]=deepcopy(case['initial']['units'][85]);row['site_ids'][117]=3
        row['observation']=reconstruct(row['physical']['units'],row['site_ids'],16,16,'final')
        with patch.object(v.old,'recount'):result=v.analyze_case(case,'homogeneous')
        self.assertFalse(result['rows'][0]['slots'][1]['copy'])
        case['final']['parents'][5]=5
        with patch.object(v.old,'recount'),self.assertRaises(ValueError):v.analyze_case(case,'homogeneous')

    def test_real_first_saved_case(self):
        case=json.loads(Path('data/v4-study-019/cases/seed-120000-random-direction-exchange-false.json').read_text())
        result=v.analyze_case(case,'homogeneous')
        self.assertEqual(result['placements'],SITES);self.assertEqual(len(result['rows']),32)

    def test_strict_summary_and_intervals(self):
        base=record_fixture(); records=[]
        for g,m,x,s in v.GRID:
            r=deepcopy(base);r.update(genotype=g,mode=m,exchange=x,seed=s);records.append(r)
        cells=v.summarize(records)
        self.assertEqual(len(cells),12);self.assertEqual(cells[0]['slot_steps'],1920)
        self.assertEqual(cells[0]['totals']['copy'],640);self.assertEqual(cells[0]['double_steps'],0)
        self.assertEqual(v.episodes([1,2,3,1,2]),([[2,3],[5,5]],2))
        mutations=[lambda r:r.reverse(),lambda r:r[0].update(longest=True),lambda r:r[0]['rows'][0].update(copy_count=2),lambda r:r[0]['rows'][0]['slots'][0].update(copy=1),lambda r:r[0]['rows'][0]['slots'][0].update(roots=[2,1]),lambda r:r[0].update(episodes=[[1,2]]),lambda r:r[0]['rows'][0]['slots'][1].update(all_new=True)]
        for mutate in mutations:
            altered=deepcopy(records);mutate(altered)
            with self.assertRaises(ValueError):v.summarize(altered)

    def test_postwrite_budget_removes_proof(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as d:
            path=Path(d)/'proof.json'
            with self.assertRaisesRegex(ValueError,'budget'):
                v.write_proof(path,{},lambda extra=0: None if extra else (_ for _ in ()).throw(ValueError('budget')))
            self.assertFalse(path.exists())


class CopySlotsVerifierMainTests(unittest.TestCase):
    def test_early_failures_preserve_input_and_output_evidence(self):
        import sys
        import types
        from tempfile import TemporaryDirectory
        for defect in ('binding', 'metadata', 'paths'):
            with self.subTest(defect=defect), TemporaryDirectory() as directory:
                root = Path(directory)
                for name in ('metadata.json', 'records.json', 'summary.json'):
                    (root/name).write_text('{}')
                bound = {f'input-{i}': 'a' * 64 for i in range(412)}
                bound['scripts/verify_v4_copy_slots.py'] = 'a' * 64
                def paths(errors):
                    if defect == 'paths': raise ValueError('broken inventory')
                    return sorted(bound)
                helper = types.SimpleNamespace(input_paths=paths,
                    digest=lambda path: 'a' * 64,
                    bindings=lambda: {} if defect == 'binding' else bound,
                    read=lambda path: dict(status='failed'), source_cases=lambda: ())
                with patch.dict(sys.modules, {'scripts.copy_slots_inputs': helper}), patch.object(v, 'OUTPUT', root), patch.object(v, 'analyze_case') as analyze:
                    with self.assertRaises(ValueError): v.main()
                    analyze.assert_not_called()
                evidence = json.loads((root/'verification-failure.json').read_text())
                self.assertEqual(evidence['status'], 'failed')
                self.assertEqual(len(evidence['files_sha256_before']), 3)
                self.assertEqual(len(evidence['files_sha256_after']), 3)
                self.assertEqual(len(evidence['input_sha256']), 0 if defect == 'paths' else 413)
                self.assertFalse((root/'independent-verification.json').exists())

    def test_existing_proof_never_overwritten(self):
        import sys
        import types
        from tempfile import TemporaryDirectory
        helper = types.SimpleNamespace(bindings=None, read=None, digest=None, input_paths=None, source_cases=None)
        with TemporaryDirectory() as directory:
            root = Path(directory)
            proof = root/'independent-verification.json'; proof.write_text('existing evidence')
            with patch.dict(sys.modules, {'scripts.copy_slots_inputs': helper}), patch.object(v, 'OUTPUT', root), self.assertRaisesRegex(ValueError, 'proof already exists'):
                v.main()
            self.assertEqual(proof.read_text(), 'existing evidence')
            self.assertFalse((root/'verification-failure.json').exists())

    def test_postwrite_budget_failure_withdraws_verified_proof(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as directory:
            proof = Path(directory)/'independent-verification.json'
            calls = []
            def budget(extra=0):
                calls.append(extra)
                if len(calls) == 2:
                    self.assertTrue(proof.exists())
                    raise ValueError('postwrite budget')
            with self.assertRaisesRegex(ValueError, 'postwrite budget'):
                v.write_proof(proof, dict(status='verified'), budget)
            self.assertFalse(proof.exists())
            self.assertGreater(calls[0], 0)
            self.assertEqual(calls[1], 0)

class CopySlotsBoundaryTests(unittest.TestCase):
    def test_program_material_and_outside_ancestry(self):
        for defect in ('program','material','root2','partial'):
            case=fixture();case['final']['parents'] += [0,1]
            row=case['rows'][0]
            for s,i in ((101,3),(102,4)):
                row['physical']['units'][s]=deepcopy(case['initial']['units'][85]);row['site_ids'][s]=i
            # Remove founders to keep the pair isolated from vertical neighbors.
            for s in (85,86):row['physical']['units'][s]=None;row['site_ids'][s]=None
            if defect=='program':row['physical']['units'][101]['program'][3]=1
            if defect=='material':row['physical']['units'][101]['material']=1
            if defect=='root2':case['final']['parents'][3]=2
            if defect=='partial':row['physical']['units'][102]=None;row['site_ids'][102]=None
            row['observation']=reconstruct(row['physical']['units'],row['site_ids'],16,16,'final')
            with patch.object(v.old,'recount'):result=v.analyze_case(case,'homogeneous')
            slot=result['rows'][0]['slots'][1]
            self.assertFalse(slot['copy'],defect)
            if defect=='program':self.assertTrue(slot['material_match']);self.assertFalse(slot['genetic_match'])
            if defect=='root2':self.assertTrue(slot['genetic_match']);self.assertTrue(slot['all_new']);self.assertFalse(slot['descendant'])
            if defect=='partial':self.assertTrue(all(not slot[f] for f in FLAGS))

    def test_persistent_interval_does_not_require_same_members(self):
        base=record_fixture()
        for tick,row in enumerate(base['rows'][:10],1):
            slot=row['slots'][1]
            slot.update(identities=[2*tick+1,2*tick+2],roots=[0,0],**dict.fromkeys(FLAGS,True))
            row.update(copy_count=2,new_copy_count=1)
        base.update(episodes=[[1,10]],longest=10)
        records=[]
        for g,m,x,s in v.GRID:
            r=deepcopy(base);r.update(genotype=g,mode=m,exchange=x,seed=s);records.append(r)
        first=v.summarize(records)[0]
        self.assertEqual(first['cases_persistent10'],20)
        self.assertEqual(first['double_steps'],200)
        self.assertEqual(first['new_double_steps'],0)
        self.assertEqual(first['max_double_run'],10)
