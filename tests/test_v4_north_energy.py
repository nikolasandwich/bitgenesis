import json
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
from scripts import run_v4_north_energy as probe


def initial(collision=False):
    units = [None]*256
    units[32] = dict(material=0, energy=7, program=[0, 0, 0, 2])
    if collision:
        units[17] = dict(material=0, energy=20, program=[1]*4)
    raw = [0]*256; raw[16] = 1
    directions = [0]*256; directions[32] = 3; directions[17] = 1
    return dict(units=units, raw=raw, directions=directions, mutation_tickets=[[0, 1, 2] for _ in units])


class EnergyProbeTest(unittest.TestCase):
    def test_selection_fixed_order_and_negative_eligibility(self):
        records = json.loads(Path('docs/research/results/v4-study-026-records.json').read_text())
        chosen = probe.select(records)
        self.assertEqual(len(chosen), 52)
        self.assertEqual(set(chosen[0]), set(probe.SELECTION_KEYS))
        self.assertEqual([sum(s['genotype']==g and s['exchange']==e for s in chosen) for g in ('homogeneous','heterogeneous') for e in (False,True)], [21,5,21,5])
        self.assertTrue(all(s['mode']=='random-both' and 0<s['energy_before']<16 for s in chosen))
        for change in ('missing', 'reverse', 'bool', 'energy'):
            bad = deepcopy(records)
            if change == 'missing': bad.pop()
            if change == 'reverse': bad.reverse()
            if change == 'bool': bad[0]['seed'] = True
            if change == 'energy':
                s = chosen[0]
                r = next(r for r in bad if all(r[k]==s[k] for k in ('genotype','mode','exchange','seed')))
                next(a for a in r['steps'][s['tick']-1] if a['site']==s['site'])['energy_interaction'] = 16
            with self.subTest(change=change), self.assertRaises(ValueError): probe.select(bad)

    def test_phase_energy_mass_expression_and_immutability(self):
        state = initial(); original = deepcopy(state)
        control = probe.phase(state)
        self.assertEqual(control['material']['proposals'][0]['reason'], 'energy')
        state['units'][32]['energy'] = 16
        treated = probe.phase(state)
        self.assertEqual(treated['units'][16], dict(material=2, energy=5, program=[0,0,0,2]))
        self.assertEqual(treated['material']['spent'], 5)
        self.assertEqual(treated['material']['energy_after'], 11)
        self.assertEqual(treated['material']['material_before'], treated['material']['material_after'])
        state['units'][32]['energy'] = 7
        self.assertEqual(state, original)

    def test_collision_preserves_other_proposal_side_effect(self):
        state = initial(True)
        control = probe.phase(state)
        state['units'][32]['energy'] = 16
        treated = probe.phase(state)
        self.assertEqual([p['reason'] for p in control['material']['proposals']], ['formed', 'energy'])
        self.assertEqual([p['reason'] for p in treated['material']['proposals']], ['collision', 'collision'])
        self.assertEqual(treated['material']['energy_after']-control['material']['energy_after'], 14)

    def test_probe_saved_control_and_tamper(self):
        records = json.loads(Path('docs/research/results/v4-study-026-records.json').read_text())
        s = probe.select(records)[0]
        path = Path(f"data/v4-study-019/cases/seed-{s['seed']}-{s['mode']}-exchange-{str(s['exchange']).lower()}.json")
        import tarfile
        with tarfile.open('docs/research/results/v4-study-019-cases.tar.gz') as archive:
            case = json.load(archive.extractfile('cases/'+path.name))
        old = deepcopy(case)
        result = probe.run_probe(case, s)
        self.assertEqual(result['added_energy'], 16-s['energy_before'])
        self.assertEqual(result['control'], {k:case['rows'][s['tick']-1]['physical'][k] for k in ('units','raw','material')})
        self.assertEqual(result['initial']['raw'], case['rows'][s['tick']-2]['physical']['raw'] if s['tick']>1 else case['initial']['raw'])
        self.assertEqual(case, old)
        for key in ('identity','root','energy_before','site','seed'):
            bad = dict(s); bad[key] += 1
            with self.subTest(key=key), self.assertRaises(ValueError): probe.run_probe(case,bad)
        bad = deepcopy(case); bad['rows'][s['tick']-1]['physical']['units'][s['site']]['energy'] += 1
        with self.assertRaises(ValueError): probe.run_probe(bad,s)

    def test_phase_rejects_bad_tickets(self):
        bad = initial(); bad['mutation_tickets'][0] = [1000,0,1]
        with self.assertRaises(ValueError): probe.phase(bad)

    def test_summary_retains_negative_and_other_source_changes(self):
        state = initial(True); control = probe.phase(state)
        augmented = deepcopy(state); augmented['units'][32]['energy'] = 16
        treated = probe.phase(augmented)
        records = []
        for g in ('homogeneous','heterogeneous'):
            for e in (False,True):
                for i in range(5 if e else 21):
                    records.append(dict(genotype=g,mode='random-both',seed=120000+min(i,19),exchange=e,
                        tick=1+int(i==20),site=32,identity=0,root=0,energy_before=7,added_energy=9,
                        initial=deepcopy(state),control=deepcopy(control),treated=deepcopy(treated)))
        summary = probe.summarize(records)
        self.assertEqual([(c['genotype'],c['exchange'],c['probes']) for c in summary],
            [('homogeneous',False,21),('homogeneous',True,5),('heterogeneous',False,21),('heterogeneous',True,5)])
        for c in summary:
            n = c['probes']
            self.assertEqual((c['control_formed'],c['treated_formed'],c['nonzero_treated']), (0,0,0))
            self.assertEqual(c['treated_reasons'], dict(energy=0,occupied=0,raw_material=0,collision=n,formed=0))
            self.assertEqual((c['total_formed_delta'],c['spent_delta'],c['energy_after_delta'],c['other_reason_changes']), (-n,-5*n,14*n,n))
        for change in ('missing','reverse','duplicate','energy','mass'):
            bad = deepcopy(records)
            if change=='missing': bad.pop()
            if change=='reverse': bad.reverse()
            if change=='duplicate': bad[-1]=bad[-2]
            if change=='energy': bad[0]['treated']['units'][32]['energy'] += 1
            if change=='mass': bad[0]['treated']['raw'][0] += 1
            with self.subTest(change=change), self.assertRaises(ValueError): probe.summarize(bad)

    def test_initial_failure_preserves_hash_inventory(self):
        import tempfile, types, sys, hashlib
        def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); out=root/'run'; present=root/'present'; missing=root/'missing'
            present.write_text('unchanged')
            helper=types.SimpleNamespace(input_paths=lambda errors:[str(present),str(missing)],
                bindings=lambda:(_ for _ in ()).throw(ValueError('bad binding')),digest=digest,
                source_cases=lambda:iter([]),read=lambda p:json.loads(p.read_text()),save=lambda p,v:p.write_text(json.dumps(v)))
            def git(command,**kwargs): return '' if command[1]=='status' else 'a'*40
            with patch.object(probe,'OUTPUT',out),patch.object(probe.subprocess,'check_output',git),patch.dict(sys.modules,{'scripts.north_energy_inputs':helper}):
                with self.assertRaisesRegex(ValueError,'bad binding'): probe.main()
                with self.assertRaises(FileExistsError): probe.main()
            meta=json.loads((out/'metadata.json').read_text())
            self.assertEqual(meta['status'],'failed')
            self.assertEqual(meta['input_paths'],[str(present),str(missing)])
            self.assertEqual(meta['input_sha256'],{str(present):digest(present)})
            self.assertEqual(meta['input_sha256_after'],meta['input_sha256'])
            self.assertIn(str(missing),meta['input_read_errors_before'])
            self.assertIn(str(missing),meta['input_read_errors'])
            self.assertEqual(meta['output_sha256'],{'records.json':digest(out/'records.json')})
            self.assertEqual((meta['new_full_world_steps'],meta['new_phase_transitions']), (0,0))

    def test_final_write_budget(self):
        import tempfile,types,sys,hashlib
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory)/'run'; expired=False
            def save(path,value):
                nonlocal expired
                path.write_text(json.dumps(value))
                if path.name=='metadata.json' and value['status']=='complete': expired=True
            helper=types.SimpleNamespace(input_paths=lambda errors:[],bindings=lambda:{},
                digest=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest(),source_cases=lambda:iter([]),read=lambda p:[],save=save)
            def git(command,**kwargs): return '' if command[1]=='status' else 'a'*40
            with patch.object(probe,'OUTPUT',out),patch.object(probe.subprocess,'check_output',git),patch.object(probe.time,'monotonic',side_effect=lambda:301 if expired else 0),patch.object(probe,'select',return_value=[]),patch.object(probe,'summarize',return_value=[]),patch.object(probe.opportunities,'GRID',[]),patch.dict(sys.modules,{'scripts.north_energy_inputs':helper}):
                with self.assertRaisesRegex(ValueError,'bounded execution'): probe.main()
            self.assertEqual(json.loads((out/'metadata.json').read_text())['status'],'failed')

    def test_failed_probe_preserves_completed_phase_count(self):
        import tempfile, types, sys, hashlib
        case = dict(mode='random-both',exchange=False,seed=120000)
        chosen = dict(genotype='homogeneous',**case)
        def fail_after_control(case, selected):
            probe.phase(initial())
            raise ValueError('after one phase')
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)/'run'
            helper = types.SimpleNamespace(input_paths=lambda errors:[],bindings=lambda:{},
                digest=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest(),
                source_cases=lambda:iter([('homogeneous',Path('fixture'))]),read=lambda p:case,
                save=lambda p,v:p.write_text(json.dumps(v)))
            def git(command,**kwargs): return '' if command[1]=='status' else 'a'*40
            with patch.object(probe,'OUTPUT',out),patch.object(probe.subprocess,'check_output',git),patch.object(probe,'select',return_value=[chosen]),patch.object(probe,'run_probe',side_effect=fail_after_control),patch.object(probe.opportunities,'GRID',[('homogeneous','random-both',False,120000)]),patch.dict(sys.modules,{'scripts.north_energy_inputs':helper}):
                with self.assertRaisesRegex(ValueError,'after one phase'): probe.main()
            meta = json.loads((out/'metadata.json').read_text())
            self.assertEqual((meta['status'],meta['completed_probes'],meta['new_phase_transitions']), ('failed',0,1))
