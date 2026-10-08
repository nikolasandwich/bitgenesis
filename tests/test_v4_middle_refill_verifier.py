"""Independent synthetic saved-phase and evidence faults; never run a physics step."""
from copy import deepcopy
import ast
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import middle_refill_inputs as inputs
from scripts import verify_v4_middle_refill as verify


def cell(energy):
    return dict(energy=energy, material=0, program=[0, 1, 2, 3])


def proposal(source, target, direction, reason):
    return dict(source=source, target=target, direction=direction, reason=reason)


class SavedCase:
    """Author the three saved phases directly, without producer or kernel helpers."""
    def __init__(self, folder, actors=None, raw=None, births=(), proposals=()):
        self.folder = Path(folder)
        ids, before, interaction, tickets = [None]*256, [None]*256, [None]*256, [0]*256
        people = []
        for site, (energy, direction) in sorted((actors or {}).items()):
            ids[site] = len(people)
            before[site], interaction[site], tickets[site] = cell(max(1, energy)), cell(energy), direction
            people.append(dict(id=ids[site], site=site, parent=None, birth_tick=0, material=0))
        raws = [0]*256
        for site, amount in (raw or {}).items():
            raws[site] = amount
        final_ids, final_cells, final_raw = ids[:], deepcopy(interaction), raws[:]
        deaths = [s for s in range(256) if interaction[s] is not None and interaction[s]['energy'] == 0]
        for site in deaths:
            final_ids[site] = final_cells[site] = None
            final_raw[site] += 1
        born = []
        for site, parent_site in births:
            item = dict(id=len(people), parent=ids[parent_site], site=site, birth_tick=32,
                        material=0, birth_energy=7)
            people.append(item)
            born.append(deepcopy(item))
            final_ids[site], final_cells[site] = item['id'], cell(7)
            final_raw[site] -= 1
        arm = dict(initial=dict(tick=31, site_ids=ids, units=before, raw=raws),
                   rows=[dict(tick=32, site_ids=final_ids, births=born, deaths=[ids[s] for s in deaths],
                              physical=dict(tick=32, units=final_cells, raw=final_raw,
                                            interaction_units=interaction, directions=tickets,
                                            material=dict(dissolved=deaths, proposals=list(proposals))))],
                   final=dict(individuals=people))
        self.branch = dict(selection=dict(seed=120005, t0=31, remaining_steps=1, category='short_window',
                                         offspring_ids=[], offspring_sites=[]),
                           control=arm, ablation=deepcopy(arm))
        self.gaps, self.reuse, self.plans = [], [], []
        self.refresh()

    def save(self, name, value):
        path = self.folder / name
        path.write_bytes(inputs.encode(value))
        return str(path)

    def refresh(self):
        branch_path = self.save('branch.json', self.branch)
        t0 = self.branch['selection']['t0']
        turns = {a: dict(diagnostic=dict(tick=t0), rows=[dict(tick=row['tick'],
                 middle=[dict(site=site, identity=row['site_ids'][site]) for site in (101, 102)],
                 B101=False, B102=False, G=True, actual_double_new=False) for row in self.branch[a]['rows']])
                 for a in ('control', 'ablation')}
        turns_path = self.save('turnover.json', turns)
        self.plans = []
        for arm in ('control', 'ablation'):
            n = len(self.branch[arm]['rows'])
            self.plans.append(dict(key=['east', 120005, arm], encoding='east', seed=120005, arm=arm, t0=t0,
                saved_states=n, diagnostic_states=1, short_window=True, category='short_window',
                target_ticks=n*2, source_slots=n*8, source=inputs.make_ref(branch_path, '/'+arm),
                diagnostic=inputs.make_ref(branch_path, '/'+arm+'/initial'),
                turnover_diagnostic=inputs.make_ref(turns_path, '/'+arm+'/diagnostic'),
                proposal_plan='needed_projection', reuse_041=None, gap_keys=[], gap_target_ticks=0, gap_source_slots=0,
                rows=[dict(tick=row['tick'], target_ticks=2, source_slots=8,
                      source=inputs.make_ref(branch_path, f'/{arm}/rows/{i}'),
                      before=inputs.make_ref(branch_path, f'/{arm}/rows/{i-1}' if i else f'/{arm}/initial'),
                      turnover=inputs.make_ref(turns_path, f'/{arm}/rows/{i}'), reuse_041=None)
                      for i, row in enumerate(self.branch[arm]['rows'])]))

    def gap(self, site=101, predecessor=None, successor=None, arm='control'):
        original = dict(site=site, predecessor=predecessor, successor=successor,
                        start_boundary=31 if predecessor is None else 32, end_boundary=32,
                        distance_ticks=1 if predecessor is None else 0,
                        empty_ticks=[32] if successor is None else [], empty_saved_states=int(successor is None),
                        left_censored=predecessor is None, right_censored=successor is None,
                        same_tick_replacement=predecessor is not None and successor is not None,
                        material_changed=False if predecessor is not None and successor is not None else None)
        path = self.save(f'gap-{len(self.gaps)}.json', original)
        ref = inputs.make_ref(path, '')
        key = ['east', 120005, arm, ref['json_pointer']]
        entry = dict(key=key, encoding='east', seed=120005, arm=arm, reference=ref, original=original,
                     decision_ticks=[32], decision_target_ticks=1, decision_source_slots=4,
                     intervals_recalculated=False)
        self.gaps.append(entry)
        plan = next(p for p in self.plans if p['arm'] == arm)
        plan['gap_keys'].append(key)
        plan['gap_target_ticks'] += 1
        plan['gap_source_slots'] += 4
        return entry

    def reconstruct(self):
        return verify.reconstruct_pair('east', self.branch, self.plans, self.gaps, self.reuse)

    def attach_reuse(self, events):
        self.reuse = [dict(encoding='east', selection=deepcopy(self.branch['selection']),
                           rows=[dict(tick=32, events=deepcopy(events), deaths=[])])]
        path = self.save('041.json', self.reuse)
        old = self.save('039.json', dict(selection=deepcopy(self.branch['selection']),
                                       ablation=deepcopy(self.branch['control'])))
        self.plans[0]['proposal_plan'] = 'reuse_041'
        self.plans[0]['reuse_041'] = dict(reference=inputs.make_ref(path, '/0'),
                old_branch=inputs.make_ref(old, '/ablation'), complete_old_arm_equal=True,
                proposals_reclassified=False, historical_verifier_mode='parent inline fallback independent algorithm')
        self.plans[0]['rows'][0]['reuse_041'] = inputs.make_ref(path, '/0/rows/0')


def slots(pair, arm='control'):
    return {(s['source'], s['target']): s for s in pair['arms'][arm]['rows'][0]['slots']}


def index_for(case=None):
    return [dict(encoding=e, seed=seed, trigger=case is not None and (e, seed)==('east', 120005),
                 t0=31 if case is not None and (e, seed)==('east', 120005) else None,
                 remaining=1 if case is not None and (e, seed)==('east', 120005) else 0,
                 short_window=case is not None and (e, seed)==('east', 120005),
                 source='saved-source', branch=str(case.folder/'branch.json') if case is not None and
                 (e, seed)==('east', 120005) else None,
                 applicability='observed' if case is not None and (e, seed)==('east', 120005) else 'not_applicable')
            for e in ('east', 'west', 'south', 'north', 'homogeneous') for seed in range(120000,120020)]


class PhaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def case(self, **kwargs):
        return SavedCase(self.tmp.name, **kwargs)

    def test_empty_and_dead_tickets_have_no_proposal_newborn_does_not_act(self):
        f = self.case(actors={100:(20,0), 102:(0,1)}, raw={101:1}, births=[(101,100)],
                      proposals=[proposal(100,101,0,'formed')])
        r=f.reconstruct(); s=slots(r)
        self.assertEqual(len(s),8)
        self.assertEqual((s[101,102]['state'],s[101,102]['end_identity']),('empty_source',2))
        self.assertEqual((s[102,101]['state'],s[102,101]['ticket_target']),('dissolved',101))
        for key in ((101,102),(102,101)):
            self.assertIsNone(s[key]['proposal_target']); self.assertIsNone(s[key]['proposal'])
        self.assertEqual(s[100,101]['proposal']['child_id'],2)
        self.assertNotEqual(s[100,101]['key'], slots(r,'ablation')[100,101]['key'])
        self.assertEqual(r['arms']['control']['diagnostic'].keys(), {'source','turnover'})

    def test_target_uses_dissolution_release_and_gap_includes_same_tick_birth(self):
        f=self.case(actors={101:(0,0),117:(20,3)}, births=[(101,117)],
                    proposals=[proposal(117,101,3,'formed')]); original=deepcopy(f.gap(predecessor=0,successor=2))
        r=f.reconstruct(); t=r['arms']['control']['rows'][0]['targets'][0]; g=r['arms']['control']['gaps'][0]
        self.assertEqual(t['before'],dict(identity=0,material=0,raw=0))
        self.assertEqual(t['preformation'],dict(identity=None,material=None,raw=1))
        self.assertEqual(t['after'],dict(identity=2,material=0,raw=0))
        self.assertEqual(g['original'], original['original']); self.assertEqual(g['original']['empty_saved_states'],0)
        self.assertEqual(g['sequence'][0]['birth_id'],2); self.assertEqual(g['counts']['births'],1)
        self.assertEqual(g['counts']['source_slots'],4)
        self.assertIsNone(r['arms']['control']['rows'][0]['targets'][1]['gap_key'])

    def test_independent_candidate_index_preserves_energy_priority(self):
        f=self.case(actors={85:(20,2),100:(3,0),117:(20,3)}, raw={101:1},
                    proposals=[proposal(85,101,2,'collision'),proposal(100,101,0,'energy'),proposal(117,101,3,'collision')])
        r=f.reconstruct(); p=slots(r)[100,101]['proposal']; t=r['arms']['control']['rows'][0]['targets'][0]
        self.assertEqual((p['reason'],p['candidate_count'],p['candidate']),('energy',2,False))
        self.assertTrue(p['raw_ok'] and p['target_empty']); self.assertEqual(len(t['candidate_keys']),2)
        self.assertEqual(len(t['proposal_keys']),3)

    def test_not_pointing_has_actual_destination_but_no_failed_proposal(self):
        f=self.case(actors={100:(3,1)}, proposals=[proposal(100,99,1,'energy')]); s=slots(f.reconstruct())[100,101]
        self.assertEqual((s['state'],s['proposal_target']),('not_pointing',99));self.assertIsNone(s['proposal'])

    def test_occupied_raw_and_energy_are_independent(self):
        f=self.case(actors={100:(20,0),101:(1,0)}, proposals=[proposal(100,101,0,'occupied'),proposal(101,102,0,'energy')])
        p=slots(f.reconstruct())[100,101]['proposal']
        self.assertEqual(p['reason'],'occupied');self.assertFalse(p['raw_ok']);self.assertFalse(p['target_empty'])
        self.assertTrue(p['energy_ok'])

    def test_saved_reason_and_destination_faults_rejected(self):
        for field, value in [('reason','formed'),('target',102),('direction',1)]:
            with self.subTest(field=field):
                f=self.case(actors={100:(20,0)},proposals=[proposal(100,101,0,'raw_material')])
                f.branch['control']['rows'][0]['physical']['material']['proposals'][0][field]=value; f.refresh()
                with self.assertRaises(ValueError):f.reconstruct()

    def test_birth_identity_parent_site_and_raw_corruption_rejected(self):
        for field,value in [('id',99),('parent',99),('site',102)]:
            with self.subTest(field=field):
                f=self.case(actors={100:(20,0)},raw={101:1},births=[(101,100)],proposals=[proposal(100,101,0,'formed')])
                f.branch['control']['rows'][0]['births'][0][field]=value; f.refresh()
                with self.assertRaisesRegex(ValueError,'birth'):f.reconstruct()
        f=self.case(actors={100:(20,0)},raw={101:1},births=[(101,100)],proposals=[proposal(100,101,0,'formed')])
        f.branch['control']['rows'][0]['physical']['raw'][101]=1; f.refresh()
        with self.assertRaisesRegex(ValueError,'raw'):f.reconstruct()

    def test_nonacting_events_and_bad_interaction_identity_rejected(self):
        for actors in ({},{100:(0,0)}):
            f=self.case(actors=actors,proposals=[proposal(100,101,0,'energy')])
            with self.assertRaises(ValueError):f.reconstruct()
        f=self.case(); f.branch['control']['rows'][0]['physical']['interaction_units'][100]=cell(5); f.refresh()
        with self.assertRaisesRegex(ValueError,'interaction'):f.reconstruct()

    def test_pointer_and_source_hash_are_bound(self):
        f=self.case(); f.plans[0]['rows'][0]['source']['json_pointer']='/ablation/rows/0'
        with self.assertRaises(ValueError):f.reconstruct()
        f=self.case(); (f.folder/'branch.json').write_text('{}')
        with self.assertRaises(ValueError):f.reconstruct()

    def test_reuse_exact_values_and_historical_author_are_retained(self):
        f=self.case(actors={100:(3,0)},proposals=[proposal(100,101,0,'energy')]); e=deepcopy(slots(f.reconstruct())[100,101]['proposal'])
        e['old_proof_annotation']='immutable'; f.attach_reuse([e]); r=f.reconstruct(); s=slots(r)[100,101]
        self.assertEqual(s['proposal'],e);self.assertEqual(s['source_mode'],'reuse_041')
        self.assertEqual(s['proposal_reference']['json_pointer'],'/0/rows/0/events/0')
        self.assertIn('parent inline fallback',r['arms']['control']['reuse_041']['historical_verifier_mode'])
        self.assertEqual(slots(r)[103,102]['source_mode'],'source_projection')

    def test_reuse_wrong_selection_arm_row_pointer_and_old_branch_rejected(self):
        for fault in ('selection','arm','row','old_branch'):
            with self.subTest(fault=fault):
                f=self.case(); f.attach_reuse([])
                if fault=='selection': f.reuse[0]['selection']['seed']=120006
                if fault=='arm': f.plans[1]['reuse_041']=deepcopy(f.plans[0]['reuse_041']); f.plans[1]['proposal_plan']='reuse_041'
                if fault=='row': f.plans[0]['rows'][0]['reuse_041']['json_pointer']='/0'
                if fault=='old_branch': f.plans[0]['reuse_041']['old_branch']['json_pointer']='/selection'
                with self.assertRaises(ValueError):f.reconstruct()

    def test_gap_window_overlap_and_original_corruption_rejected(self):
        f=self.case(); g=f.gap(); g['decision_ticks']=[]
        with self.assertRaises(ValueError):f.reconstruct()
        f=self.case(); g=f.gap();g['original']['right_censored']=False
        with self.assertRaises(ValueError):f.reconstruct()
        f=self.case();f.gap();f.gaps.append(deepcopy(f.gaps[0]))
        with self.assertRaises(ValueError):f.reconstruct()

    def test_summary_full_zero_grid_and_numeric_deltas(self):
        s=verify.independent_summary([],index_for())
        self.assertEqual((s['index_cases'],s['no_trigger'],len(s['cells'])),(100,100,20))
        self.assertTrue(all(c['policy_denominator']==20 and c['source_slots']==0 for c in s['cells']))
        f=self.case(); r=f.reconstruct(); s=verify.independent_summary([r],index_for(f));d=s['paired'][0]['delta']
        self.assertEqual(d['source_slots'],0); self.assertEqual(d['cross_counts']['other']['outside']['states']['formed'],0)
        self.assertEqual(s['overall']['control']['source_slots'],8)

    def test_index_missing_duplicate_or_wrong_selection_is_rejected(self):
        f=self.case(); r=f.reconstruct(); idx=index_for(f)
        for bad in (idx[:-1],idx[:-1]+[idx[0]],deepcopy(idx)):
            if bad==idx:bad[5]['remaining']=2
            with self.assertRaises(ValueError):verify.independent_summary([r],bad)

    def test_previous_physical_raw_and_success_endpoint_are_preserved(self):
        f = self.case(actors={100:(20,0)}, raw={101:1}, births=[(101,100)],
                      proposals=[proposal(100,101,0,'formed')])
        f.branch['selection'].update(t0=30, remaining_steps=2)
        for arm in ('control', 'ablation'):
            saved = f.branch[arm]
            saved['initial']['tick'] = 30
            first = saved['rows'][0]
            first['tick'] = first['physical']['tick'] = first['births'][0]['birth_tick'] = 31
            saved['final']['individuals'][-1]['birth_tick'] = 31
            second = deepcopy(first)
            second.update(tick=32, births=[], deaths=[])
            second['physical'].update(tick=32, interaction_units=deepcopy(first['physical']['units']),
                material=dict(dissolved=[], proposals=[proposal(100,101,0,'occupied'), proposal(101,102,0,'energy')]))
            saved['rows'].append(second)
        f.refresh()
        original = dict(site=101, predecessor=None, successor=1, start_boundary=30, end_boundary=31,
                        distance_ticks=1, empty_ticks=[], empty_saved_states=0, left_censored=True,
                        right_censored=False, same_tick_replacement=False, material_changed=None)
        path = f.save('endpoint.json', original)
        gap = dict(key=['east',120005,'control',''], encoding='east', seed=120005, arm='control',
                   reference=inputs.make_ref(path,''), original=original, decision_ticks=[31],
                   decision_target_ticks=1, decision_source_slots=4, intervals_recalculated=False)
        f.gaps = [gap]
        f.plans[0].update(gap_keys=[gap['key']], gap_target_ticks=1, gap_source_slots=4)
        pair = f.reconstruct()
        rows = pair['arms']['control']['rows']
        self.assertEqual(rows[1]['targets'][0]['before']['raw'], 0)
        self.assertEqual(rows[1]['targets'][0]['preformation']['raw'], 0)
        self.assertFalse(rows[1]['slots'][0]['proposal']['raw_ok'])
        self.assertEqual(pair['arms']['control']['gaps'][0]['sequence'][0]['birth_id'], 1)
        self.assertIsNone(rows[1]['targets'][0]['gap_key'])

    def test_all_28_synthetic_paired_deltas_keep_every_zero_leaf(self):
        f = self.case()
        template = f.reconstruct()
        index = index_for()
        records = []
        for entry in index[:28]:
            entry.update(trigger=True, t0=31, remaining=1, short_window=True,
                         branch='synthetic', applicability='observed')
            record = deepcopy(template)
            record['encoding'] = entry['encoding']
            record['selection']['seed'] = entry['seed']
            records.append(record)
        summary = verify.independent_summary(records,index)
        self.assertEqual((len(summary['cells']), len(summary['paired']), summary['no_trigger']), (20,28,72))
        def check_leaves(value):
            if isinstance(value,dict):
                for child in value.values():
                    check_leaves(child)
            else:
                self.assertIs(type(value),int)
                self.assertEqual(value,0)
        for pair in summary['paired']:
            check_leaves(pair['delta'])

    def test_scientific_imports_are_independent(self):
        tree=ast.parse(Path(verify.__file__).read_text())
        names=[n.module or '' for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
        names += [alias.name for n in ast.walk(tree) if isinstance(n,ast.Import) for alias in n.names]
        self.assertFalse(any('analyze_v4' in n or 'bitgenesis' in n for n in names))


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name); self.case=SavedCase(self.root)
        self.producer=self.root/'producer'; self.producer.mkdir()
        self.index=index_for(self.case); self.records=[self.case.reconstruct()]
        self.census=dict(index=self.index, index_reference=None, arms=self.case.plans,gaps=[],counts={})
        self.census_path=self.case.save('census.json',self.census)
        # Real readable inputs with exact required cardinality; bind independently of scientific code.
        self.paths=[str(p) for p in self.root.iterdir() if p.is_file()]
        self.paths += list(inputs.NEW)
        for i in range(954-len(self.paths)):
            path=self.root/f'input-{i}.json';path.write_text('{}');self.paths.append(str(path))
        self.hashes=inputs.capture(self.paths)[0]
        self.write_producer()
        self.addCleanup(patch.stopall)
        patch.object(verify.inputs,'bindings',return_value=self.hashes).start()
        patch.object(verify.inputs,'input_paths',return_value=self.paths).start()
        patch.object(verify.inputs,'CENSUS',self.census_path).start()
        # Only the root index reference is synthetic; phase references remain real and hash checked.
        self.census['index_reference']=inputs.make_ref(self.producer/'index.json','')
        Path(self.census_path).write_bytes(inputs.encode(self.census))
        self.hashes.update(inputs.capture(self.paths)[0]);self.write_producer()

    def write_producer(self):
        values={'index.json':self.index,'records.json':self.records,'pair-01.json':self.records[0],
                'summary.json':verify.independent_summary(self.records,self.index)}
        for name,value in values.items():(self.producer/name).write_bytes(inputs.encode(value))
        self.metadata=dict(status='complete',phase='engineering',route='producer',planned_cases=1,planned_arms=2,
                completed_cases=1,completed_arms=2,saved_steps=2,diagnostic_states=2,target_ticks=4,source_slots=16,
                new_simulation_steps=0,new_environment_sources=0,new_independent_initial_worlds=0,
                outputs_exclusive=True,includes_verifier=True,source_epoch='producer and verifier',
                input_paths=sorted(self.hashes),input_inventory_errors={},input_sha256=dict(self.hashes),
                input_sha256_after=dict(self.hashes),input_read_errors_before={},input_read_errors_after={},
                time_limit_seconds=600,storage_limit_bytes=128*1024*1024,elapsed_seconds=0.1,
                output_bytes_before_metadata=sum((self.producer/n).stat().st_size for n in values),
                output_sha256={n:inputs.digest(self.producer/n) for n in values},git_commit='fixture')
        self.save_metadata()

    def save_metadata(self):
        (self.producer/'metadata.json').write_bytes(inputs.encode(self.metadata))

    def run_verify(self, name='verify', **kwargs):
        return verify.run(self.producer,self.root/name,engineering=True,**kwargs)

    def read_proof(self,name='verify'):
        return inputs.read(self.root/name/'independent-verification.json')

    def test_success_binds_all_sources_outputs_and_rejects_existing_output(self):
        result=self.run_verify();p=self.read_proof()
        self.assertEqual(result['status'],'complete');self.assertEqual(p['status'],'complete')
        self.assertTrue(p['execution_complete'] and p['closing_complete'])
        self.assertEqual(len(p['input_sha256']),954);self.assertEqual(p['input_sha256'],p['input_sha256_after'])
        self.assertEqual(p['producer_sha256'],p['producer_sha256_after']);self.assertEqual(p['source_slots'],16)
        self.assertEqual(p['new_simulation_steps'],0)
        with self.assertRaises(FileExistsError):self.run_verify()
        self.assertEqual(self.read_proof(),p)

    def test_historical_953_subset_allowed_only_when_explicit_engineering(self):
        old=dict(self.hashes);del old[inputs.NEW[-1]]
        self.metadata.update(input_paths=sorted(old),input_sha256=old,input_sha256_after=dict(old),
                             includes_verifier=False,source_epoch='producer-only engineering');self.save_metadata()
        self.run_verify();p=self.read_proof()
        self.assertEqual(p['producer_source_count'],953);self.assertEqual(len(p['input_sha256']),954)
        self.metadata['input_sha256'][inputs.NEW[0]]='f'*64;self.metadata['input_sha256_after']=dict(self.metadata['input_sha256']);self.save_metadata()
        with self.assertRaises(ValueError):self.run_verify('bad')
        self.assertEqual(self.read_proof('bad')['status'],'failed')

    def test_missing_or_forged_source_binding_rejected_and_failure_preserved(self):
        for fault in ('count','after','reads','physical','status','outputset','epoch','timebudget','storagebudget'):
            with self.subTest(fault=fault):
                self.write_producer()
                if fault=='count':self.metadata['input_sha256'].pop(next(iter(self.hashes)))
                if fault=='after':self.metadata['input_sha256_after'][inputs.NEW[0]]='0'*64
                if fault=='reads':self.metadata['input_read_errors_before']={'broken':'bad'}
                if fault=='physical':self.metadata['new_simulation_steps']=1
                if fault=='status':self.metadata['status']='failed'
                if fault=='outputset':self.metadata['output_sha256'].pop('index.json')
                if fault=='epoch':self.metadata['source_epoch']='forged'
                if fault=='timebudget':self.metadata['time_limit_seconds']=0.01
                if fault=='storagebudget':self.metadata['storage_limit_bytes']=1
                self.save_metadata()
                with self.assertRaises(ValueError):self.run_verify(fault)
                p=self.read_proof(fault);self.assertEqual(p['status'],'failed');self.assertTrue(p['error'])
                self.assertEqual(p['producer_sha256'],p['producer_sha256_after'])

    def test_corrupt_record_target_gap_and_summary_even_with_updated_hash_rejected(self):
        for fault in ('target','slot','gap','summary','pair','index'):
            with self.subTest(fault=fault):
                self.write_producer()
                name='records.json';value=deepcopy(self.records)
                if fault=='target':value[0]['arms']['control']['rows'][0]['targets'][0]['preformation']['raw']=10
                if fault=='slot':value[0]['arms']['control']['rows'][0]['slots'][0]['proposal_target']=101
                if fault=='gap':value[0]['arms']['control']['gaps']=[{'fake':True}]
                if fault=='summary':name='summary.json';value=inputs.read(self.producer/name);value['cells'].pop()
                if fault=='pair':name='pair-01.json';value={}
                if fault=='index':name='index.json';value=self.index[:-1]
                (self.producer/name).write_bytes(inputs.encode(value));self.metadata['output_sha256'][name]=inputs.digest(self.producer/name)
                self.metadata['output_bytes_before_metadata']=sum((self.producer/n).stat().st_size for n in self.metadata['output_sha256']);self.save_metadata()
                with self.assertRaises(ValueError):self.run_verify(fault)
                self.assertEqual(self.read_proof(fault)['status'],'failed')

    def test_invalid_json_missing_file_and_changed_output_preserve_both_epochs(self):
        (self.producer/'records.json').write_text('{')
        with self.assertRaises(ValueError):self.run_verify('json')
        self.assertEqual(len(self.read_proof('json')['producer_sha256']),5)
        self.write_producer();(self.producer/'records.json').unlink()
        with self.assertRaises(ValueError):self.run_verify('missing')
        self.assertIn(str((self.producer/'records.json').resolve()),self.read_proof('missing')['producer_read_errors_before'])
        self.write_producer();original=verify.reconstruct_pair
        def changed(*a,**kw):
            r=original(*a,**kw);(self.producer/'records.json').write_text('[]');return r
        with patch.object(verify,'reconstruct_pair',side_effect=changed),self.assertRaises(ValueError):self.run_verify('changed')
        p=self.read_proof('changed');self.assertNotEqual(p['producer_sha256'],p['producer_sha256_after'])

    def test_budgets_and_closing_hash_errors_are_failures(self):
        for name,limits in [('time',dict(seconds=0)),('storage',dict(byte_limit=10))]:
            with self.subTest(name=name),self.assertRaises((ValueError,TimeoutError)):self.run_verify(name,**limits)
            self.assertEqual(self.read_proof(name)['status'],'failed')
            self.assertGreaterEqual(self.read_proof(name)['elapsed_seconds'],0)
        original=verify.reconstruct_pair
        def remove(*a,**kw):
            r=original(*a,**kw);Path(self.paths[0]).unlink();return r
        with patch.object(verify,'reconstruct_pair',side_effect=remove),self.assertRaises(ValueError):self.run_verify('cleanup')
        self.assertTrue(self.read_proof('cleanup')['input_read_errors_after'])

    def test_corrupt_metadata_json_retains_hashes_and_summary_fault_reports_progress(self):
        (self.producer/'metadata.json').write_text('{')
        with self.assertRaises(ValueError):
            self.run_verify('metadata')
        proof = self.read_proof('metadata')
        self.assertEqual(len(proof['input_sha256']),954)
        self.assertEqual(proof['producer_sha256'],proof['producer_sha256_after'])
        self.write_producer()
        summary = inputs.read(self.producer/'summary.json')
        summary['paired'][0]['delta']['states']['formed'] = 1
        (self.producer/'summary.json').write_bytes(inputs.encode(summary))
        self.metadata['output_sha256']['summary.json'] = inputs.digest(self.producer/'summary.json')
        self.metadata['output_bytes_before_metadata'] = sum((self.producer/n).stat().st_size for n in self.metadata['output_sha256'])
        self.save_metadata()
        with self.assertRaisesRegex(ValueError,'summary'):
            self.run_verify('progress')
        proof = self.read_proof('progress')
        self.assertEqual((proof['completed_cases'],proof['completed_arms'],proof['source_slots']), (1,2,16))
        self.assertTrue((self.root/'progress'/'pair-01.json').exists())

    def test_changed_own_output_and_failed_closing_capture_cannot_claim_success(self):
        original = verify.independent_summary
        def change_own(*args, **kwargs):
            result = original(*args, **kwargs)
            (self.root/'own'/'pair-01.json').write_text('{}')
            return result
        with patch.object(verify,'independent_summary',side_effect=change_own):
            with self.assertRaisesRegex(ValueError,'output before/after'):
                self.run_verify('own')
        self.assertEqual(self.read_proof('own')['status'],'failed')
        original_capture = inputs.capture
        call_count = 0
        def fail_close(paths):
            nonlocal call_count
            call_count += 1
            if call_count == 3:
                raise OSError('closing device failure')
            return original_capture(paths)
        with patch.object(inputs,'capture',side_effect=fail_close):
            with self.assertRaisesRegex(OSError,'closing device failure'):
                self.run_verify('capture')
        proof = self.read_proof('capture')
        self.assertIn('capture',proof['input_read_errors_after'])
        self.assertEqual(proof['producer_sha256'],proof['producer_sha256_after'])

    def test_main_keyboard_interrupt_and_system_exit_leave_failed_proof(self):
        for number, error in enumerate((KeyboardInterrupt('cancel reconstruction'), SystemExit(7))):
            with self.subTest(error=type(error).__name__):
                name = f'main-interrupt-{number}'
                with patch.object(verify, 'reconstruct_pair', side_effect=error):
                    with self.assertRaises(type(error)) as caught:
                        self.run_verify(name)
                self.assertIs(caught.exception, error)
                proof = self.read_proof(name)
                self.assertEqual(proof['status'], 'failed')
                self.assertEqual(proof['error'], repr(error))
                self.assertEqual(proof['completed_cases'], 0)
                self.assertEqual(proof['source_slots'], 0)
                self.assertFalse(proof['execution_complete'])
                self.assertEqual(proof['input_sha256'], proof['input_sha256_after'])
                self.assertEqual(proof['producer_sha256'], proof['producer_sha256_after'])
                self.assertEqual(proof['output_sha256'], proof['output_sha256_after'])

    def test_each_closing_capture_interrupt_still_attempts_all_three_inventories(self):
        original_capture = inputs.capture
        for stage, call in (('input', 3), ('producer', 4), ('output', 5)):
            for kind in (KeyboardInterrupt, SystemExit):
                with self.subTest(stage=stage, error=kind.__name__):
                    name = f'{stage}-{kind.__name__}'
                    error = kind('closing cancellation')
                    calls = []
                    def interrupt(paths):
                        calls.append(list(paths))
                        if len(calls) == call:
                            raise error
                        return original_capture(paths)
                    with patch.object(inputs, 'capture', side_effect=interrupt):
                        with self.assertRaises(kind) as caught:
                            self.run_verify(name)
                    self.assertIs(caught.exception, error)
                    proof = self.read_proof(name)
                    self.assertEqual(proof['status'], 'failed')
                    self.assertEqual(proof['error'], repr(error))
                    self.assertEqual(len(calls), 5)
                    self.assertTrue(proof['execution_complete'])
                    self.assertFalse(proof['closing_complete'])
                    self.assertTrue(proof[f'{stage}_read_errors_after'])
                    for other in {'input', 'producer', 'output'} - {stage}:
                        self.assertEqual(proof[f'{other}_sha256'], proof[f'{other}_sha256_after'])

    def test_primary_interrupt_survives_multiple_closing_interrupts(self):
        original_capture = inputs.capture
        primary = KeyboardInterrupt('primary cancellation')
        calls = []
        def interrupt(paths):
            calls.append(list(paths))
            if len(calls) in (3, 4):
                raise SystemExit('secondary closing cancellation')
            return original_capture(paths)
        with patch.object(verify, 'reconstruct_pair', side_effect=primary):
            with patch.object(inputs, 'capture', side_effect=interrupt):
                with self.assertRaises(KeyboardInterrupt) as caught:
                    self.run_verify('primary')
        self.assertIs(caught.exception, primary)
        proof = self.read_proof('primary')
        self.assertEqual(proof['status'], 'failed')
        self.assertEqual(proof['error'], repr(primary))
        self.assertEqual(len(calls), 5)
        self.assertTrue(proof['input_read_errors_after'])
        self.assertTrue(proof['producer_read_errors_after'])
        self.assertEqual(proof['output_sha256'], proof['output_sha256_after'])

    def test_equal_value_wrong_types_in_all_producer_contracts_fail(self):
        mutations = (
            ('records.json', (0,'arms','control','rows',0,'slots',0,'direction'), False),
            ('records.json', (0,'arms','control','rows',0,'targets',0,'before','raw'), 0.0),
            ('pair-01.json', ('arms','control','saved_steps'), 1.0),
            ('index.json', (5,'remaining'), True),
            ('summary.json', ('overall','control','states','formed'), False),
            ('summary.json', ('overall','control','source_slots'), 8.0),
            ('summary.json', ('paired',0,'delta','states','formed'), False),
            ('summary.json', ('cells',0,'policy_denominator'), 20.0),
            ('metadata.json', ('completed_cases',), True),
            ('metadata.json', ('source_slots',), 16.0),
            ('metadata.json', ('new_simulation_steps',), False),
        )
        for number, (filename, trail, wrong_type) in enumerate(mutations):
            with self.subTest(filename=filename, trail=trail):
                self.write_producer()
                value = inputs.read(self.producer/filename)
                target = value
                for key in trail[:-1]:
                    target = target[key]
                self.assertEqual(target[trail[-1]], wrong_type)
                self.assertIsNot(type(target[trail[-1]]), type(wrong_type))
                target[trail[-1]] = wrong_type
                (self.producer/filename).write_bytes(inputs.encode(value))
                if filename != 'metadata.json':
                    self.metadata['output_sha256'][filename] = inputs.digest(self.producer/filename)
                    self.metadata['output_bytes_before_metadata'] = sum(
                        (self.producer/n).stat().st_size for n in self.metadata['output_sha256'])
                    self.save_metadata()
                name = f'wrong-type-{number}'
                # Isolate full producer index comparison from the synthetic fixture's
                # reference to that same index file (real census references 045).
                with patch.object(verify.inputs.SourceReader, 'resolve', autospec=True,
                                  side_effect=self.reference_resolver_for_index()):
                    with self.assertRaises(ValueError):
                        self.run_verify(name)
                proof = self.read_proof(name)
                self.assertEqual(proof['status'], 'failed')
                self.assertTrue(proof['error'])
                self.assertEqual(proof['input_sha256'], proof['input_sha256_after'])
                self.assertEqual(proof['producer_sha256'], proof['producer_sha256_after'])

    def reference_resolver_for_index(self):
        original = inputs.SourceReader.resolve
        def resolve(reader, reference):
            if reference == self.census['index_reference']:
                return deepcopy(self.index)
            return original(reader, reference)
        return resolve

    def test_engineering_rejects_formal_output_and_wrong_case_before_projection(self):
        with patch.object(verify,'reconstruct_pair') as project:
            with self.assertRaises(ValueError):verify.run(self.producer,Path('data/v4-study-046'),engineering=True)
            project.assert_not_called()
        self.census['index'][5]['seed']=120006
        Path(self.census_path).write_bytes(inputs.encode(self.census))
        with patch.object(verify,'reconstruct_pair') as project:
            with self.assertRaises(ValueError):self.run_verify('wrong')
            project.assert_not_called()


if __name__=='__main__':
    unittest.main()
