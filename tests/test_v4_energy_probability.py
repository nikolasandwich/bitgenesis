import json
import unittest
from copy import deepcopy
from fractions import Fraction as F
from pathlib import Path
from unittest.mock import patch
from scripts import analyze_v4_energy_probability as run


class EnergyProbabilityTest(unittest.TestCase):
    def test_closed_forms_and_conservation(self):
        rows=run.curve(5)
        self.assertEqual(len(rows),6)
        self.assertEqual(rows[0],dict(horizon=0,alive=['0']*4+['1']+['0']*10,first_hit='0',first_death='0',hit='0',dead='0',surviving='1'))
        self.assertEqual(F(rows[1]['alive'][3]),F(63,64))
        self.assertEqual(F(rows[1]['alive'][11]),F(1,64))
        self.assertEqual(F(rows[2]['first_hit']),F(1,64**2))
        self.assertEqual(F(rows[3]['first_hit']),F(2*63,64**3))
        self.assertEqual(F(rows[5]['dead']),F(63**5,64**5))
        for i,row in enumerate(rows):
            self.assertEqual(set(row),{'horizon','alive','first_hit','first_death','hit','dead','surviving'})
            self.assertEqual(len(row['alive']),15)
            self.assertTrue(all(type(p) is str and p==str(F(p)) and F(p)>=0 for p in row['alive']+[row[k] for k in ('hit','dead','surviving','first_hit','first_death')]))
            self.assertEqual(sum(map(F,row['alive'])),F(row['surviving']))
            self.assertEqual(sum(F(row[k]) for k in ('hit','dead','surviving')),1)
            if i:
                for cumulative,first in (('hit','first_hit'),('dead','first_death')):
                    self.assertEqual(F(row[cumulative])-F(rows[i-1][cumulative]),F(row[first]))
        # Already-hit paths remain hit despite later no-ticket steps.
        self.assertGreaterEqual(F(rows[5]['hit']),F(rows[2]['hit']))
        self.assertEqual(F(rows[5]['first_death']),F(63,64)**5)

    def test_horizon_types(self):
        for value in (-1,33,True,1.0,'2',None):
            with self.subTest(value=value),self.assertRaises(ValueError):run.curve(value)

    def timing(self):
        return json.loads(Path('docs/research/results/v4-study-030-records.json').read_text())

    def fixture_curve(self):
        return [dict(horizon=h,hit=str(F(h,64)),dead=str(F(1,4)),surviving=str(F(3,4)-F(h,64))) for h in range(33)]

    def test_complete_cohort_plumbing(self):
        timing=self.timing(); before=deepcopy(timing); curve=self.fixture_curve()
        with patch.object(run,'curve',return_value=curve) as compute:records,summary=run.build(timing)
        compute.assert_called_once_with()
        self.assertEqual(records['curve'],curve);self.assertEqual(timing,before)
        self.assertEqual([r['selection'] for r in records['cohort']],[r['selection'] for r in timing])
        self.assertEqual([s['n'] for s in summary],[21,5,21,5])
        for source,row in zip(timing,records['cohort']):
            self.assertEqual(row,dict(selection=source['selection'],horizon=32-source['birth_tick'],**{k:curve[32-source['birth_tick']][k] for k in ('hit','dead','surviving')}))
        for cell in summary:
            chosen=[r for r in records['cohort'] if (r['selection']['genotype'],r['selection']['exchange'])==(cell['genotype'],cell['exchange'])]
            self.assertEqual(F(cell['expected_hits']),sum(F(r['hit']) for r in chosen))
            for k in ('hit','dead','surviving'):self.assertEqual(F(cell['mean_'+k]),sum(F(r[k]) for r in chosen)/len(chosen))
        records['cohort'][0]['selection']['seed']=0
        self.assertEqual(timing,before)

    def test_bad_cohort_rejected_before_curve(self):
        for kind in ('missing','duplicate','order','extra','bool','birth','birth_type','range'):
            bad=self.timing()
            if kind=='missing':bad.pop()
            if kind=='duplicate':bad[1]=deepcopy(bad[0])
            if kind=='order':bad[0],bad[1]=bad[1],bad[0]
            if kind=='extra':bad[0]['selection']['extra']=0
            if kind=='bool':bad[0]['selection']['seed']=True
            if kind=='birth':bad[0]['birth_tick']+=1
            if kind=='birth_type':bad[0]['birth_tick']=float(bad[0]['birth_tick'])
            if kind=='range':bad[0]['birth_tick']=bad[0]['selection']['tick']=1
            with self.subTest(kind=kind),patch.object(run,'curve') as compute:
                with self.assertRaises(ValueError):run.build(bad)
                compute.assert_not_called()

    def test_main_evidence_and_final_budget(self):
        import hashlib,sys,tempfile,types
        for mode in ('binding','complete','budget'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as directory:
                out=Path(directory)/'out'; expired=False
                inventory=[str(i) for i in range(503)]; before={p:'a'*64 for p in inventory}
                def digest(path):
                    return hashlib.sha256(path.read_bytes()).hexdigest() if isinstance(path,Path) else before[path]
                def bindings():
                    if mode=='binding':raise ValueError('bad binding')
                    return dict(before)
                def save(path,value):
                    nonlocal expired
                    path.write_text(json.dumps(value))
                    if mode=='budget' and path.name=='metadata.json' and value['status']=='complete':expired=True
                helper=types.SimpleNamespace(input_paths=lambda errors:inventory,bindings=bindings,digest=digest,read=lambda p:[],save=save)
                def git(command,**kwargs):return '' if command[1]=='status' else 'a'*40
                fake=dict(curve=[None]*33,cohort=[None]*52)
                with patch.object(run,'OUTPUT',out),patch.object(run.subprocess,'check_output',git),patch.object(run.time,'monotonic',side_effect=lambda:61 if expired else 0),patch.object(run,'build',return_value=(fake,[])),patch.dict(sys.modules,{'scripts.energy_probability_inputs':helper}):
                    if mode=='complete':run.main()
                    else:
                        with self.assertRaisesRegex(ValueError,'bad binding' if mode=='binding' else 'bounded execution'):run.main()
                    with self.assertRaises(FileExistsError):run.main()
                meta=json.loads((out/'metadata.json').read_text())
                self.assertEqual(meta['status'],'complete' if mode=='complete' else 'failed')
                self.assertEqual(meta['input_sha256'],before);self.assertEqual(meta['input_sha256_after'],before)
                self.assertEqual(meta['completed_horizons'],0 if mode=='binding' else 33)
                self.assertEqual((meta['cohort_states'],meta['time_limit_seconds'],meta['storage_limit_bytes']),(52,60,8388608))
                self.assertEqual(meta['new_full_world_steps'],0)
                for name,digest_value in meta['output_sha256'].items():self.assertEqual(digest_value,digest(out/name))

    def test_absorbed_weights_never_reenter_alive(self):
        alive,hit,dead,first_hit,first_death=run._advance([0]*15,3,5)
        self.assertEqual(alive,[0]*15)
        self.assertEqual((hit,dead,first_hit,first_death),(192,320,0,0))
        initial=[0]*15;initial[0]=7;initial[14]=2
        alive,hit,dead,first_hit,first_death=run._advance(initial,3,5)
        self.assertEqual((first_hit,first_death),(2,441))
        self.assertEqual((hit,dead),(194,761))
        self.assertEqual(sum(alive)+hit+dead,(7+2+3+5)*64)

    def test_unreadable_input_hashes_survive_binding_failure(self):
        import hashlib,sys,tempfile,types
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);out=root/'out';present=root/'present';missing=root/'missing';present.write_text('input')
            def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
            helper=types.SimpleNamespace(input_paths=lambda errors:[str(present),str(missing)],
                bindings=lambda:(_ for _ in ()).throw(ValueError('bad binding')),digest=digest,
                read=lambda p:json.loads(p.read_text()),save=lambda p,v:p.write_text(json.dumps(v)))
            def git(command,**kwargs):return '' if command[1]=='status' else 'a'*40
            with patch.object(run,'OUTPUT',out),patch.object(run.subprocess,'check_output',git),patch.dict(sys.modules,{'scripts.energy_probability_inputs':helper}):
                with self.assertRaisesRegex(ValueError,'bad binding'):run.main()
            meta=json.loads((out/'metadata.json').read_text())
            self.assertEqual(meta['input_paths'],[str(present),str(missing)])
            self.assertEqual(meta['input_sha256'],{str(present):digest(present)})
            self.assertEqual(meta['input_sha256_after'],meta['input_sha256'])
            self.assertIn(str(missing),meta['input_read_errors_before'])
            self.assertIn(str(missing),meta['input_read_errors'])
            self.assertEqual(meta['completed_horizons'],0)
