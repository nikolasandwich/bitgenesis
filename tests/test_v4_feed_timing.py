import json
import tarfile
import unittest
from copy import deepcopy
from pathlib import Path
from scripts import analyze_v4_feed_timing as run


class FeedTimingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with tarfile.open('docs/research/results/v4-study-028-cases.tar.gz') as archive:
            cls.branches=[json.load(archive.extractfile(f'cases/branch-{i:03d}.json')) for i in (0,21,26,47)]
        all_energy=json.loads(Path('docs/research/results/v4-study-029-records.json').read_text())
        cls.energy=[all_energy[i] for i in (0,21,26,47)]
        cls.selections=[r['selection'] for r in all_energy]

    def test_saved_full_window_and_energy(self):
        original=deepcopy(self.branches)
        for branch,energy in zip(self.branches,self.energy):
            r=run.analyze_branch(branch,energy)
            self.assertEqual([x['tick'] for x in r['rows']],list(range(r['birth_tick']+1,33)))
            self.assertEqual(r['totals']['child_accepted'],energy['totals']['accepted'])
            self.assertEqual(len(r['totals']),13)
            for row in r['rows']:
                self.assertEqual(row['site_accepted']+row['rejected'],row['proposed'])
                self.assertEqual(row['child_accepted']+row['other_accepted'],row['site_accepted'])
        self.assertEqual(self.branches,original)

    def engineered(self):
        b=deepcopy(self.branches[0]); e=deepcopy(self.energy[0]); child=e['child_identity']; site=e['child_site']; death=e['death_tick']
        for saved in b['rows']:
            tick=saved['tick']; supplied=saved['physical']['driven']['inputs'][site]
            supplied.update(proposed=8,accepted=8 if tick in (death,death+2) else 0,rejected=0 if tick in (death,death+2) else 8)
            saved['site_ids'][site]=child if tick<death else None if tick==death else 999
        for row in e['rows']:
            row.update(proposed=8,accepted=8 if row['tick']==death else 0)
        e['totals']['accepted']=8
        return b,e

    def test_death_input_precedes_dissolution_and_replacement(self):
        b,e=self.engineered(); r=run.analyze_branch(b,e); by_tick={x['tick']:x for x in r['rows']}; death=r['death_tick']
        self.assertEqual(by_tick[death]['child_accepted'],8)
        self.assertEqual(by_tick[death+1]['identity_before'],None)
        self.assertEqual(by_tick[death+1]['rejected'],8)
        self.assertEqual(by_tick[death+2]['other_accepted'],8)
        self.assertEqual(r['totals']['child_accepted'],8)
        self.assertEqual(r['first_after_death_tick'],death+1)

    def test_reject_saved_corruption(self):
        for kind in ('tick','identity','resurrection','proposal','accepted','empty','energy','selection','death'):
            b,e=self.engineered(); site=e['child_site']; death=e['death_tick']; index=death-e['birth_tick']
            if kind=='tick':b['rows'].pop()
            if kind=='identity':b['rows'][0]['site_ids'][site]=999
            if kind=='resurrection':b['rows'][-1]['site_ids'][site]=e['child_identity']
            if kind=='proposal':b['rows'][0]['physical']['driven']['inputs'][site]['proposed']=True
            if kind=='accepted':b['rows'][0]['physical']['driven']['inputs'][site]['accepted']=1
            if kind=='empty':b['rows'][index]['physical']['driven']['inputs'][site].update(accepted=8,rejected=0)
            if kind=='energy':e['rows'][0]['proposed']=0
            if kind=='selection':e['selection']['seed']+=1
            if kind=='death':e['death_tick']+=1
            with self.subTest(kind=kind),self.assertRaises(ValueError):run.analyze_branch(b,e)

    def summary_records(self):
        template=run.analyze_branch(*self.engineered()); result=[]
        for selection in self.selections:
            r=deepcopy(template); shift=selection['tick']-r['birth_tick'];r['selection']=deepcopy(selection)
            r['birth_tick']+=shift;r['death_tick']+=shift
            r['rows']=[]
            for tick in range(r['birth_tick']+1,33):
                phase='before_death' if tick<r['death_tick'] else 'death' if tick==r['death_tick'] else 'after_death'
                r['rows'].append(dict(tick=tick,phase=phase,identity_before=r['child_identity'] if tick<=r['death_tick'] else None,
                    identity_after=r['child_identity'] if tick<r['death_tick'] else None,proposed=8,site_accepted=0,child_accepted=0,other_accepted=0,rejected=8))
            r['totals']=run.totals(r['rows']);r['first_proposed_tick']=r['birth_tick']+1;r['first_proposed_phase']=r['rows'][0]['phase'];r['first_after_death_tick']=r['death_tick']+1
            result.append(r)
        return result

    def test_pairs_and_strict_schema(self):
        records=self.summary_records(); summary=run.summarize(records)
        self.assertEqual(len(summary['pairs']),26)
        self.assertEqual([c['n'] for c in summary['cells']],[21,5,21,5])
        self.assertTrue(all(p['phase_shift_ticks']==[] for p in summary['pairs']))
        for kind in ('missing','duplicate','site','proposal','total','extra','boolean'):
            bad=deepcopy(records)
            if kind=='missing':bad.pop()
            if kind=='duplicate':bad[1]=deepcopy(bad[0])
            if kind=='site':bad[26]['child_site']+=1
            if kind=='proposal':bad[26]['rows'][-1].update(proposed=0,rejected=0);bad[26]['totals']=run.totals(bad[26]['rows'])
            if kind=='total':bad[0]['totals']['steps']+=1
            if kind=='extra':bad[0]['rows'][0]['extra']=0
            if kind=='boolean':bad[0]['rows'][0]['proposed']=True
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
            with patch.object(run,'OUTPUT',out),patch.object(run.subprocess,'check_output',git),patch.dict(sys.modules,{'scripts.feed_timing_inputs':helper}):
                with self.assertRaisesRegex(ValueError,'bad binding'):run.main()
                with self.assertRaises(FileExistsError):run.main()
            meta=json.loads((out/'metadata.json').read_text())
            self.assertEqual(meta['status'],'failed');self.assertEqual(meta['input_paths'],[str(present),str(missing)])
            self.assertEqual(meta['input_sha256'],{str(present):digest(present)})
            self.assertEqual(meta['input_sha256_after'],meta['input_sha256'])
            self.assertIn(str(missing),meta['input_read_errors_before']);self.assertIn(str(missing),meta['input_read_errors'])
            self.assertEqual(meta['output_sha256'],{'records.json':digest(out/'records.json')})
            self.assertEqual((meta['completed_branches'],meta['site_steps'],meta['new_full_world_steps']),(0,0,0))

    def test_partial_progress_and_post_write_budget(self):
        import hashlib,sys,tempfile,types
        from unittest.mock import patch
        # Stub orchestration only: no production extraction of the full queue.
        for final_budget in (False,True):
            with self.subTest(final_budget=final_budget),tempfile.TemporaryDirectory() as directory:
                out=Path(directory)/'out'; expired=False; calls=0
                inventory=[str(i) for i in range(491)]; before={p:'a'*64 for p in inventory}
                def digest(path):
                    return hashlib.sha256(Path(path).read_bytes()).hexdigest() if isinstance(path,Path) else before[path]
                def save(path,value):
                    nonlocal expired
                    path.write_text(json.dumps(value))
                    if path.name=='metadata.json' and value['status']=='complete':expired=True
                def read(path):
                    if path.name=='records.json':return [None]*52
                    return dict(rows=[None]*(996 if path.name=='0' else 0))
                def analyze(branch,energy):
                    nonlocal calls
                    calls+=1
                    if not final_budget and calls==2:raise ValueError('second branch failed')
                    return dict(child_identity=1,rows=[dict(identity_before=1)]*(268 if calls==1 else 0)+[dict(identity_before=None)]*(728 if calls==1 else 0))
                helper=types.SimpleNamespace(input_paths=lambda errors:inventory,bindings=lambda:dict(before),digest=digest,
                    source_cases=lambda:[Path(str(i)) for i in range(52)],read=read,save=save)
                def git(command,**kwargs):return '' if command[1]=='status' else 'a'*40
                with patch.object(run,'OUTPUT',out),patch.object(run.subprocess,'check_output',git),patch.object(run.time,'monotonic',side_effect=lambda:301 if expired else 0),patch.object(run,'analyze_branch',side_effect=analyze),patch.object(run,'summarize',return_value=dict(cells=[dict(totals=dict(steps=n)) for n in (64,26,129,49)])),patch.dict(sys.modules,{'scripts.feed_timing_inputs':helper}):
                    with self.assertRaisesRegex(ValueError,'bounded execution' if final_budget else 'second branch failed'):run.main()
                meta=json.loads((out/'metadata.json').read_text())
                self.assertEqual(meta['status'],'failed')
                self.assertEqual(meta['completed_branches'],52 if final_budget else 1)
                self.assertEqual((meta['saved_world_steps'],meta['site_steps']),(996,996))
                self.assertEqual((meta['new_full_world_steps'],meta['new_phase_transitions']),(0,0))
                self.assertEqual(meta['input_sha256_after'],meta['input_sha256'])

    def test_phase_shift_and_all_first_classes(self):
        records=self.summary_records()
        # Extend one paired child's saved lifetime by one step without changing tickets.
        r=records[26];r['death_tick']+=1
        for row in r['rows']:
            row['phase']=run.phase(row['tick'],r['death_tick'])
            row['identity_before']=r['child_identity'] if row['tick']<=r['death_tick'] else None
            row['identity_after']=r['child_identity'] if row['tick']<r['death_tick'] else None
        r['totals']=run.totals(r['rows']);r.update(run.firsts(r['rows']))
        summary=run.summarize(records)
        self.assertEqual(summary['pairs'][0]['phase_shift_ticks'],[records[0]['death_tick'],r['death_tick']])
        self.assertEqual(summary['pairs'][0]['delta']['proposed'],0)
        for first_phase in (None,'before_death','death','after_death'):
            r=deepcopy(records[0])
            for row in r['rows']:
                row['proposed']=row['rejected']=8 if row['phase']==first_phase else 0
            r['totals']=run.totals(r['rows']);r.update(run.firsts(r['rows']))
            run.validate_record(r)
            self.assertEqual(r['first_proposed_phase'],first_phase)
