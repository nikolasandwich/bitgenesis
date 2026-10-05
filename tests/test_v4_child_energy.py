import json
import tarfile
import unittest
from copy import deepcopy
from pathlib import Path
from scripts import analyze_v4_child_energy as run


class ChildEnergyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with tarfile.open('docs/research/results/v4-study-028-cases.tar.gz') as archive:
            cls.branches = [json.load(archive.extractfile(f'cases/branch-{i:03d}.json')) for i in (0,21,26,47)]

    def test_saved_lifetimes_and_exact_ledger(self):
        original = deepcopy(self.branches)
        for branch, steps in zip(self.branches,(3,7,5,13)):
            record = run.analyze_branch(branch)
            self.assertEqual(record['totals']['steps'],steps)
            self.assertEqual(record['initial_energy'],5)
            self.assertEqual(record['totals']['final_energy'],0)
            self.assertTrue(record['rows'][-1]['dissolved'])
            for row in record['rows']:
                self.assertEqual(row['energy_interaction'],row['energy_before']+row['accepted']-row['leakage']-row['bond_cost']+row['exchange_in']-row['exchange_out'])
        self.assertEqual(self.branches,original)
        first=run.analyze_branch(self.branches[0])
        self.assertEqual(first['rows'][0]['bond_cost'],2)
        self.assertEqual(first['totals']['accepted'],0)

    def engineered(self):
        from dataclasses import asdict
        from bitgenesis.v4.heredity import HeritableUnit
        from bitgenesis.v4.hereditary_growing import step
        from bitgenesis.v4.lineage import Observer
        units=[None]*9; units[1]=HeritableUnit(2,1,(2,2,2,2)); units[4]=HeritableUnit(0,5,(1,1,1,1))
        raw=[0]*9; raw[5]=1
        serialize=lambda values:json.loads(json.dumps([None if u is None else asdict(u) for u in values]))
        observer=Observer(serialize(units)); observer.tick=15; child=observer.alive[4]
        initial=dict(tick=15,units=serialize(units),site_ids=list(observer.alive),parents=[None,0],injected_child=child)
        rows=[]; death=None
        for tick in range(16,24):
            proposals=[0]*9; proposals[1]=16 if tick==22 else 1
            if tick==16:proposals[4]=12
            directions=[0]*9; directions[1]=2
            units,raw,event=step(units,raw,3,3,proposals,directions,[(999,0,1)]*9,exchange=False,mutation_per_thousand=0)
            physical=dict(tick=tick,units=serialize(units),raw=raw,**event)
            observer.accept(physical)
            rows.append(dict(tick=tick,physical=physical,site_ids=list(observer.alive)))
            if death is None and child not in observer.alive:death=tick
        selection=dict(self.branches[0]['selection']); selection.update(identity=0,site=1)
        self.assertEqual(death,22)
        self.assertIsNotNone(rows[6]['site_ids'][4])
        self.assertNotEqual(rows[6]['site_ids'][4],child)
        return dict(initial=initial,rows=rows,selection=selection,
                    child_fate=dict(identity=child,birth_tick=15,death_tick=death,alive_final=False))

    def test_formation_is_separate_from_offspring_and_replacement_stops_identity(self):
        r=run.analyze_branch(self.engineered())
        self.assertEqual(r['totals']['steps'],7)
        self.assertEqual((r['rows'][0]['formation_spent'],r['rows'][0]['offspring_energy'],r['rows'][0]['energy_after']),(5,5,6))
        self.assertEqual(r['rows'][0]['bond_cost'],0)
        self.assertEqual(r['rows'][-1]['energy_after'],0)

    def test_reject_inconsistent_identity_energy_and_death(self):
        for kind in ('identity','energy','death','site','root','ancestry'):
            b=deepcopy(self.branches[0]); site=b['initial']['site_ids'].index(b['initial']['injected_child'])
            if kind=='identity':b['rows'][0]['site_ids'][site]=999
            if kind=='energy':b['rows'][0]['physical']['interaction_units'][site]['energy']+=1
            if kind=='death':b['child_fate']['death_tick']+=1
            if kind=='root':b['selection']['root']=1
            if kind=='ancestry':b['initial']['parents'][b['selection']['identity']]=b['initial']['injected_child']
            if kind=='site':b['rows'][0]['site_ids'][site],b['rows'][0]['site_ids'][0]=b['rows'][0]['site_ids'][0],b['rows'][0]['site_ids'][site]
            with self.subTest(kind=kind),self.assertRaises(ValueError):run.analyze_branch(b)

    def summary_records(self):
        probes=json.loads(Path('docs/research/results/v4-study-027-records.json').read_text())
        template=run.analyze_branch(self.branches[0]); result=[]
        for probe in probes:
            r=deepcopy(template); r['selection']={k:probe[k] for k in template['selection']}; shift=probe['tick']-r['birth_tick']; r['birth_tick']+=shift;r['death_tick']+=shift
            for row in r['rows']:row['tick']+=shift
            result.append(r)
        return result

    def test_summary_complete_pairs_schema_and_zero_cases(self):
        records=self.summary_records(); result=run.summarize(records)
        self.assertEqual(set(result),{'cells','pairs'})
        self.assertEqual([c['n'] for c in result['cells']],[21,5,21,5])
        self.assertEqual(len(result['pairs']),26)
        self.assertEqual(result['pairs'][0]['homogeneous_index'],0)
        self.assertEqual(result['pairs'][0]['heterogeneous_index'],26)
        self.assertTrue(all(not any(p['delta'].values()) for p in result['pairs']))
        self.assertTrue(all(c['zero_accepted']==c['n'] for c in result['cells']))
        for kind in ('missing','duplicate','pair','total','bool','extra'):
            bad=deepcopy(records)
            if kind=='missing':bad.pop()
            if kind=='duplicate':bad[1]=deepcopy(bad[0])
            if kind=='pair':bad[26]['selection']['identity']+=1
            if kind=='total':bad[0]['totals']['accepted']+=1
            if kind=='bool':bad[0]['rows'][0]['accepted']=False
            if kind=='extra':bad[0]['rows'][0]['extra']=0
            with self.subTest(kind=kind),self.assertRaises(ValueError):run.summarize(bad)

    def test_failure_preserves_inventory_hashes_and_exclusive_directory(self):
        import hashlib,sys,tempfile,types
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); out=root/'out'; present=root/'present'; missing=root/'missing'; present.write_text('input')
            digest=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
            helper=types.SimpleNamespace(input_paths=lambda errors:[str(present),str(missing)],
                bindings=lambda:(_ for _ in ()).throw(ValueError('bad binding')),digest=digest,
                source_cases=lambda:[],read=lambda p:json.loads(p.read_text()),save=lambda p,v:p.write_text(json.dumps(v)))
            def git(command,**kwargs):return '' if command[1]=='status' else 'a'*40
            with patch.object(run,'OUTPUT',out),patch.object(run.subprocess,'check_output',git),patch.dict(sys.modules,{'scripts.child_energy_inputs':helper}):
                with self.assertRaisesRegex(ValueError,'bad binding'):run.main()
                with self.assertRaises(FileExistsError):run.main()
            meta=json.loads((out/'metadata.json').read_text())
            self.assertEqual(meta['status'],'failed');self.assertEqual(meta['input_paths'],[str(present),str(missing)])
            self.assertEqual(meta['input_sha256'],{str(present):digest(present)})
            self.assertEqual(meta['input_sha256_after'],meta['input_sha256'])
            self.assertIn(str(missing),meta['input_read_errors_before']);self.assertIn(str(missing),meta['input_read_errors'])
            self.assertEqual(meta['output_sha256'],{'records.json':digest(out/'records.json')})
            self.assertEqual((meta['completed_branches'],meta['child_steps'],meta['new_full_world_steps']),(0,0,0))

    def test_partial_progress_and_post_write_budget(self):
        import hashlib,sys,tempfile,types
        from unittest.mock import patch
        # Stub orchestration only: no production extraction of the full queue.
        for final_budget in (False,True):
            with self.subTest(final_budget=final_budget),tempfile.TemporaryDirectory() as directory:
                out=Path(directory)/'out'; expired=False; calls=0
                inventory=[str(i) for i in range(479)]; before={p:'a'*64 for p in inventory}
                def digest(path):
                    return hashlib.sha256(Path(path).read_bytes()).hexdigest() if isinstance(path,Path) else before[path]
                def save(path,value):
                    nonlocal expired
                    path.write_text(json.dumps(value))
                    if path.name=='metadata.json' and value['status']=='complete':expired=True
                def read(path):return dict(rows=[None]*(996 if path.name=='0' else 0))
                def analyze(branch):
                    nonlocal calls
                    calls+=1
                    if not final_budget and calls==2:raise ValueError('second branch failed')
                    return dict(rows=[None]*(268 if calls==1 else 0))
                helper=types.SimpleNamespace(input_paths=lambda errors:inventory,bindings=lambda:dict(before),digest=digest,
                    source_cases=lambda:[Path(str(i)) for i in range(52)],read=read,save=save)
                def git(command,**kwargs):return '' if command[1]=='status' else 'a'*40
                with patch.object(run,'OUTPUT',out),patch.object(run.subprocess,'check_output',git),patch.object(run.time,'monotonic',side_effect=lambda:301 if expired else 0),patch.object(run,'analyze_branch',side_effect=analyze),patch.object(run,'summarize',return_value=dict(cells=[dict(totals=dict(steps=n)) for n in (64,26,129,49)])),patch.dict(sys.modules,{'scripts.child_energy_inputs':helper}):
                    with self.assertRaisesRegex(ValueError,'bounded execution' if final_budget else 'second branch failed'):run.main()
                meta=json.loads((out/'metadata.json').read_text())
                self.assertEqual(meta['status'],'failed')
                self.assertEqual(meta['completed_branches'],52 if final_budget else 1)
                self.assertEqual((meta['saved_world_steps'],meta['child_steps']),(996,268))
                self.assertEqual((meta['new_full_world_steps'],meta['new_phase_transitions']),(0,0))
                self.assertEqual(meta['input_sha256_after'],meta['input_sha256'])
