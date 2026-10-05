import hashlib
import json
import sys
import tempfile
import types
import unittest
from copy import deepcopy
from fractions import Fraction as F
from pathlib import Path
from unittest.mock import patch
from scripts import analyze_v4_energy_absorption as run


def fixture():
    states = [dict(energy=e, hit='1/2', dead='1/2', mean_steps='2') for e in range(1,16)]
    curve = []
    for t in range(33):
        s = F(1,2**t)
        alive = ['0']*15
        alive[4] = str(s)
        curve.append(dict(horizon=t, alive=alive, surviving=str(s), hit=str((1-s)/2), dead=str((1-s)/2)))
    return states, dict(curve=curve, cohort=[])


class AbsorptionTest(unittest.TestCase):
    def test_small_exact_system_and_row_exchange(self):
        matrix = [[0,2],[3,1]]; rhs = [[1,4],[2,5]]
        original = deepcopy((matrix,rhs))
        self.assertEqual(run.gauss_jordan(matrix,rhs), [[F(1,2),F(1)],[F(1,2),F(2)]])
        self.assertEqual((matrix,rhs),original)
        with self.assertRaisesRegex(ValueError,'singular'):
            run.gauss_jordan([[1,2],[2,4]],[[1],[2]])

    def test_solver_assembles_fixed_bellman_system_without_solving_it(self):
        class Stop(Exception): pass
        def inspect(matrix,rhs):
            self.assertEqual(len(matrix),15)
            self.assertEqual(matrix[0],[64,0,0,0,0,0,0,-1,0,0,0,0,0,0,0])
            self.assertEqual(matrix[-1][-2:],[-63,64])
            self.assertEqual(rhs,[[int(e>=9),64] for e in range(1,16)])
            raise Stop()
        with patch.object(run,'gauss_jordan',side_effect=inspect),self.assertRaises(Stop):
            run.solve_states()

    def test_solver_rejects_bad_synthetic_solution_without_formal_solve(self):
        for values in ([[F(2),F(1)]]*15, [[F(0),F(1)]]*15, [[F(0),F(0)]]*15):
            with patch.object(run,'gauss_jordan',return_value=values),self.assertRaises(ValueError):
                run.solve_states()

    def test_unreadable_input_retains_readable_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory)/'run'; present=Path(directory)/'present';missing=Path(directory)/'missing'
            present.write_text('fixture')
            def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
            helper=types.SimpleNamespace(input_paths=lambda errors:[str(present),str(missing)],
                bindings=lambda:(_ for _ in ()).throw(ValueError('bad binding')),digest=digest,
                read=lambda p:None,save=lambda p,v:p.write_text(json.dumps(v)))
            def git(command,**kwargs):return '' if command[1]=='status' else 'a'*40
            with patch.object(run,'OUTPUT',out),patch.object(run.subprocess,'check_output',git),patch.dict(sys.modules,{'scripts.energy_absorption_inputs':helper}):
                with self.assertRaisesRegex(ValueError,'bad binding'):run.main()
            meta=json.loads((out/'metadata.json').read_text())
            self.assertEqual(meta['input_sha256'],{str(present):digest(present)})
            self.assertEqual(meta['input_sha256_after'],meta['input_sha256'])
            self.assertIn(str(missing),meta['input_read_errors_before'])
            self.assertIn(str(missing),meta['input_read_errors'])

    def test_33_reconstructions_and_summary(self):
        states, prior = fixture()
        with patch.object(run,'solve_states',return_value=states):
            records, summary = run.build(prior)
        self.assertEqual(len(records['finite_checks']),33)
        for row in records['finite_checks']:
            self.assertEqual(row['hit_reconstructed'],'1/2')
            self.assertEqual(row['mean_steps_reconstructed'],'2')
        self.assertEqual(summary,dict(initial_energy=5,eventual_hit='1/2',eventual_dead='1/2',mean_absorption_steps='2',
            at_32_hit=str((1-F(1,2**32))/2),additional_hit_after_32=str(F(1,2**33)),
            remaining_mean_steps_after_32=str(F(1,2**31)),at_32_surviving=str(F(1,2**32))))

    def test_reject_broken_finite_bridge(self):
        for kind in ('missing','order','hit','surviving','negative','noncanonical','alive'):
            states,prior=fixture()
            if kind=='missing':prior['curve'].pop()
            if kind=='order':prior['curve'][1]['horizon']=2
            if kind=='hit':prior['curve'][2]['hit']='1/3'
            if kind=='surviving':prior['curve'][2]['surviving']='1'
            if kind=='negative':prior['curve'][2]['alive'][0]='-1'
            if kind=='noncanonical':prior['curve'][0]['hit']='0/1'
            if kind=='alive':prior['curve'][0]['alive'].pop()
            with self.subTest(kind=kind),patch.object(run,'solve_states',return_value=states),self.assertRaises(ValueError):run.build(prior)

    def test_main_evidence_exclusivity_failure_and_final_budget(self):
        for mode in ('ok','binding','changed','time','storage'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as directory:
                out=Path(directory)/'run'; present=Path(directory)/'input';present.write_text('fixture')
                inventory=[str(present)]+['fixture-'+str(i) for i in range(514)]
                def digest(p):
                    return hashlib.sha256(Path(p).read_bytes()).hexdigest() if Path(p).exists() else 'b'*64
                before={p:digest(p) for p in inventory}; calls=0;expired=False
                def bindings():
                    nonlocal calls
                    calls+=1
                    if mode=='binding':raise ValueError('bad binding')
                    if mode=='changed' and calls>1:return dict(before,changed='c'*64)
                    return before
                def save(p,v):
                    nonlocal expired
                    p.write_text(json.dumps(v))
                    if p.name=='metadata.json' and v['status']=='complete':
                        if mode=='time':expired=True
                        if mode=='storage':(out/'oversize').write_bytes(b'x'*8388608)
                states,prior=fixture()
                helper=types.SimpleNamespace(input_paths=lambda errors:inventory,bindings=bindings,digest=digest,read=lambda p:prior,save=save)
                def git(command,**kwargs):return '' if command[1]=='status' else 'a'*40
                with patch.object(run,'OUTPUT',out),patch.object(run.subprocess,'check_output',git),patch.object(run.time,'monotonic',side_effect=lambda:61 if expired else 0),patch.object(run,'solve_states',return_value=states),patch.dict(sys.modules,{'scripts.energy_absorption_inputs':helper}):
                    if mode=='ok':run.main()
                    else:
                        with self.assertRaises(ValueError):run.main()
                    with self.assertRaises(FileExistsError):run.main()
                meta=json.loads((out/'metadata.json').read_text())
                self.assertEqual(meta['status'],'complete' if mode=='ok' else 'failed')
                self.assertEqual(meta['planned_states'],15)
                self.assertEqual(meta['completed_states'],0 if mode=='binding' else 15)
                self.assertEqual(meta['input_paths'],inventory)
                self.assertEqual(meta['input_sha256'],before)
                self.assertEqual(meta['finite_horizons'],33)
                self.assertEqual(meta['new_full_world_steps'],0)
                self.assertIn('records.json',meta['output_sha256'])
