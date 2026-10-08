"""Task2.2 synthetic independent-route evidence; never draws a study seed future."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
import signal
import tempfile
import time
import unittest
from unittest.mock import patch

from scripts import middle_withdrawal_inputs as inputs
from scripts import verify_v4_middle_withdrawal as verifier

COUNTS = dict(dictionary_physical_steps=0, producer_physical_steps=0, synthetic_future_ticks=0)


def setUpModule():
    global _physical, _draw
    _physical, _draw = verifier.physical_step, verifier.draw_future
    def physical(*args, **kwargs):
        result = _physical(*args, **kwargs)
        COUNTS['dictionary_physical_steps'] += 1
        return result
    def draw(streams, budget=lambda: None, progress=None, partial=None):
        partial = {} if partial is None else partial
        try:
            return _draw(streams, budget, progress, partial)
        finally:
            COUNTS['synthetic_future_ticks'] += len(partial.get('natural_tape', []))
    verifier.physical_step, verifier.draw_future = physical, draw


def tearDownModule():
    verifier.physical_step, verifier.draw_future = _physical, _draw
    print(json.dumps(dict(task='2.2', synthetic_seed=987654, **COUNTS,
                         real_study047_future_ticks=0, real_study047_physical_steps=0)))


def fixture():
    def person(i, site, material, parent=None, birth=0):
        return dict(id=i, site=site, birth_tick=birth, death_tick=None, parent=parent,
                    founder=i if parent is None else parent, generation=0 if parent is None else 1,
                    material=material, program=[material]*4, birth_energy=32, mutated=False,
                    offspring=1 if i in (0, 1) else 0)
    people = [person(0,85,0), person(1,86,0), person(2,204,3),
              person(3,117,0,0,20), person(4,118,0,1,20)]
    template = dict(tick=0, units=[None]*256, site_ids=[None]*256)
    for p in people[:3]:
        template['units'][p['site']] = dict(material=p['material'],energy=32,program=p['program'][:])
        template['site_ids'][p['site']] = p['id']
    units, ids, raw = [None]*256, [None]*256, [0]*256
    for p in people[2:]:
        units[p['site']] = dict(material=p['material'],energy=32,program=p['program'][:]); ids[p['site']] = p['id']
    for s in (85,86,101,102): raw[s] = 1
    state = dict(tick=32, units=units, raw=raw, site_ids=ids, individuals=people, parents=[p['parent'] for p in people])
    return dict(item=dict(encoding='homogeneous',seed=987654,trigger=True,t0=10,short_window=False,
                         selection=dict(offspring_ids=[3,4],exchange=False),boundary={'synthetic':True}),
                initial=state,template=template,
                prefix_initial=dict(tick=10,removals=[dict(identity=i,site=85+i,energy=32) for i in (0,1)],energy_export=64),
                prefix_rows=[dict(tick=t,copies=[]) for t in range(11,33)])


def tape():
    return tuple(dict(tick=t,directions=tuple([0]*256),feed_sites_draw_order=(1,2,3,4)) for t in range(33,65))


def environment():
    # Test oracle encodes the original documented seed construction, not verifier helpers.
    streams = {k: random.Random(int.from_bytes(hashlib.sha256(f'v4-copy-ablation-1:987654:{k}'.encode()).digest(),'big'))
               for k in ('directions','feeds')}
    originals = {m:dict(seed=987654,mode=m,exchange=False,config=dict(inputs.CONFIG),rows=[])
                 for m in ('random-direction','random-both')}
    past=[]
    for t in range(1,33):
        directions=[streams['directions'].randrange(4) for _ in range(256)]
        feeds=streams['feeds'].sample(range(256),4)
        past.append(dict(tick=t,directions=directions,feed_sites_draw_order=feeds))
        for m, source in originals.items():
            sites=(85,86,117,118) if m=='random-direction' else feeds
            source['rows'].append(dict(physical=dict(tick=t,directions=directions[:],mutation_tickets=[[999,0,1] for _ in range(256)],
                driven=dict(inputs=[dict(site=s,proposed=8 if s in sites else 0) for s in range(256)]))))
    states={k:json.loads(json.dumps(r.getstate())) for k,r in streams.items()}
    boundary=dict(seed=987654,past_ticks=32,states_after_tick32=states,
                  state_sha256={k:inputs.object_hash(v) for k,v in states.items()},tape_sha256=inputs.object_hash(past),
                  past_feed_sites_draw_order=[r['feed_sites_draw_order'] for r in past])
    return boundary, originals, streams


class EnvironmentTests(unittest.TestCase):
    def test_original_stream_after_32_and_full_32_future(self):
        boundary, originals, oracle=environment()
        restored=verifier.restore_environment(boundary,originals,inputs.runtime())
        for k,r in restored.items(): self.assertEqual(r.getstate(),oracle[k].getstate())
        future=verifier.draw_future(restored)
        self.assertIsInstance(future,tuple)
        for row,t in zip(future,range(33,65)):
            self.assertEqual(row['tick'],t)
            self.assertEqual(row['directions'],tuple(oracle['directions'].randrange(4) for _ in range(256)))
            self.assertEqual(row['feed_sites_draw_order'],tuple(oracle['feeds'].sample(range(256),4)))
        self.assertEqual(len(future),32)

    def test_reject_past_and_checkpoint_drift(self):
        for mutation in ('seed','runtime','directions','feed','mutation','state','order','count','type'):
            boundary, originals, _=environment(); runtime=inputs.runtime()
            if mutation=='seed': boundary['seed']+=1
            if mutation=='runtime': runtime['python_version']='wrong'
            if mutation=='directions': originals['random-both']['rows'][0]['physical']['directions'][0]^=1
            if mutation=='feed': originals['random-direction']['rows'][0]['physical']['driven']['inputs'][85]['proposed']=0
            if mutation=='mutation': originals['random-direction']['rows'][0]['physical']['mutation_tickets'][0][0]=998
            if mutation=='state': boundary['states_after_tick32']['feeds'][1][0]^=1
            if mutation=='order': boundary['past_feed_sites_draw_order'][0].reverse()
            if mutation=='count': boundary['past_ticks']=31
            if mutation=='type': originals['random-both']['exchange']=0
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):
                verifier.restore_environment(boundary,originals,runtime)

    def test_mask_empty_sites_only_and_preserve_tape(self):
        natural=tuple(s%4 for s in range(256))
        a=verifier.directions_for(natural,'continue_north');b=verifier.directions_for(natural,'withdraw_to_natural')
        self.assertEqual([s for s in range(256) if a[s]!=b[s]],[101,102])
        self.assertEqual(a[101:103],[3,3]);self.assertEqual(b,list(natural))
        with self.assertRaises(ValueError): verifier.directions_for([False]*256,'continue_north')

    def test_failed_draw_retains_partial_values_and_both_states(self):
        boundary,originals,_=environment(); streams=verifier.restore_environment(boundary,originals,inputs.runtime())
        class Broken:
            def __init__(self,r): self.r=r;self.calls=0
            def randrange(self,n):
                self.calls+=1
                if self.calls==260: raise KeyboardInterrupt('draw failed')
                return self.r.randrange(n)
            def getstate(self): return self.r.getstate()
        streams['directions']=Broken(streams['directions']);partial={};progress={}
        with self.assertRaises(KeyboardInterrupt): verifier.draw_future(streams,progress=progress,partial=partial)
        self.assertEqual(len(partial['natural_tape']),1)
        self.assertEqual(len(partial['pending_tick']['directions']),3)
        self.assertEqual(progress['future_direction_values'],259)
        self.assertEqual(set(partial['current_stream_states']),{'directions','feeds'})
        self.assertEqual(partial['status'],'failed')


class ScientificTests(unittest.TestCase):
    def test_history_no_second_removal_or_renumbering(self):
        original=fixture()['initial']; state=verifier.restore_state(original)
        self.assertIsNone(state['individuals'][0]['death_tick']); self.assertNotIn(0,state['site_ids'])
        state['raw'][0]=10;self.assertEqual(original['raw'][0],0)
        ids,people=deepcopy(original['site_ids']),deepcopy(original['individuals'])
        event=dict(tick=33,units=deepcopy(original['units']),material=dict(dissolved=[204],proposals=[dict(reason='formed',source=117,target=101,
            material=0,child_program=[0]*4,child_energy=4,mutated=False)]))
        event['units'][204]=None;event['units'][101]=dict(material=0,energy=4,program=[0]*4)
        births,deaths=verifier.advance_identities(ids,people,event)
        self.assertEqual((births[0]['id'],births[0]['parent'],deaths),(5,3,[2]))
        self.assertEqual(people[3]['offspring'],1);self.assertEqual(people[2]['death_tick'],33)
        self.assertIsNone(people[0]['death_tick'])

    def test_whole_component_program_ancestry_and_one_founder_allowed(self):
        f=fixture();s=f['initial']
        def observe(x): return verifier.observe(f['template'],x['units'],x['site_ids'],x['individuals'],10)
        result=observe(s);self.assertEqual(result['new_copy_count'],1)
        self.assertTrue(result['copies'][0]['member_witnesses'][0]['born_after_original_t0'])
        self.assertFalse(result['copies'][0]['member_witnesses'][0]['born_after_tick32'])
        one=deepcopy(s);one['individuals'][4].update(parent=0,founder=0)
        self.assertEqual(observe(one)['new_copy_count'],1)
        for kind in ('program','material','third_member','ancestry','original'):
            x=deepcopy(s)
            if kind=='program': x['units'][117]['program'][3]=1
            if kind=='material': x['units'][117]['material']=1
            if kind=='third_member':
                x['units'][116]=deepcopy(x['units'][117]);x['site_ids'][116]=2;x['units'][204]=None;x['site_ids'][204]=None
            if kind=='ancestry': x['individuals'][4]['founder']=2
            if kind=='original': x['site_ids'][117]=0
            with self.subTest(kind=kind): self.assertEqual(observe(x)['new_copy_count'],0)

    def test_future_intervals_cross_boundary_and_censoring(self):
        prefix=[dict(tick=t,copies=[{'all_new':True}]*2) for t in range(24,33)]
        r=verifier.temporal([2]+[0]*31,2,prefix,23)
        self.assertEqual(r['longest_double'],1);self.assertFalse(r['future_persistent10'])
        self.assertEqual(r['cross_boundary']['combined_observed_length'],10)
        self.assertTrue(r['cross_boundary']['combined_persistent10'])
        self.assertTrue(r['cross_boundary']['prefix_left_censored_at_original_intervention'])
        self.assertIsNone(verifier.temporal([2]+[0]*31,1,prefix,23)['cross_boundary'])
        self.assertIsNone(verifier.temporal([0]+[2]*31,2,prefix,23)['cross_boundary'])
        r=verifier.temporal([0]*22+[2]*10,0,[],10)
        self.assertEqual(r['intervals'],[dict(start=55,end=64,length=10,left_censored_at_boundary=False,right_censored=True)])
        self.assertTrue(r['future_persistent10'])
        self.assertFalse(verifier.temporal([2]*9+[0]*23,0,[],10)['future_persistent10'])
        with self.assertRaises(ValueError): verifier.temporal([2]*31,2,prefix,23)

    def test_two_birth_thresholds_preserve_original_support(self):
        people=fixture()['initial']['individuals']
        people += [dict(id=5,site=85,birth_tick=25,parent=3),dict(id=6,site=86,birth_tick=25,parent=4)]
        copies=[dict(all_new=True,members=[3,4],sites=[117,118]),dict(all_new=True,members=[5,6],sites=[85,86])]
        rows=[dict(tick=t,copies=deepcopy(copies)) for t in range(33,43)]
        r=verifier.support(rows,people,10,[3,4])
        self.assertEqual(r['metrics']['formation_persistent10'],1)
        self.assertEqual(r['metrics']['selected_ancestry_persistent10'],1)
        self.assertEqual(r['metrics']['after32_formation_supported'],0)
        self.assertEqual(r['upper_witnesses'][0]['selected_ancestry'][0]['chain'],[5,3])

    def test_complete_synthetic_pair_matches_other_route_and_known_accounts(self):
        from scripts import run_v4_middle_withdrawal as producer
        f=fixture();before=deepcopy(f);progress={}
        kernel=producer.step
        def counted(*args,**kwargs):
            r=kernel(*args,**kwargs);COUNTS['producer_physical_steps']+=1;return r
        with patch.object(producer,'step',side_effect=counted): expected=producer.run_pair(f,tape())
        actual=verifier.reconstruct_pair(f,tape(),progress=progress)
        inputs.same(actual,expected,'entire independent synthetic pair')
        self.assertEqual(f,before);self.assertEqual(progress['physical_steps'],64)
        for name in inputs.ARMS:
            arm=actual[name];self.assertEqual(arm['ledger']['initial_energy'],96)
            self.assertEqual(arm['ledger']['energy_export'],0)
            self.assertEqual(arm['ledger']['initial_living'],3)
            self.assertEqual(len(arm['rows']),32);self.assertEqual(arm['final']['tick'],64)
            self.assertEqual(arm['metrics']['final_energy'],96+arm['metrics']['imported']-arm['metrics']['spent'])
            self.assertTrue(all(r['physical']['material_after']==7 for r in arm['rows']))
            self.assertIsNone(arm['final']['individuals'][0]['death_tick'])
        for mutate in (lambda c:c['continue_north']['rows'][0]['physical'].__setitem__('tick',33.0),
                       lambda c:c['withdraw_to_natural']['ledger'].__setitem__('energy_export',False),
                       lambda c:c['continue_north']['rows'][0]['components'][0]['member_witnesses'][0].__setitem__('founder',False)):
            bad=deepcopy(expected);mutate(bad)
            with self.assertRaises(ValueError): verifier.compare_artifact(bad,actual,'case')

    def test_physical_observation_failure_preserves_completed_kernel(self):
        partial={};progress={};original=verifier.observe;calls=0
        def observe(*args):
            nonlocal calls
            calls+=1
            if calls==2: raise SystemExit('observer failure')
            return original(*args)
        with patch.object(verifier,'observe',side_effect=observe),self.assertRaises(SystemExit):
            verifier.reconstruct_pair(fixture(),tape(),progress=progress,partial=partial)
        self.assertEqual(progress['physical_steps'],1)
        arm=partial['continue_north'];self.assertEqual(len(arm['rows']),1)
        self.assertEqual(arm['rows'][0]['status'],'physical_complete')
        self.assertEqual(arm['last_observer_state']['tick'],33)


class EpochTests(unittest.TestCase):
    def test_source_drift_preserved_as_failure(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'source';source.write_text('before');root=Path(d)/'epoch'
            epoch=verifier.Epoch(root)
            def work():
                epoch.capture([str(source)]);epoch.write('records.json',[]);source.write_text('after')
            with self.assertRaises(ValueError): epoch.execute(work)
            meta=inputs.read(root/'metadata.json')
            self.assertEqual(meta['status'],'failed');self.assertNotEqual(meta['input_sha256'],meta['input_sha256_after'])
            self.assertIn('records.json',meta['output_sha256']);self.assertTrue((root/'failure.json').exists())
            with self.assertRaises(FileExistsError): verifier.Epoch(root)

    def test_first_baseexception_retained_and_independent_closers_attempted(self):
        for first in (ValueError('first'),KeyboardInterrupt('first'),SystemExit(19)):
            with self.subTest(first=type(first).__name__),tempfile.TemporaryDirectory() as d:
                e=verifier.Epoch(Path(d)/'epoch');calls=[]
                def work():
                    e.active_case={'partial':1};e.active_environment={'pending_tick':33};raise first
                def fail(): calls.append('fail');raise OSError('closing')
                def other(): calls.append('other')
                with self.assertRaises(type(first)) as caught: e.execute(work,(fail,other))
                self.assertIs(caught.exception,first);self.assertEqual(calls,['fail','other'])
                self.assertEqual(inputs.read(e.root/'metadata.json')['status'],'failed')
                self.assertTrue((e.root/'partial-case.json').exists());self.assertTrue((e.root/'partial-environment.json').exists())
                self.assertIn('closing:0',e.meta['finalization_errors'])

    def test_success_metadata_and_proof(self):
        with tempfile.TemporaryDirectory() as d:
            e=verifier.Epoch(Path(d)/'epoch');meta=e.execute(lambda:e.write('case.json',{'exact':True}))
            self.assertEqual(meta['status'],'verified');self.assertEqual(inputs.read(e.root/'proof.json')['status'],'verified')
            self.assertEqual(meta['output_sha256']['case.json'],inputs.digest(e.root/'case.json'))

    def test_finalize_write_failure_never_verified(self):
        with tempfile.TemporaryDirectory() as d:
            e=verifier.Epoch(Path(d)/'epoch');write=e.write
            def broken(name,value):
                if name=='proof.json': raise OSError('proof unavailable')
                return write(name,value)
            with patch.object(e,'write',side_effect=broken),self.assertRaises(OSError): e.execute(lambda:None)
            self.assertEqual(inputs.read(e.root/'metadata.json')['status'],'failed')
            self.assertEqual(inputs.read(e.root/'failure.json')['status'],'failed')

    @unittest.skipUnless(hasattr(signal,'setitimer'),'POSIX timer capability required')
    def test_blocking_work_deadline_and_failure_epoch(self):
        with tempfile.TemporaryDirectory() as d:
            e=verifier.Epoch(Path(d)/'epoch',seconds=.5,enforce_deadline=True);start=time.monotonic()
            with self.assertRaises(inputs.DeadlineExpired): e.execute(lambda:time.sleep(2))
            self.assertLess(time.monotonic()-start,1)
            self.assertEqual(inputs.read(e.root/'metadata.json')['status'],'failed')

    def test_unsupported_deadline_backend_rejected_before_work(self):
        with tempfile.TemporaryDirectory() as d,patch.object(verifier,'signal',object()):
            with self.assertRaisesRegex(RuntimeError,'POSIX'): verifier.Epoch(Path(d)/'epoch',enforce_deadline=True)


if __name__=='__main__': unittest.main()
