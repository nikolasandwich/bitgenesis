import json
import tarfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
from scripts import run_v4_energy_continuation as run


class ContinuationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.probe = json.loads(Path('docs/research/results/v4-study-027-records.json').read_text())[0]
        p = cls.probe
        with tarfile.open('docs/research/results/v4-study-019-cases.tar.gz') as archive:
            cls.source = json.load(archive.extractfile(f"cases/seed-{p['seed']}-{p['mode']}-exchange-{str(p['exchange']).lower()}.json"))

    def test_continuation_ledger_and_branch_identity(self):
        source, probe = deepcopy(self.source), deepcopy(self.probe)
        result = run.run_branch(source, probe)
        t = probe['tick']
        self.assertEqual([r['tick'] for r in result['rows']], list(range(t+1,33)))
        self.assertEqual(result['initial']['units'], probe['treated']['units'])
        self.assertEqual(result['initial']['raw'], probe['treated']['raw'])
        child = result['initial']['injected_child']
        self.assertEqual(result['initial']['parents'][child], probe['identity'])
        self.assertEqual(result['child_fate']['birth_tick'], t)
        self.assertEqual(len(result['copy_parents'][0]['series']['descendant_genetic']),32)
        m = result['metrics']
        energy = sum(u['energy'] for u in result['initial']['units'] if u)
        self.assertEqual(m['final_energy'], energy+m['imported']-m['spent'])
        self.assertEqual(m['births'],sum(p['reason']=='formed' for r in result['rows'] for p in r['physical']['material']['proposals']))
        for row in result['rows']:
            self.assertEqual(sum(row['physical']['raw'])+sum(u is not None for u in row['physical']['units']),7)
            original=source['rows'][row['tick']-1]['physical']
            self.assertEqual([v['proposed'] for v in row['physical']['driven']['inputs']], [v['proposed'] for v in original['driven']['inputs']])
        self.assertEqual(result['delta'],{k:m[k]-result['control_metrics'][k] for k in m})
        self.assertEqual(source,self.source); self.assertEqual(probe,self.probe)
        self.assertEqual(set(run.record(result)), {'selection','added_energy','metrics','control_metrics','delta','child_fate'})

    def test_reject_wrong_source_and_added_energy(self):
        for key in ('seed','identity','added_energy'):
            bad=deepcopy(self.probe);bad[key]+=1
            with self.subTest(key=key),self.assertRaises(ValueError):run.run_branch(self.source,bad)

    def test_summary_signed_totals_and_strict_metrics(self):
        selections=json.loads(Path('docs/research/results/v4-study-027-records.json').read_text())
        records=[]
        for index,p in enumerate(selections):
            control={k:2 for k in run.METRICS}; control.update(genetic_ever=1,genetic_persistent10=0,longest_genetic=2,material_ever=1); metrics=dict(control)
            metrics['births']+=(-1,0,1)[index%3]
            records.append(dict(selection={k:p[k] for k in run.SELECTION_KEYS},added_energy=p['added_energy'],
                metrics=metrics,control_metrics=control,delta={k:metrics[k]-control[k] for k in metrics},
                child_fate=dict(identity=7,birth_tick=p['tick'],death_tick=p['tick']+1,alive_final=False,direct_offspring=2,descendants_born=2,lineage_living_final=2,observed_alive_finals=1)))
        cells=run.summarize(records)
        self.assertEqual([c['n'] for c in cells],[21,5,21,5])
        self.assertEqual(sum(c['positive']['births']+c['negative']['births']+c['tie']['births'] for c in cells),52)
        self.assertTrue(all(c['child_alive_final']==0 and c['child_reproduced']==c['lineage_alive_final']==c['n'] for c in cells))
        for kind in ('missing','reverse','bool','delta','negative','copy','fate','selection'):
            bad=deepcopy(records)
            if kind=='missing':bad.pop()
            if kind=='reverse':bad.reverse()
            if kind=='bool':bad[0]['metrics']['births']=True
            if kind=='delta':bad[0]['delta']['births']+=1
            if kind=='negative':bad[0]['metrics']['spent']=-1
            if kind=='copy':bad[0]['metrics']['genetic_ever']=0
            if kind=='fate':bad[0]['child_fate']['observed_alive_finals']=2
            if kind=='selection':bad[0]['selection']['extra']=0
            with self.subTest(kind=kind),self.assertRaises(ValueError):run.summarize(bad)

    def test_initial_failure_preserves_hash_inventory(self):
        import tempfile,types,sys,hashlib
        def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);out=root/'run';present=root/'present';missing=root/'missing';present.write_text('unchanged')
            helper=types.SimpleNamespace(input_paths=lambda errors:[str(present),str(missing)],
                bindings=lambda:(_ for _ in ()).throw(ValueError('bad binding')),digest=digest,
                source_cases=lambda:iter([]),read=lambda p:json.loads(p.read_text()),save=lambda p,v:p.write_text(json.dumps(v)))
            def git(command,**kwargs):return '' if command[1]=='status' else 'a'*40
            with patch.object(run,'OUTPUT',out),patch.object(run.subprocess,'check_output',git),patch.dict(sys.modules,{'scripts.energy_continuation_inputs':helper}):
                with self.assertRaisesRegex(ValueError,'bad binding'):run.main()
                with self.assertRaises(FileExistsError):run.main()
            meta=json.loads((out/'metadata.json').read_text())
            self.assertEqual(meta['status'],'failed')
            self.assertEqual(meta['input_paths'],[str(present),str(missing)])
            self.assertEqual(meta['input_sha256'],{str(present):digest(present)})
            self.assertEqual(meta['input_sha256_after'],meta['input_sha256'])
            self.assertIn(str(missing),meta['input_read_errors_before']);self.assertIn(str(missing),meta['input_read_errors'])
            self.assertEqual(meta['output_sha256'],{'records.json':digest(out/'records.json')})
            self.assertEqual((meta['new_full_world_steps'],meta['new_phase_transitions']),(0,0))

    def test_failed_observation_counts_completed_native_step(self):
        original_accept=run.Observer.accept
        def accept(observer,physical):
            if physical['tick']==self.probe['tick']+1:raise ValueError('after native step')
            return original_accept(observer,physical)
        before=run._full_world_steps
        with patch.object(run.Observer,'accept',accept):
            with self.assertRaisesRegex(ValueError,'after native step'):run.run_branch(self.source,self.probe)
        self.assertEqual(run._full_world_steps-before,1)

    def test_final_write_budget_and_failed_steps_metadata(self):
        import tempfile,types,sys,hashlib
        p=dict(self.probe);p['tick']=-964
        case=dict(mode=p['mode'],exchange=p['exchange'],seed=p['seed'])
        key=(p['genotype'],p['mode'],p['exchange'],p['seed'])
        for fail in (False,True):
            with self.subTest(fail=fail),tempfile.TemporaryDirectory() as directory:
                out=Path(directory)/'run';expired=False
                def save(path,value):
                    nonlocal expired
                    path.write_text(json.dumps(value))
                    if path.name=='metadata.json' and value['status']=='complete':expired=True
                def branch(source,probe):
                    run._full_world_steps+=1 if fail else 996
                    if fail:raise ValueError('after one step')
                    return {}
                helper=types.SimpleNamespace(input_paths=lambda errors:[],bindings=lambda:{},
                    digest=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest(),
                    source_cases=lambda:iter([(p['genotype'],Path('fixture'))]),
                    read=lambda path:[p] if path.name=='records.json' else case,save=save)
                def git(command,**kwargs):return '' if command[1]=='status' else 'a'*40
                with patch.object(run,'OUTPUT',out),patch.object(run.subprocess,'check_output',git),patch.object(run.time,'monotonic',side_effect=lambda:601 if expired else 0),patch.object(run,'ordered_selection'),patch.object(run,'run_branch',side_effect=branch),patch.object(run,'record',return_value={}),patch.object(run,'summarize',return_value=[]),patch.object(run.opportunities,'GRID',[key]),patch.dict(sys.modules,{'scripts.energy_continuation_inputs':helper}):
                    with self.assertRaisesRegex(ValueError,'after one step' if fail else 'bounded execution'):run.main()
                meta=json.loads((out/'metadata.json').read_text())
                self.assertEqual(meta['status'],'failed')
                self.assertEqual(meta['new_full_world_steps'],1 if fail else 996)
                self.assertEqual(meta['completed_branches'],0 if fail else 1)
