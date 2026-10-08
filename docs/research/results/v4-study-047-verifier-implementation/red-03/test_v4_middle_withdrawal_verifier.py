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

COUNTS = dict(dictionary_physical_steps=0, producer_physical_steps=0, synthetic_future_ticks=0, reference_future_ticks=0)


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
            COUNTS['reference_future_ticks'] += 1
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


class GuardFailureTests(unittest.TestCase):
    @unittest.skipUnless(hasattr(signal,'setitimer') and hasattr(__import__('os'),'fork'),'POSIX fork/timer required')
    def test_no_alarm_when_handler_installation_failed(self):
        g=verifier.Guard(time.monotonic(),1)
        with patch.object(signal,'setitimer') as arm,self.assertRaisesRegex(RuntimeError,'installed'):
            g.call(lambda:None)
        arm.assert_not_called()

    @unittest.skipUnless(hasattr(signal,'setitimer') and hasattr(__import__('os'),'fork'),'POSIX fork/timer required')
    def test_call_releases_lease_before_return_and_preserves_first_error(self):
        g=verifier.Guard(time.monotonic(),1);g.install()
        try:
            g.call(lambda:None)
            self.assertEqual(signal.getitimer(signal.ITIMER_REAL),(0.0,0.0))
            first=KeyboardInterrupt('scientific first')
            def fail():raise first
            with self.assertRaises(KeyboardInterrupt) as caught:g.call(fail)
            self.assertIs(caught.exception,first)
            self.assertEqual(signal.getitimer(signal.ITIMER_REAL),(0.0,0.0))
        finally:g.release()

    @unittest.skipUnless(hasattr(signal,'setitimer') and hasattr(__import__('os'),'fork'),'POSIX fork/timer required')
    def test_child_writer_exception_type_message_and_phase_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            e=verifier.Epoch(Path(d)/'epoch',seconds=1,enforce_deadline=True);write=e.write
            def broken(name,value):
                if name=='proof.json':raise OSError('distinct child write failure')
                return write(name,value)
            with patch.object(e,'write',side_effect=broken),self.assertRaisesRegex(OSError,'distinct child'):
                e.execute(lambda:None)
            meta=inputs.read(e.root/'metadata.json')
            self.assertEqual(meta['status'],'failed')
            self.assertIn('proof.json',meta['child_failure']['traceback'])

    @unittest.skipUnless(hasattr(signal,'setitimer') and hasattr(__import__('os'),'fork'),'POSIX fork/timer required')
    def test_parent_interrupt_cancels_child_before_failure_commit(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);g=verifier.Guard(time.monotonic(),1);real_wait=verifier.os.waitpid;calls=0
            first=KeyboardInterrupt('parent interruption')
            def interrupt(pid,flags):
                nonlocal calls
                calls+=1
                if calls==1:raise first
                return real_wait(pid,flags)
            def late():time.sleep(.03);(root/'late-verified').write_text('bad')
            with patch.object(verifier.os,'waitpid',side_effect=interrupt),self.assertRaises(KeyboardInterrupt) as caught:g.commit(late)
            self.assertIs(caught.exception,first)
            time.sleep(.06)
            self.assertFalse((root/'late-verified').exists())
            g.commit(lambda:(root/'failed').write_text('failed'))
            self.assertEqual((root/'failed').read_text(),'failed')

    @unittest.skipUnless(hasattr(signal,'setitimer') and hasattr(__import__('os'),'fork'),'POSIX fork/timer required')
    def test_blocking_commit_leaves_failed_within_total_deadline(self):
        with tempfile.TemporaryDirectory() as d:
            e=verifier.Epoch(Path(d)/'epoch',seconds=.5,enforce_deadline=True);write=e.write;start=time.monotonic()
            def blocked(name,value):
                if name=='proof.json':time.sleep(2)
                return write(name,value)
            with patch.object(e,'write',side_effect=blocked),self.assertRaises(inputs.DeadlineExpired):e.execute(lambda:None)
            self.assertLess(time.monotonic()-start,.8)
            self.assertEqual(inputs.read(e.root/'metadata.json')['status'],'failed')

    @unittest.skipUnless(hasattr(signal,'setitimer') and hasattr(__import__('os'),'fork'),'POSIX fork/timer required')
    def test_timer_release_failure_never_writes_verified(self):
        with tempfile.TemporaryDirectory() as d:
            e=verifier.Epoch(Path(d)/'epoch',seconds=1,enforce_deadline=True);release=e.guard.release;calls=[]
            def broken():
                calls.append(inputs.read(e.root/'metadata.json')['status'])
                release();raise OSError('release failure')
            with patch.object(e.guard,'release',side_effect=broken),self.assertRaisesRegex(OSError,'release failure'):e.execute(lambda:None)
            self.assertTrue(all(s=='closing' for s in calls));self.assertEqual(len(calls),2)
            self.assertEqual(inputs.read(e.root/'metadata.json')['status'],'failed')


def census_fixture():
    selected={('east',120005+i) for i in range(5)} | {('west',120000+i) for i in range(3)} | {('north',120000+i) for i in range(9)} | {('homogeneous',120003+i) for i in range(11)}
    cases=[];selected_number=0
    for encoding in inputs.ENCODINGS:
        for seed in inputs.SEEDS:
            triggered=(encoding,seed) in selected
            cases.append(dict(encoding=encoding,seed=seed,source='synthetic-index-only',trigger=triggered,
                              t0=10 if triggered else None,remaining=22 if triggered else None,
                              short_window=triggered and selected_number<10,applicability='synthetic',selection={'synthetic':True} if triggered else None))
            selected_number+=int(triggered)
    return {'cases':cases}


def fake_records(census):
    rows=[]
    for index,c in enumerate(c for c in census['cases'] if c['trigger']):
        row=dict(encoding=c['encoding'],seed=c['seed'],case=f"cases/{c['encoding']}-{c['seed']}.json",intervals={},cross_boundary={})
        for name,bit in zip(inputs.ARMS,((index//2)%2,index%2)):
            row[name+'_metrics']={m:bit if m in verifier.BINARY else index+(1 if name==inputs.ARMS[1] else 0) for m in verifier.METRICS}
        row['delta']={m:row['withdraw_to_natural_metrics'][m]-row['continue_north_metrics'][m] for m in verifier.METRICS}
        rows.append(row)
    return rows


class SummaryTests(unittest.TestCase):
    def test_full_grid_zero_cell_all_four_binary_cells_and_delta(self):
        census=census_fixture();records=fake_records(census)
        index=verifier.build_index(census,records,'formal');summary=verifier.summarize(records,index,'formal')
        self.assertEqual(len(index),100);self.assertEqual(sum(c['future'] is None for c in index),72)
        self.assertEqual([c['selected_n'] for c in summary['cells']],[5,3,0,9,11])
        self.assertEqual(len(summary['seed_groups']),14);self.assertEqual(summary['completed_physical_steps'],1792)
        self.assertEqual(summary['historical_short_windows'],10)
        south=summary['cells'][2];self.assertEqual(south['n'],0)
        self.assertTrue(all(v is None for v in south['mean_delta'].values()))
        self.assertTrue(all(v==0 for v in south['delta_totals'].values()))
        self.assertEqual(summary['overall']['delta_totals']['births'],28)
        self.assertEqual(summary['overall']['mean_delta']['births'],'1')
        self.assertEqual(summary['overall']['mean_delta']['persistent10'],'0')
        for metric in verifier.BINARY:
            self.assertEqual([c['n'] for c in summary['overall']['binary_pairs'][metric]],[7,7,7,7])
            self.assertEqual([summary['overall'][s][metric] for s in ('positive','negative','tie')],[7,7,14])
        self.assertEqual(summary['pairs'],records)
        from scripts import run_v4_middle_withdrawal as producer
        inputs.same(index,producer.make_index(census,records,'formal'),'complete synthetic index')
        inputs.same(summary,producer.summarize(records,index,'formal'),'complete synthetic summary')

    def test_engineering_retains_27_unrun_and_72_na(self):
        census=census_fixture();records=[r for r in fake_records(census) if (r['encoding'],r['seed'])==('east',120005)]
        index=verifier.build_index(census,records,'engineering');summary=verifier.summarize(records,index,'engineering')
        self.assertEqual(sum(c['future_status']=='not_run_engineering' for c in index),27)
        self.assertEqual(sum(c['future_status']=='not_applicable_original_32_no_trigger' for c in index),72)
        self.assertEqual(summary['completed_pairs'],1);self.assertEqual(summary['selected_pairs'],28)
        self.assertEqual(sum(s['n'] for s in summary['seed_groups']),1)
        with self.assertRaises(ValueError):verifier.build_index(census,records,'formal')
        with self.assertRaises(ValueError):verifier.build_index(census,records*2,'engineering')

    def test_summary_rejects_wrong_sign_types_denominator_and_fourgrid(self):
        census=census_fixture();records=fake_records(census)
        for mutation in ('sign','bool','binary','denominator'):
            values=deepcopy(records);c=deepcopy(census)
            if mutation=='sign':values[0]['delta']['births']=-1
            if mutation=='bool':values[0]['continue_north_metrics']['births']=False
            if mutation=='binary':values[0]['withdraw_to_natural_metrics']['persistent10']=2;values[0]['delta']['persistent10']=2
            if mutation=='denominator':c['cases'][0]['short_window']=True
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):
                verifier.summarize(values,verifier.build_index(c,values,'formal'),'formal')


class MoreScienceTests(unittest.TestCase):
    def test_every_proposal_gate_including_masked_failures(self):
        units=[None]*256
        for s in range(6):units[s]=dict(material=0,energy=32 if s!=5 else 2,program=[0,1,2,3])
        for s in (30,50):units[s]=dict(material=0,energy=5,program=[0]*4)
        raw=[0]*256;raw[20]=1
        proposals=[dict(source=s,target=t,reason=r,direction=3) for s,t,r in
                   ((0,10,'formed'),(1,20,'collision'),(2,20,'collision'),(3,30,'occupied'),(4,40,'raw_material'),(5,50,'energy'))]
        physical=dict(interaction_units=units,raw=raw,mutation_tickets=[[999,0,1] for _ in range(256)],material={'proposals':proposals})
        gates=verifier.gates_for(physical)
        self.assertEqual({g['reason'] for g in gates},set(verifier.REASONS))
        self.assertEqual(gates[0]['candidate_count'],1);self.assertTrue(gates[0]['raw_available'])
        self.assertEqual([g['candidate_count'] for g in gates[1:3]],[2,2]);self.assertFalse(gates[1]['no_collision'])
        self.assertEqual([gates[-1][k] for k in ('energy_sufficient','target_empty','raw_available','no_collision')],[False]*4)
        self.assertEqual(gates[0]['expressed_material'],3);self.assertEqual(gates[0]['mutation_ticket'],[999,0,1])

    def test_prefix_passive_history_and_components_reconstructed_without_physics(self):
        f=fixture();state=f['initial'];f['prefix_initial'].update(deepcopy(state));f['prefix_initial']['tick']=10
        f['prefix_rows']=[]
        for t in range(11,33):
            physical=dict(tick=t,units=deepcopy(state['units']),material=dict(dissolved=[],proposals=[]))
            f['prefix_rows'].append(dict(tick=t,physical=physical,site_ids=state['site_ids'][:],births=[],deaths=[],
                observation=verifier.partition(state['units'],state['site_ids'],16,16,'final'),
                copies=[dict(members=[3,4],sites=[117,118],all_new=True)]))
        with patch.object(verifier,'physical_step',side_effect=AssertionError('prefix physics forbidden')):
            prefix=verifier.reconstruct_prefix(f)
            self.assertEqual([r['tick'] for r in prefix],list(range(11,33)))
            self.assertEqual(prefix[-1]['copies'],[dict(members=[3,4],sites=[117,118],all_new=True)])
            for kind in ('id','copy','history'):
                bad=deepcopy(f)
                if kind=='id':bad['prefix_rows'][0]['site_ids'][117]=0
                if kind=='copy':bad['prefix_rows'][-1]['copies'][0]['all_new']=False
                if kind=='history':bad['initial']['individuals'][0]['offspring']=3
                with self.subTest(kind=kind),self.assertRaises(ValueError):verifier.reconstruct_prefix(bad)


def producer_metadata_fixture(root,mode='engineering'):
    chosen=[c for c in census_fixture()['cases'] if c['trigger'] and (mode=='formal' or (c['encoding'],c['seed'])==('east',120005))]
    hashes={}
    for name in verifier.expected_artifacts(chosen):
        p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('{}\n');hashes[name]=inputs.digest(p)
    bindings={'source.py':'sourcehash','producer-review.json':'approved-producer','verifier-review.json':'approved-verifier'}
    if mode=='formal':bindings['engineering-review.json']='approved-engineering'
    meta=dict(schema=inputs.SCHEMA,route='producer',status='complete',mode=mode,git_commit='synthetic-commit',
              planned_pairs=len(chosen),completed_pairs=len(chosen),planned_physical_steps=64*len(chosen),physical_steps=64*len(chosen),
              full_case_expected_steps=64,fixed_future_ticks=[33,64],synthetic_fixture_steps=0,
              future_generator_ticks=len({c['seed'] for c in chosen})*32,reconstructed_past_generator_ticks=640,work_done=True,
              runtime=inputs.runtime(),input_sha256=bindings,input_sha256_after=dict(bindings),
              input_read_errors_before={},input_read_errors_after={},output_read_errors={},finalization_errors={},
              elapsed_seconds=1.0,output_sha256=hashes)
    (root/'metadata.json').write_text(inputs.canonical(meta))
    return chosen,bindings,meta


class InputInterfaceTests(unittest.TestCase):
    def test_producer_inventory_includes_each_stage_review_gate(self):
        for mode in ('engineering','formal'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as d:
                root=Path(d);chosen,bindings,meta=producer_metadata_fixture(root,mode)
                self.assertEqual(verifier.validate_producer(root,mode,chosen,bindings,'synthetic-commit'),meta)
                with self.assertRaises(ValueError):verifier.validate_producer(root,mode,chosen,{'source.py':'sourcehash'},'synthetic-commit')

    def test_metadata_types_stage_hashes_and_extra_outputs_rejected(self):
        for kind in ('status','mode','commit','physical','bool','ticks','runtime','error','hash','extra','missing','time'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as d:
                root=Path(d);chosen,bindings,meta=producer_metadata_fixture(root)
                if kind=='status':meta['status']='failed'
                if kind=='mode':meta['mode']='formal'
                if kind=='commit':meta['git_commit']='other'
                if kind=='physical':meta['physical_steps']=64.0
                if kind=='bool':meta['work_done']=1
                if kind=='ticks':meta['future_generator_ticks']=64
                if kind=='runtime':meta['runtime']['python_version']='wrong'
                if kind=='error':meta['finalization_errors']={'write':'failed'}
                if kind=='hash':meta['output_sha256']['summary.json']='0'*64
                if kind=='extra':(root/'unexpected.json').write_text('{}')
                if kind=='missing':(root/'records.json').unlink()
                if kind=='time':meta['elapsed_seconds']=601.0
                (root/'metadata.json').write_text(inputs.canonical(meta))
                with self.assertRaises(ValueError):verifier.validate_producer(root,'engineering',chosen,bindings,'synthetic-commit')

    def test_real_entry_rejects_gate_before_future_or_producer_reads(self):
        error=ValueError('synthetic denied gate')
        with patch.object(verifier,'Guard'),patch.object(verifier,'check_no_other_process'),patch.object(inputs,'execution_gates',side_effect=error),\
             patch.object(verifier,'draw_future') as draw,patch.object(verifier,'physical_step') as physics,patch.object(verifier,'validate_producer') as read:
            with self.assertRaises(ValueError) as caught:verifier.run('engineering','nonexistent-producer','nonexistent-output')
            self.assertIs(caught.exception,error);draw.assert_not_called();physics.assert_not_called();read.assert_not_called()

    def test_process_gate_detects_script_module_and_flags(self):
        for command in ('python -X dev -W error scripts/verify_v4_middle_withdrawal.py --mode engineering',
                        'python3.14 -I -mscripts.run_v4_middle_withdrawal',
                        'python -- scripts/run_v4_middle_withdrawal.py',
                        'python --check-hash-based-pycs always -m scripts.verify_v4_middle_withdrawal'):
            with self.subTest(command=command),patch.object(verifier.subprocess,'check_output',return_value='999999 '+command),self.assertRaises(ValueError):
                verifier.check_no_other_process()
        with patch.object(verifier.subprocess,'check_output',return_value='999999 python -c "print(\'verify_v4_middle_withdrawal.py\')"'):
            verifier.check_no_other_process()


class AdditionalFailureTests(unittest.TestCase):
    def test_environment_tickets_are_deeply_immutable(self):
        boundary,originals,_=environment();streams=verifier.restore_environment(boundary,originals,inputs.runtime())
        tickets=verifier.draw_future(streams)
        with self.assertRaises(TypeError):tickets[0]['tick']=34
        with self.assertRaises(TypeError):tickets[0]['directions'][0]=3

    def test_rng_state_capture_failure_preserves_first_and_other_state(self):
        boundary,originals,_=environment();streams=verifier.restore_environment(boundary,originals,inputs.runtime())
        first=SystemExit('first budget stop');partial={}
        def stop():raise first
        with patch.object(streams['feeds'],'getstate',side_effect=OSError('feed checkpoint')),self.assertRaises(SystemExit) as caught:
            verifier.draw_future(streams,budget=stop,partial=partial)
        self.assertIs(caught.exception,first)
        self.assertEqual(partial['status'],'failed');self.assertIn('directions',partial['current_stream_states'])
        self.assertIn('feeds',partial['state_capture_errors'])

    def test_input_read_errors_both_phases_preserve_first(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'source';source.write_text('source');e=verifier.Epoch(root/'epoch')
            first=KeyboardInterrupt('first read failure');digest=inputs.digest;calls=0
            def broken(path):
                nonlocal calls
                if str(path)==str(source):
                    calls+=1
                    if calls==1:raise first
                    raise OSError('after read failure')
                return digest(path)
            with patch.object(inputs,'digest',side_effect=broken),self.assertRaises(KeyboardInterrupt) as caught:
                e.execute(lambda:e.capture([str(source)]))
            self.assertIs(caught.exception,first)
            self.assertIn(str(source),e.meta['input_read_errors_before']);self.assertIn(str(source),e.meta['input_read_errors_after'])
            self.assertEqual(inputs.read(e.root/'metadata.json')['status'],'failed')

    def test_output_hash_read_failure_preserves_completed_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            e=verifier.Epoch(Path(d)/'epoch');digest=inputs.digest
            def broken(path):
                if Path(path).name=='records.json':raise OSError('output read failed')
                return digest(path)
            with patch.object(inputs,'digest',side_effect=broken),self.assertRaisesRegex(OSError,'output read failed'):
                e.execute(lambda:e.write('records.json',[{'complete':True}]))
            self.assertEqual(inputs.read(e.root/'records.json'),[{'complete':True}])
            self.assertIn(str(e.root/'records.json'),e.meta['output_read_errors'])
            self.assertEqual(inputs.read(e.root/'metadata.json')['status'],'failed')

    def test_initial_metadata_io_failure_is_saved_and_science_not_started(self):
        with tempfile.TemporaryDirectory() as d:
            e=verifier.Epoch(Path(d)/'epoch');write=e.write;calls=0;first=OSError('initial metadata')
            def broken(name,value):
                nonlocal calls
                if name=='metadata.json':
                    calls+=1
                    if calls==1:raise first
                return write(name,value)
            with patch.object(e,'write',side_effect=broken),patch.object(verifier,'reconstruct_pair') as science,self.assertRaises(OSError) as caught:
                e.execute(science)
            self.assertIs(caught.exception,first);science.assert_not_called()
            self.assertEqual(inputs.read(e.root/'metadata.json')['status'],'failed')

    def test_storage_failure_retains_error_without_dropping_scientific_fields(self):
        with tempfile.TemporaryDirectory() as d:
            e=verifier.Epoch(Path(d)/'epoch',storage=65536)
            def work():e.active_case={'full_science':'x'*100000};e.budget()
            with self.assertRaisesRegex(ValueError,'storage'):e.execute(work)
            self.assertEqual(e.active_case['full_science'],'x'*100000)
            self.assertEqual(inputs.read(e.root/'metadata.json')['status'],'failed')
            self.assertIn('partial_case',e.meta['finalization_errors'])

    @unittest.skipUnless(hasattr(signal,'setitimer') and hasattr(__import__('os'),'fork'),'POSIX fork/timer required')
    def test_hash_timeout_and_later_closer_attempted_with_original_exception(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'source';source.write_text('before')
            e=verifier.Epoch(root/'epoch',seconds=.7,enforce_deadline=True);digest=inputs.digest;calls=0;first=SystemExit('original scientific failure')
            def broken(path):
                nonlocal calls
                if str(path)==str(source):
                    calls+=1
                    if calls>1:time.sleep(2)
                return digest(path)
            def work():e.capture([str(source)]);e.write('records.json',[]);raise first
            with patch.object(inputs,'digest',side_effect=broken),self.assertRaises(SystemExit) as caught:e.execute(work)
            self.assertIs(caught.exception,first)
            self.assertIn(str(source),e.meta['input_read_errors_after']);self.assertIn('records.json',e.meta['output_sha256'])
            self.assertEqual(inputs.read(e.root/'metadata.json')['status'],'failed')

    @unittest.skipUnless(hasattr(signal,'setitimer') and hasattr(__import__('os'),'fork'),'POSIX fork/timer required')
    def test_partial_child_write_and_abnormal_child_exit_are_failed(self):
        for mode in ('partial','exit'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as d:
                e=verifier.Epoch(Path(d)/'epoch',seconds=1,enforce_deadline=True);write=e.write
                def broken(name,value):
                    if name=='proof.json':
                        (e.root/name).write_text('{truncated')
                        if mode=='exit':verifier.os._exit(23)
                        raise KeyboardInterrupt('child interrupted write')
                    return write(name,value)
                expected=KeyboardInterrupt if mode=='partial' else RuntimeError
                with patch.object(e,'write',side_effect=broken),self.assertRaises(expected):e.execute(lambda:None)
                self.assertEqual(inputs.read(e.root/'metadata.json')['status'],'failed')
                self.assertEqual((e.root/'proof.json').read_text(),'{truncated')

    @unittest.skipUnless(hasattr(signal,'setitimer') and hasattr(__import__('os'),'fork'),'POSIX fork/timer required')
    def test_install_failure_uses_no_parent_alarm_and_saves_failed_epoch(self):
        with tempfile.TemporaryDirectory() as d:
            e=verifier.Epoch(Path(d)/'epoch',seconds=1,enforce_deadline=True);first=RuntimeError('handler install failed')
            with patch.object(e.guard,'install',side_effect=first),patch.object(e.guard,'call',wraps=e.guard.call),self.assertRaises(RuntimeError) as caught:
                e.execute(lambda:self.fail('science must not run'))
            self.assertIs(caught.exception,first)
            self.assertEqual(inputs.read(e.root/'metadata.json')['status'],'failed')
