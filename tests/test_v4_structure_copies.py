import copy
import unittest
from itertools import product
from scripts import analyze_v4_structure_copies as a

P=(0,1,2,3)
def snapshot(groups,locations=None,programs=None,materials=None,tick=None):
    locations=locations or {0:0,1:1,2:8,3:16,4:17,5:9,6:24,7:25}
    ids=[None]*256;units=[None]*256
    for group in groups:
        for i in group:
            site=locations[i];ids[site]=i;units[site]=dict(material=(materials or {}).get(i,0),program=list((programs or {}).get(i,P)),energy=1)
    base=dict(site_ids=ids,observation=dict(components=dict(material=groups)))
    return dict(base,units=units) if tick is None else dict(base,tick=tick,physical=dict(units=units))

def case(groups=None):
    initial=snapshot([[0,1],[2]])
    rows=[snapshot([[0,1],[2]],tick=1),snapshot(groups or [[0,1],[3,4],[2,5],[6,7]],tick=2)]
    final=dict(parents=[None,None,None,0,1,2,2,2],site_ids=rows[-1]['site_ids'])
    return initial,rows,final

def parent(series):
    eps={k:a.episodes(v) for k,v in series.items()}
    return dict(component=0,anchor_members=[0,1],anchor_size=2,impossible_double=False,series=series,episodes=eps,longest={k:max((e-s+1 for s,e in v),default=0) for k,v in eps.items()})

def grid():
    return [dict(history=h,seed=s,mutation=m,exchange=e,parents=[parent({k:[0]*400 for k in a.SERIES})]) for h,s,m,e in product((True,False),range(112000,112005),(0,100),(True,False))]

class StructureCopies(unittest.TestCase):
    def test_periodic_translation_and_attributes(self):
        shape=((15,0,0,P),(0,0,1,P),(15,2,0,P))
        translated=tuple(((x+4)%16,(y+15)%16,m,p) for x,y,m,p in shape)
        self.assertEqual(a.canonical(shape),a.canonical(translated))
        rotation=tuple(((-y)%16,x,m,p) for x,y,m,p in shape)
        self.assertNotEqual(a.canonical(shape),a.canonical(rotation))
        changed=list(shape);changed[0]=(15,0,1,P)
        self.assertNotEqual(a.canonical(shape),a.canonical(changed))
        changed[0]=(15,0,0,(1,0,2,3))
        self.assertNotEqual(a.canonical(shape),a.canonical(changed))
    def test_full_components_ancestry_and_future_birth(self):
        p=a.analyze(*case())[0]
        self.assertEqual(p['series']['descendant_material'],[1,2])
        self.assertEqual(p['series']['descendant_genetic'],[1,2])
        self.assertEqual(p['series']['unrelated_material'],[0,2])
        self.assertEqual(p['episodes']['descendant_material'],[[2,2]])
        initial,rows,final=case([[0,1,3,4],[2,5],[6,7]])
        self.assertEqual(a.analyze(initial,rows,final)[0]['series']['descendant_material'],[1,0])
    def test_mixed_component_and_program_mismatch(self):
        initial,rows,final=case();rows[1]=snapshot([[0,2],[3,4]],locations={0:0,2:1,3:16,4:17},programs={4:(1,1,2,3)},tick=2);final['site_ids']=rows[1]['site_ids']
        p=a.analyze(initial,rows,final)[0]
        self.assertEqual(p['series']['descendant_material'][1],1)
        self.assertEqual(p['series']['descendant_genetic'][1],0)
        self.assertEqual(p['series']['unrelated_material'][1],0)
    def test_symmetry_counts_one_component_once(self):
        points=tuple((x,0,0) for x in range(16))
        self.assertEqual(a.canonical(points),a.canonical(tuple(((x+5)%16,y,m) for x,y,m in points)))
        initial=snapshot([list(range(16)),[16]],locations={**{i:i for i in range(16)},16:32})
        row=snapshot([list(range(16)),[16]],locations={**{i:i for i in range(16)},16:32},tick=1)
        p=a.analyze(initial,[row],dict(parents=[None]*17,site_ids=row['site_ids']))[0]
        self.assertEqual(p['series']['descendant_material'],[1])
    def test_episode_inclusive_edges_and_nine_ten(self):
        self.assertEqual(a.episodes([2]*9+[1]+[3]*10),[[1,9],[11,20]])
        self.assertEqual(a.episodes([]),[])
        for values in ([True],[1.0],[-1]):
            with self.assertRaises(ValueError):a.episodes(values)
        rows=grid()
        for r in rows:r['parents']=[parent({k:[2]*9+[0]*391 for k in a.SERIES})]
        results,_=a.summarize_records(rows)
        self.assertEqual(results[0]['counts']['descendant_genetic_ever'],1)
        self.assertEqual(results[0]['counts']['descendant_genetic_persistent'],0)
        for r in rows:r['parents']=[parent({k:[2]*10+[0]*390 for k in a.SERIES})]
        self.assertEqual(a.summarize_records(rows)[0][0]['counts']['descendant_genetic_persistent'],1)
    def test_equal_weight_missing_and_grid_validation(self):
        rows=grid()
        for r in rows:
            if r['seed']==112000:
                r['parents']=[dict(parent({k:[2]*400 for k in a.SERIES}),component=i,anchor_members=[2*i,2*i+1]) for i in range(9)]
            if r['seed']==112004:r['parents']=[]
        results,summary=a.summarize_records(rows)
        self.assertEqual(summary['cells'][0]['metrics']['descendant_genetic_persistent'],dict(mean='1/4',available=4,missing=1))
        self.assertEqual([len(summary[k]) for k in ('cells','pairs','groups')],[8,20,4])
        for change in (lambda r:r.pop(),lambda r:r.append(r[0]),lambda r:r[0].update(history=1)):
            bad=copy.deepcopy(rows);change(bad)
            with self.assertRaises(ValueError):a.summarize_records(bad)
        for change in (lambda r:r[0].update(status='failed'),lambda r:r[0].update(eligible=True),lambda r:r[0]['fractions'].update(descendant_genetic_ever='0/2'),lambda r:r[0]['counts'].update(descendant_genetic_ever=10)):
            bad=copy.deepcopy(results);change(bad)
            with self.assertRaises(ValueError):a.aggregate(bad)

    def test_large_impossible_parent_kept(self):
        groups=[list(range(129)),[129]];locations={**{i:i for i in range(129)},129:200}
        initial=snapshot(groups,locations=locations);row=snapshot(groups,locations=locations,tick=1)
        records=a.analyze(initial,[row],dict(parents=[None]*130,site_ids=row['site_ids']))
        self.assertEqual(len(records),1);self.assertEqual(records[0]['anchor_size'],129)
        self.assertTrue(records[0]['impossible_double'])
        self.assertEqual(records[0]['series']['descendant_genetic'],[1])
        self.assertEqual(records[0]['longest']['descendant_genetic'],0)

    def test_different_candidate_pairs_preserve_condition_episode(self):
        initial,rows,final=case()
        first=snapshot([[0,1],[3,4],[2,5]],tick=1)
        second=snapshot([[0,1],[6,7],[2,5]],locations={0:0,1:1,6:32,7:33,2:8,5:9},tick=2)
        final=dict(parents=[None,None,None,0,1,2,3,4],site_ids=second['site_ids'])
        p=a.analyze(initial,[first,second],final)[0]
        self.assertEqual(p['series']['descendant_genetic'],[2,2])
        self.assertEqual(p['episodes']['descendant_genetic'],[[1,2]])

    def test_failed_partial_run_budget_and_exclusive(self):
        import json
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        branches=grid();source_rows=[dict(r,status='complete',directory='unused') for r in branches]
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp);(directory/'steps.jsonl').write_text('{}\n'*400)
            for r in source_rows:r['directory']=str(directory)
            def read(path):
                return dict(source=str(directory),width=16,height=16)
            out=directory/'out'
            with patch.object(a,'OUTPUT',out),patch.object(a.subprocess,'check_output',side_effect=['','fixture-commit']),patch('scripts.structure_copy_inputs.bindings',return_value={'fixture':'fixed'}),patch('scripts.structure_copy_inputs.source_rows',return_value=source_rows),patch('scripts.structure_copy_inputs.read',side_effect=read),patch.object(a,'analyze',side_effect=[branches[0]['parents'],ValueError('second branch failure')]):
                with self.assertRaisesRegex(ValueError,'second branch failure'):a.main()
            meta=json.loads((out/'metadata.json').read_text())
            self.assertEqual((meta['status'],meta['completed_branches']),('failed',1))
            self.assertEqual(meta['input_sha256'],meta['input_sha256_after'])
            self.assertEqual(len(json.loads((out/'results.json').read_text())),1)
            self.assertEqual(len(json.loads((out/'records.json').read_text())),1)
            with patch.object(a,'OUTPUT',out),patch.object(a.subprocess,'check_output',return_value=''):
                with self.assertRaises(FileExistsError):a.main()
            budget_out=directory/'budget'
            with patch.object(a,'OUTPUT',budget_out),patch.object(a,'STORAGE',0),patch.object(a.subprocess,'check_output',side_effect=['','fixture-commit']),patch('scripts.structure_copy_inputs.bindings',return_value={'fixture':'fixed'}),patch('scripts.structure_copy_inputs.source_rows',return_value=source_rows):
                with self.assertRaisesRegex(ValueError,'storage budget exceeded'):a.main()
            self.assertEqual(json.loads((budget_out/'metadata.json').read_text())['status'],'failed')
