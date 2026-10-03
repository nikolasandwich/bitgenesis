import copy
import unittest
from pathlib import Path
import tempfile
import json
import hashlib
import types
import sys
from unittest.mock import patch
from scripts import verify_v4_copy_episodes as v


def fixture():
    def snapshot(mapping):
        ids=[None]*256;units=[None]*256
        for identity,site in mapping.items():
            ids[site]=identity
            material=3 if identity==2 else 0
            units[site]=dict(material=material,program=[material]*4,energy=1)
        return ids,units
    mappings=[{0:85,1:86,2:204},{0:85,1:86,2:204,3:117,4:118,5:101},
              {0:85,1:86,2:204,3:117,4:118,6:101},{0:85,1:86,2:204,3:117,4:118}]
    ids,units=snapshot(mappings[0]);rows=[]
    for tick,(old,new) in enumerate(zip(mappings,mappings[1:]),1):
        ids2,units2=snapshot(new)
        rows.append(dict(tick=tick,site_ids=ids2,physical=dict(units=units2,material=dict(
            dissolved=[old[i] for i in old.keys()-new.keys()],
            proposals=[dict(reason='formed',source=85,target=new[i]) for i in sorted(new.keys()-old.keys())]))))
    return dict(seed=120000,mode='random-direction',exchange=False,config=dict(width=16,height=16),
                initial=dict(site_ids=ids,units=units),rows=rows,
                final=dict(site_ids=ids2,units=units2,parents=[None,None,None,0,0,0,0]),
                summary=dict(genetic_counts=[0,0,2],episodes=[[3,3]]))


class EpisodeVerifierTests(unittest.TestCase):
    def test_hidden_compound_and_right_censoring(self):
        record=v.recount(fixture())
        self.assertEqual(record['steps'][1]['crossings'],[True,False,False,True])
        self.assertTrue(record['steps'][1]['hidden'])
        self.assertEqual(record['steps'][1]['dissolved'],[[0,1],[3,4]])
        self.assertEqual(record['steps'][1]['births'],[6])
        self.assertEqual(record['steps'][1]['deaths'],[5])
        self.assertEqual(record['episodes'],[dict(start=3,end=3,length=1,right_censored=True,start_step=record['steps'][2],exit_step=None)])

    def test_tampered_events_survivor_geometry_program_and_summary(self):
        mutations=[lambda c:c['rows'][1]['physical']['material']['dissolved'].clear(),
                   lambda c:c['rows'][0]['physical']['material']['proposals'].pop(),
                   lambda c:c['rows'][1]['physical']['units'][85]['program'].__setitem__(0,2),
                   lambda c:c['rows'][1]['site_ids'].__setitem__(87,0),
                   lambda c:c['summary']['genetic_counts'].__setitem__(0,2),
                   lambda c:c['rows'][0]['physical']['material']['proposals'][0].__setitem__('source',204)]
        for mutate in mutations:
            case=fixture();mutate(case)
            with self.subTest(mutate=mutate),self.assertRaises((ValueError,AssertionError)):
                v.recount(case)

    def test_zero_and_six_cells(self):
        case=fixture();case['rows']=case['rows'][:2];case['final']['site_ids']=case['rows'][-1]['site_ids'];case['final']['units']=case['rows'][-1]['physical']['units']
        case['summary']=dict(genetic_counts=[0,0],episodes=[])
        record=v.recount(case);self.assertEqual(record['episodes'],[])
        records=[]
        for seed in range(120000,120020):
            for mode in v.MODES:
                for exchange in (False,True):
                    r=copy.deepcopy(record);r.update(seed=seed,mode=mode,exchange=exchange);records.append(r)
        cells=v.aggregate(records)
        self.assertEqual(len(cells),6)
        for c in cells:
            self.assertEqual(c['cases'],20);self.assertEqual(c['hidden'],20)
            self.assertEqual(c['dissolution_up'],20);self.assertEqual(c['formation_down'],20)
        with self.assertRaises(ValueError):v.aggregate(records[:-1])

    def test_periodic_material_and_full_program_matching(self):
        def unit(program=None):return dict(material=0,program=program or [0]*4)
        target=((5,5,0,(0,0,0,0)),(6,5,0,(0,0,0,0)))
        state={3:(15,unit()),4:(0,unit())};owners={3:0,4:1,5:0}
        self.assertEqual(v.matches(state,owners,target,16,16),[[3,4]])
        state[4]=(0,unit([0,0,0,1]));self.assertEqual(v.matches(state,owners,target,16,16),[])
        state[4]=(0,unit());state[5]=(1,unit())
        self.assertEqual(v.matches(state,owners,target,16,16),[])
        del state[5];owners[4]=2
        self.assertEqual(v.matches(state,owners,target,16,16),[])
        state={3:(0,unit()),4:(16,unit())};owners[4]=1
        self.assertEqual(v.matches(state,owners,target,16,16),[])

    def test_closed_episode_boundary_and_down_crossing(self):
        case=fixture();last=copy.deepcopy(case['rows'][2]);last['tick']=4
        last['site_ids'][117]=None;last['physical']['units'][117]=None
        last['physical']['material']=dict(dissolved=[117],proposals=[])
        case['rows'].append(last);case['final']['site_ids']=last['site_ids'];case['final']['units']=last['physical']['units']
        case['summary']=dict(genetic_counts=[0,0,2,1],episodes=[[3,3]])
        record=v.recount(case);episode=record['episodes'][0]
        self.assertFalse(episode['right_censored']);self.assertEqual(episode['exit_step'],record['steps'][3])
        self.assertEqual(record['steps'][3]['crossings'],[False,True,False,False])

    def test_formation_up(self):
        case=fixture();row=case['rows'][0];case['rows']=[row]
        row['site_ids'][101]=None;row['physical']['units'][101]=None
        row['physical']['material']['proposals']=[p for p in row['physical']['material']['proposals'] if p['target']!=101]
        case['final']['site_ids']=row['site_ids'];case['final']['units']=row['physical']['units']
        case['summary']=dict(genetic_counts=[2],episodes=[[1,1]])
        self.assertEqual(v.recount(case)['steps'][0]['crossings'],[False,False,True,False])

    def test_dissolved_source_cannot_parent_same_step_birth(self):
        case=fixture()
        case['rows'][1]['physical']['material']['proposals'][0]['source']=101
        case['final']['parents'][6]=5
        with self.assertRaises(ValueError):v.recount(case)

    def test_old_runner_case_has_full_32_steps(self):
        from scripts.run_v4_copy_ablation import run_case
        record=v.recount(run_case(120000,'random-direction',False))
        self.assertEqual(len(record['steps']),32)


class VerifierMainTests(unittest.TestCase):
    def setup_output(self,root):
        cases={};records=[]
        for seed,mode,exchange in v.GRID:
            case=fixture();last=copy.deepcopy(case['rows'][-1])
            last['physical']['material']=dict(dissolved=[],proposals=[])
            for tick in range(4,33):
                row=copy.deepcopy(last);row['tick']=tick;case['rows'].append(row)
            case['summary']=dict(genetic_counts=[0,0]+[2]*30,episodes=[[3,32]])
            case.update(seed=seed,mode=mode,exchange=exchange)
            path=Path(f'source-{seed}-{mode}-{exchange}.json');cases[path]=case;records.append(v.recount(case))
        def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
        bound={'scripts/verify_v4_copy_episodes.py':digest(Path(v.__file__))}
        helper=types.SimpleNamespace(bindings=lambda:bound.copy(),digest=digest,
            read=lambda path:copy.deepcopy(cases[path]) if path in cases else json.loads(path.read_text()),source_cases=lambda:iter(cases))
        for name,value in [('records.json',records),('summary.json',v.aggregate(records))]:
            (root/name).write_text(json.dumps(value))
        meta=dict(status='complete',planned_cases=120,completed_cases=120,saved_steps=3840,
                  new_simulation_steps=0,new_environment_sources=0,reused_environment_sources=20,
                  new_independent_initial_worlds=0,time_limit_seconds=300,storage_limit_bytes=33554432,
                  git_commit='a'*40,elapsed_seconds=1,input_sha256=bound,input_sha256_after=bound,
                  output_sha256={name:digest(root/name) for name in ('records.json','summary.json')})
        (root/'metadata.json').write_text(json.dumps(meta))
        return helper,meta

    def test_independent_main_full_grid_and_exclusive_proof(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);helper,meta=self.setup_output(root)
            with patch.object(v,'OUTPUT',root),patch.dict(sys.modules,{'scripts.copy_episode_inputs':helper}),patch('builtins.print'):
                v.main()
                proof=json.loads((root/'independent-verification.json').read_text())
                self.assertEqual((proof['cases'],proof['saved_steps']),(120,3840))
                with self.assertRaises(FileExistsError):v.main()

    def test_output_hash_and_stage_tampering_rejected(self):
        for rebound in (False,True):
            with self.subTest(rebound=rebound),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);helper,meta=self.setup_output(root)
                records=json.loads((root/'records.json').read_text());records[0]['steps'][1]['dissolved']=[]
                (root/'records.json').write_text(json.dumps(records))
                if rebound:
                    meta['output_sha256']['records.json']=helper.digest(root/'records.json')
                    (root/'metadata.json').write_text(json.dumps(meta))
                with patch.object(v,'OUTPUT',root),patch.dict(sys.modules,{'scripts.copy_episode_inputs':helper}),self.assertRaises(ValueError):v.main()
                self.assertFalse((root/'independent-verification.json').exists())

    def test_changed_verifier_binding_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);helper,meta=self.setup_output(root)
            helper.bindings=lambda:{'scripts/verify_v4_copy_episodes.py':'0'*64}
            meta['input_sha256']=meta['input_sha256_after']=helper.bindings()
            (root/'metadata.json').write_text(json.dumps(meta))
            with patch.object(v,'OUTPUT',root),patch.dict(sys.modules,{'scripts.copy_episode_inputs':helper}),self.assertRaises(ValueError):v.main()

if __name__=='__main__':unittest.main()
