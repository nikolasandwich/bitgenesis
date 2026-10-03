import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
from scripts import verify_v4_copy_members as v


def fixture(groups=None):
    groups=groups or [[[0,1],[3,4]],[[0,1],[3,4]]]
    def snap(gs):
        ids=[None]*256;units=[None]*256
        for k,g in enumerate(gs):
            for offset,i in enumerate(g):
                s=16*(2+k*4)+2+offset;ids[s]=i
                units[s]=dict(material=0,program=[0]*4)
        return ids,units
    ids,units=snap([[0,1]]);rows=[]
    for tick,gs in enumerate(groups,1):
        final_ids,final_units=snap(gs)
        rows.append(dict(tick=tick,site_ids=final_ids,physical=dict(units=final_units)))
    return dict(seed=120000,mode='random-direction',exchange=False,config=dict(width=16,height=16),
        initial=dict(site_ids=ids,units=units),rows=rows,
        final=dict(site_ids=final_ids,units=final_units,parents=[None,None,0,0,1,3,4,5,6]),
        summary=dict(genetic_counts=[len(g) for g in groups],episodes=[[1,len(groups)]]))


class MemberTests(unittest.TestCase):
    def test_original_new_depth_and_roots(self):
        r=v.recount(fixture([[[0,1],[5,6]]]),'sample')
        self.assertEqual(r['steps'][0]['copies'],[
            dict(members=[0,1],original_members=[0,1],depths=[0,0],founder_roots=[0,1],all_new=False),
            dict(members=[5,6],original_members=[],depths=[2,2],founder_roots=[0,1],all_new=True)])
        self.assertEqual(r['steps'][0]['new_only_count'],1)
        self.assertEqual(r['episodes'][0]['max_same_pair_run'],1)
        mixed=v.recount(fixture([[[0,1],[3,6]]]),'sample')['steps'][0]['copies'][1]
        self.assertEqual(mixed['depths'],[1,2])

    def test_rotating_three_groups_and_stable_pair(self):
        r=v.recount(fixture([[[0,1],[3,4],[5,6]],[[0,1],[5,6],[7,8]],[[0,1],[3,4],[7,8]]]),'sample')
        self.assertEqual(r['episodes'][0],dict(start=1,end=3,length=3,right_censored=True,
            stable_groups=[[0,1]],stable_pair=False,max_same_pair_run=2))
        self.assertEqual(r['new_episodes'],[[1,3]])
        r=v.recount(fixture([[[0,1],[3,4],[5,6]],[[0,1],[3,4],[7,8]]]),'sample')
        self.assertTrue(r['episodes'][0]['stable_pair'])
        self.assertEqual(r['episodes'][0]['max_same_pair_run'],2)

    def test_new_persistence_closed_and_negative(self):
        gs=[[[3,4],[5,6]]]*10+[[[0,1]]]
        c=fixture(gs);c['summary']['episodes']=[[1,10]]
        r=v.recount(c,'sample');self.assertTrue(r['new_persistent10'])
        self.assertEqual(r['new_longest'],10);self.assertFalse(r['episodes'][0]['right_censored'])
        c=fixture([[[0,1]]]);c['summary']['episodes']=[]
        r=v.recount(c,'sample');self.assertEqual(r['episodes'],[]);self.assertEqual(r['new_longest'],0)

    def test_lineage_geometry_and_old_summary_tampering(self):
        for mutate in (lambda c:c['final']['parents'].__setitem__(3,3),
                       lambda c:c['final']['parents'].__setitem__(0,1),
                       lambda c:c['summary']['genetic_counts'].__setitem__(0,0),
                       lambda c:c['rows'][0]['physical']['units'][98]['program'].__setitem__(0,9)):
            c=fixture();mutate(c)
            with self.assertRaises(ValueError):v.recount(c,'sample')

    def test_old_runner_controls(self):
        from scripts.run_v4_copy_control import run_case
        for name in ('constructed-off','constructed-on','no-raw-off'):
            c=run_case(name);r=v.recount(c,'control-'+name)
            self.assertEqual(len(r['steps']),32)
            self.assertEqual([len(s['copies']) for s in r['steps']],c['summary']['genetic_counts'])


class MainTests(unittest.TestCase):
    def setup_output(self,root):
        cases=[];records=[]
        for index,label in enumerate(v.LABELS):
            case=fixture([[[0,1],[3,4]]]*32)
            if index<120:
                seed,mode,exchange=v.GRID[index];case.update(seed=seed,mode=mode,exchange=exchange)
            else:
                name=v.CONTROLS[index-120];case.update(name=name,exchange=name=='constructed-on',raw_tokens=0 if name=='no-raw-off' else 4)
            cases.append((label,case));records.append(v.recount(case,label))
        def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
        bound={f'source-{i}':'a'*64 for i in range(202)}
        bound['scripts/verify_v4_copy_members.py']=digest(Path(v.__file__))
        helper=types.SimpleNamespace(bindings=lambda:bound.copy(),digest=digest,
            read=lambda path:json.loads(Path(path).read_text()),source_cases=lambda:iter(copy.deepcopy(cases)))
        for name,value in [('records.json',records),('summary.json',v.aggregate(records))]:(root/name).write_text(json.dumps(value))
        meta=dict(status='complete',planned_cases=123,completed_cases=123,saved_steps=3936,new_simulation_steps=0,
            new_environment_sources=0,reused_environment_sources=20,reused_deterministic_controls=3,new_independent_initial_worlds=0,
            time_limit_seconds=300,storage_limit_bytes=33554432,git_commit='a'*40,elapsed_seconds=1,
            input_sha256=bound,input_sha256_after=bound,
            output_sha256={name:digest(root/name) for name in ('records.json','summary.json')})
        (root/'metadata.json').write_text(json.dumps(meta))
        return helper,meta,cases

    def test_main_all_sources_exclusive_proof(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);helper,meta,cases=self.setup_output(root)
            summary=helper.read(root/'summary.json')
            self.assertEqual([c['cases'] for c in summary['cells']],[20]*6)
            self.assertEqual([c['cases'] for c in summary['controls']],[1]*3)
            self.assertEqual(summary['cells'][0]['stable_pair_episodes'],20)
            with patch.object(v,'OUTPUT',root),patch.dict(sys.modules,{'scripts.copy_member_inputs':helper}),patch('builtins.print'):
                v.main();proof=helper.read(root/'independent-verification.json')
                self.assertEqual((proof['cases'],proof['saved_steps'],proof['input_files']),(123,3936,203))
                original=(root/'independent-verification.json').read_bytes()
                with self.assertRaises(FileExistsError):v.main()
                self.assertEqual((root/'independent-verification.json').read_bytes(),original)
                self.assertFalse((root/'verification-failure.json').exists())

    def test_tampered_fields_summary_and_hash_rejected_with_retained_failure(self):
        for kind in ('depth','root','stable_pair','summary','hash','identity','order','binding','source_lineage','count'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);helper,meta,cases=self.setup_output(root)
                records=helper.read(root/'records.json')
                if kind=='depth':records[0]['steps'][0]['copies'][1]['depths'][0]=9
                if kind=='root':records[0]['steps'][0]['copies'][1]['founder_roots']=[0]
                if kind=='stable_pair':records[0]['episodes'][0]['stable_pair']=False
                if kind in ('depth','root','stable_pair','hash'):
                    if kind=='hash':records[0]['new_longest']=9
                    (root/'records.json').write_text(json.dumps(records))
                    if kind!='hash':meta['output_sha256']['records.json']=helper.digest(root/'records.json')
                if kind=='summary':
                    summary=helper.read(root/'summary.json');summary['controls'][0]['double_steps']=0
                    (root/'summary.json').write_text(json.dumps(summary));meta['output_sha256']['summary.json']=helper.digest(root/'summary.json')
                if kind=='identity':cases[0][1]['seed']=120001
                if kind=='order':cases[0],cases[1]=cases[1],cases[0]
                if kind=='source_lineage':cases[0][1]['final']['parents'][3]=1
                if kind=='count':cases[0][1]['summary']['genetic_counts'][0]=0
                if kind=='binding':
                    bound=helper.bindings();bound['scripts/verify_v4_copy_members.py']='0'*64
                    helper.bindings=lambda:bound.copy();meta['input_sha256']=meta['input_sha256_after']=bound
                (root/'metadata.json').write_text(json.dumps(meta))
                with patch.object(v,'OUTPUT',root),patch.dict(sys.modules,{'scripts.copy_member_inputs':helper}):
                    with self.assertRaises(ValueError):v.main()
                    failure=(root/'verification-failure.json').read_bytes()
                    with self.assertRaises(ValueError):v.main()
                    self.assertEqual((root/'verification-failure.json').read_bytes(),failure)
                self.assertFalse((root/'independent-verification.json').exists())

    def test_short_binding_inventory_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);helper,meta,cases=self.setup_output(root)
            helper.bindings=lambda:{}
            with patch.object(v,'OUTPUT',root),patch.dict(sys.modules,{'scripts.copy_member_inputs':helper}),self.assertRaisesRegex(ValueError,'203'):v.main()


class MatchingTests(unittest.TestCase):
    def test_periodic_full_components_material_program_rotation_and_ancestry(self):
        def unit(material=0,program=None):return dict(material=material,program=program or [0]*4)
        target=((5,5,0,(0,0,0,0)),(6,5,0,(0,0,0,0)))
        state={3:(15,unit()),4:(0,unit())};roots={3:0,4:1,5:0}
        self.assertEqual(v.matching_groups(state,roots,target,16,16),[[3,4]])
        for changed in ({3:(0,unit()),4:(16,unit())},
                        {3:(15,unit()),4:(0,unit(program=[0,0,0,1]))},
                        {3:(15,unit()),4:(0,unit()),5:(1,unit())},
                        {3:(15,unit(1)),4:(0,unit(1))}):
            self.assertEqual(v.matching_groups(changed,roots,target,16,16),[])
        roots[4]=2
        self.assertEqual(v.matching_groups(state,roots,target,16,16),[])


if __name__=='__main__':unittest.main()
